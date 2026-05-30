"""
VoiceScript Web API — FastAPI backend untuk React UI.

Jembatan HTTP antara React frontend dan src/ tools yang sudah ada.
MCP server (mcp_server.py) tetap berjalan terpisah dan tidak terpengaruh.

Jalankan: uvicorn web_api:app --reload --port 8000
"""
import os
import uuid
import time
import asyncio
import shutil
import logging
from contextlib import asynccontextmanager
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, UploadFile, File, HTTPException, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from src.utils.helpers import load_config
from src.agent.orchestrator import AudioAnalysisAgent
from src.transcription.transcriber import Transcriber
from src.tools.silence import configure as configure_silence
from src.tools.volume import configure as configure_volume

load_dotenv()

# ── Konstanta ─────────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).parent
CONFIG_PATH = BASE_DIR / "config" / "settings.yaml"
UPLOAD_DIR = BASE_DIR / "data" / "uploads"
FILE_TTL_SECONDS = 30 * 60  # 30 menit — file di-cleanup setelah ini
CLEANUP_INTERVAL_SECONDS = 15 * 60  # cek setiap 15 menit

SUPPORTED_EXTENSIONS = {".mp3", ".wav", ".m4a", ".webm", ".ogg", ".flac", ".aac", ".wma"}

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("voicescript.api")

# ── Background Cleanup Task ───────────────────────────────────────────────────

async def cleanup_old_uploads():
    """Hapus file upload yang berumur lebih dari FILE_TTL_SECONDS secara periodik."""
    while True:
        await asyncio.sleep(CLEANUP_INTERVAL_SECONDS)
        if UPLOAD_DIR.exists():
            now = time.time()
            deleted = 0
            for f in UPLOAD_DIR.iterdir():
                if f.is_file() and (now - f.stat().st_mtime) > FILE_TTL_SECONDS:
                    try:
                        f.unlink()
                        deleted += 1
                    except OSError:
                        pass
            if deleted:
                logger.info(f"[Cleanup] Dihapus {deleted} file upload kadaluarsa.")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle: jalankan background cleanup saat startup."""
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    task = asyncio.create_task(cleanup_old_uploads())
    logger.info("[API] VoiceScript API started. Upload dir: %s", UPLOAD_DIR)
    yield
    task.cancel()
    logger.info("[API] VoiceScript API shutting down.")


# ── FastAPI App ───────────────────────────────────────────────────────────────

app = FastAPI(
    title="VoiceScript API",
    description="REST API untuk Audio Analysis Agent & Transcription.",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS: di production, set CORS_ORIGINS=https://your-app.vercel.app
_default_origins = ["http://localhost:5173", "http://127.0.0.1:5173"]
_env_origins = os.getenv("CORS_ORIGINS", "")
_origins = [o.strip() for o in _env_origins.split(",") if o.strip()] if _env_origins else _default_origins

app.add_middleware(
    CORSMiddleware,
    allow_origins=_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Helper ────────────────────────────────────────────────────────────────────

def _save_upload(upload: UploadFile) -> Path:
    """Simpan file upload ke UPLOAD_DIR dengan UUID filename. Return path-nya."""
    suffix = Path(upload.filename).suffix.lower()
    if suffix not in SUPPORTED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Format tidak didukung: '{suffix}'. "
                   f"Format yang diterima: {', '.join(sorted(SUPPORTED_EXTENSIONS))}",
        )
    unique_name = f"{uuid.uuid4().hex}{suffix}"
    dest = UPLOAD_DIR / unique_name
    with dest.open("wb") as f:
        shutil.copyfileobj(upload.file, f)
    logger.info("[Upload] Disimpan: %s (%d bytes)", dest.name, dest.stat().st_size)
    return dest


def _load_settings():
    return load_config(str(CONFIG_PATH))


# ── Endpoints ─────────────────────────────────────────────────────────────────

@app.get("/api/health", tags=["System"])
def health():
    """Cek status API dan konfigurasi aktif."""
    settings = _load_settings()
    return {
        "status": "ok",
        "llm_model": os.getenv("GROQ_MODEL", settings.get("analysis", {}).get("llm_model", "N/A")),
        "transcription_model": settings.get("api", {}).get("model", "N/A"),
        "upload_dir": str(UPLOAD_DIR),
        "supported_formats": sorted(SUPPORTED_EXTENSIONS),
    }


@app.get("/api/config", tags=["System"])
def get_config():
    """Kembalikan konfigurasi aktif dari settings.yaml (read-only)."""
    return _load_settings()


@app.post("/api/analyze", tags=["Analysis"])
async def analyze_audio(file: UploadFile = File(...)):
    """
    Upload file audio dan jalankan Audio Quality Analysis Agent.

    Mengembalikan JSON report: metadata, audio_quality, issues, llm_insights.
    File akan otomatis dihapus setelah 30 menit.
    """
    temp_path = None
    try:
        temp_path = _save_upload(file)
        settings = _load_settings()

        analysis_cfg = settings.get("analysis", {})
        configure_silence(analysis_cfg)
        configure_volume(analysis_cfg)

        agent = AudioAnalysisAgent(settings, use_cache=False)

        # Jalankan di thread pool agar tidak blocking event loop
        loop = asyncio.get_event_loop()
        report = await loop.run_in_executor(
            None, lambda: agent.analyze(str(temp_path), verbose=False)
        )

        if "error" in report:
            raise HTTPException(status_code=500, detail=report["error"])

        # Tambahkan nama file asli ke report
        report["original_filename"] = file.filename
        return JSONResponse(content=report)

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("[Analyze] Unexpected error")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/transcribe", tags=["Transcription"])
async def transcribe_audio(
    file: UploadFile = File(...),
    language: str = Form(default="id"),
    output_format: str = Form(default="txt"),
):
    """
    Upload file audio dan transkripsi menggunakan Groq Whisper.

    - **language**: Kode bahasa (id, en, dll). Default: id
    - **output_format**: txt | srt | vtt | json. Default: txt

    File akan otomatis dihapus setelah 30 menit.
    """
    if output_format not in {"txt", "srt", "vtt", "json"}:
        raise HTTPException(status_code=400, detail="output_format harus: txt, srt, vtt, atau json")

    temp_path = None
    try:
        temp_path = _save_upload(file)
        settings = _load_settings()
        transcriber = Transcriber(settings)

        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None,
            lambda: transcriber.transcribe_file(
                file_path=str(temp_path),
                language=language,
                response_format=output_format,
            ),
        )

        return JSONResponse(content={
            "original_filename": file.filename,
            "language": language,
            "output_format": output_format,
            "transcript": result,
        })

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("[Transcribe] Unexpected error")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("web_api:app", host="0.0.0.0", port=8000, reload=True)
