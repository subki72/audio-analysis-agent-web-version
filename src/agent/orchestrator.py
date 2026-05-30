"""
Audio Analysis Agent — ReAct Loop dengan Groq Tool Calling.

Pola ReAct (Reason + Act):
1. Agent menerima prompt awal untuk menganalisis file audio.
2. LLM secara dinamis memutuskan tool mana yang perlu dipanggil.
3. Setelah semua data terkumpul, LLM menghasilkan summary & recommended_actions.
4. Hasil akhir dikemas dalam JSON report.
"""
import os
import json
import hashlib
import platform
from dotenv import load_dotenv
from groq import Groq

from src.tools import TOOL_REGISTRY, TOOL_SCHEMAS

load_dotenv()

SYSTEM_PROMPT = """Kamu adalah Audio Analysis Agent yang ahli dalam analisis kualitas audio.
Tugasmu adalah menganalisis file audio secara menyeluruh dan memberikan penilaian profesional.

Kamu memiliki akses ke 4 tools:
1. get_audio_metadata — Mengambil metadata teknis (format, durasi, sample rate, channels, codec, bitrate).
2. detect_silence — Mendeteksi segmen keheningan beserta posisi waktunya dalam audio.
3. detect_clipping — Mengukur level volume dan mendeteksi distorsi/clipping.
4. detect_noise — Menganalisis noise level dan dynamic range audio.

LANGKAH KERJA:
1. Panggil keempat tools tersebut untuk mengumpulkan data teknis secara lengkap.
2. Analisis data yang kamu terima — gunakan judgment profesionalmu untuk menilai
   apakah kondisi audio tersebut bermasalah, mengacu pada standar industri rekaman audio.
3. Hasilkan laporan akhir dalam format JSON berikut (tanpa markdown code fence):

{
  "file_name": "<nama file>",
  "duration_seconds": <durasi dalam detik>,
  "audio_quality": {
    "silence_ratio": <rasio 0.0–1.0>,
    "clipping_detected": <true/false>,
    "avg_volume_db": <angka dB>
  },
  "issues": [
    "<deskripsi masalah spesifik dalam Bahasa Inggris, sertakan angka dan timestamp jika relevan>"
  ],
  "llm_insights": {
    "summary": "<analisis kondisi kualitas audio secara keseluruhan dalam Bahasa Indonesia>",
    "recommended_actions": ["<aksi konkret 1>", "<aksi konkret 2>"]
  }
}

PANDUAN ANALISIS:
- Nilai setiap metrik berdasarkan konteks penggunaan audio (rekaman deposisi hukum).
- Untuk field "issues": tulis deskripsi spesifik yang mencantumkan nilai aktual dan,
  jika ada data segmen, sertakan rentang waktu (contoh: "silence detected at 12.5s–45.2s").
- Jika audio tidak memiliki masalah signifikan, kembalikan array "issues" kosong: [].
- Tulis "summary" dan "recommended_actions" dalam Bahasa Indonesia yang profesional.
- Semua angka di "audio_quality" HARUS berasal dari data tool — jangan estimasi.
"""


class AudioAnalysisAgent:
    """ReAct Agent untuk menganalisis file audio menggunakan Groq tool calling."""
    
    def __init__(self, settings: dict = None, use_cache: bool = True):
        self.settings = settings or {}
        api_settings = self.settings.get("api", {})
        
        self.api_key = os.getenv("GROQ_API_KEY")
        self.model = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
        
        if not self.api_key:
            raise ValueError("GROQ_API_KEY tidak ditemukan di file .env")
        
        # Hapus suffix /openai/v1 — Groq SDK menambahkannya secara otomatis
        base_url = os.getenv("GROQ_BASE_URL")
        if base_url:
            if base_url.endswith("/openai/v1"):
                base_url = base_url[:-10]
            elif base_url.endswith("/openai/v1/"):
                base_url = base_url[:-11]
        
        if base_url:
            self.client = Groq(api_key=self.api_key, base_url=base_url)
        else:
            self.client = Groq(api_key=self.api_key)
        
        self.max_iterations = 10  # Safety limit untuk loop ReAct
        
        analysis_cfg = self.settings.get("analysis", {})
        self.noise_threshold = analysis_cfg.get("noise_threshold", "-50dB")
        self.min_silence_duration = analysis_cfg.get("min_silence_duration", 2.0)
        self.clipping_threshold_db = analysis_cfg.get("clipping_threshold_db", -1.0)
        self.low_volume_threshold_db = analysis_cfg.get("low_volume_threshold_db", -35.0)
        
        self.use_cache = use_cache
        self._current_tool_results = {}
        
        # User ID yang di-hash untuk pencegahan penyalahgunaan Groq (tanpa data pribadi)
        raw_id = f"voicescript-{platform.node()}"
        self.user_id = hashlib.sha256(raw_id.encode()).hexdigest()[:16]
    
    def analyze(self, file_path: str, verbose: bool = False) -> dict:
        """
        Menjalankan loop ReAct untuk menganalisis satu file audio.
        
        Args:
            file_path: Path ke file audio.
            verbose: Jika True, cetak langkah-langkah agent ke konsol.
            
        Returns:
            dict berisi laporan analisis JSON.
        """
        if not os.path.exists(file_path):
            return {"error": f"File tidak ditemukan: {file_path}"}
        
        cache_path = None
        if self.use_cache:
            cache_dir = os.path.join(
                os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
                ".cache"
            )
            os.makedirs(cache_dir, exist_ok=True)
            try:
                with open(file_path, "rb") as f:
                    file_hash = hashlib.sha256(f.read()).hexdigest()
                cache_path = os.path.join(cache_dir, f"{file_hash}_report.json")
                
                if os.path.exists(cache_path):
                    if verbose:
                        print(f"  [Cache] Hit! Menggunakan laporan tersimpan untuk file ini.")
                    with open(cache_path, "r", encoding="utf-8") as f:
                        return json.load(f)
            except Exception:
                cache_path = None
        
        self._current_tool_results = {}
        
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": (
                    f"Analisis file audio di path berikut: {file_path}\n"
                    f"Ekstrak metadata, deteksi masalah kualitas (silence, clipping, low volume), "
                    f"dan hasilkan laporan JSON akhir."
                )
            }
        ]
        
        for iteration in range(self.max_iterations):
            if verbose:
                print(f"  [Agent] Iterasi {iteration + 1}...")
            
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    tools=TOOL_SCHEMAS,
                    tool_choice="auto",
                    temperature=0.1,
                    max_tokens=4096,
                    user=self.user_id
                )
            except Exception as e:
                if verbose:
                    print(f"  [Agent] API call failed: {e}")
                return {"error": f"Gagal memanggil API: {str(e)}"}
            
            assistant_message = response.choices[0].message
            
            if assistant_message.tool_calls:
                messages.append({
                    "role": "assistant",
                    "content": assistant_message.content or "",
                    "tool_calls": [
                        {
                            "id": tc.id,
                            "type": "function",
                            "function": {
                                "name": tc.function.name,
                                "arguments": tc.function.arguments
                            }
                        }
                        for tc in assistant_message.tool_calls
                    ]
                })
                
                for tool_call in assistant_message.tool_calls:
                    fn_name = tool_call.function.name
                    fn_args = json.loads(tool_call.function.arguments)
                    
                    if verbose:
                        print(f"  [Tool Call] {fn_name}({json.dumps(fn_args, ensure_ascii=False)})")
                    
                    # Suntikkan nilai default dari settings jika LLM tidak menyertakan argumen
                    if fn_name == "detect_silence":
                        fn_args.setdefault("noise_threshold", self.noise_threshold)
                        fn_args.setdefault("min_duration", self.min_silence_duration)
                    if fn_name == "detect_clipping":
                        fn_args.setdefault("clipping_threshold_db", self.clipping_threshold_db)
                        fn_args.setdefault("low_volume_threshold_db", self.low_volume_threshold_db)
                    
                    if fn_name in TOOL_REGISTRY:
                        tool_result = TOOL_REGISTRY[fn_name](**fn_args)
                        self._current_tool_results[fn_name] = tool_result
                    else:
                        tool_result = {"error": f"Tool tidak dikenal: {fn_name}"}
                    
                    result_str = json.dumps(tool_result, ensure_ascii=False, indent=2)
                    
                    if verbose:
                        # Tampilkan ringkasan hasil (truncate jika terlalu panjang)
                        preview = result_str[:200] + "..." if len(result_str) > 200 else result_str
                        print(f"  [Result]    {preview}")
                    
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": result_str
                    })
            else:
                # LLM tidak memanggil tool lagi — ini adalah respons akhir
                final_content = assistant_message.content or ""
                
                if verbose:
                    print("  [Agent] Menyusun laporan akhir...")
                
                result = self._parse_final_report(final_content)
                
                if cache_path and "error" not in result:
                    try:
                        with open(cache_path, "w", encoding="utf-8") as f:
                            json.dump(result, f, ensure_ascii=False, indent=2)
                        if verbose:
                            print(f"  [Cache] Laporan disimpan ke cache.")
                    except Exception:
                        pass
                
                return result
        
        return {"error": "Agent mencapai batas iterasi maksimum tanpa menghasilkan laporan."}
    
    def _parse_final_report(self, content: str) -> dict:
        """Parse respons akhir LLM menjadi dict JSON, lalu normalisasi ke schema assessment."""
        cleaned = content.strip()
        if cleaned.startswith("```json"):
            cleaned = cleaned[7:]
        if cleaned.startswith("```"):
            cleaned = cleaned[3:]
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]
        cleaned = cleaned.strip()
        
        parsed = None
        try:
            parsed = json.loads(cleaned)
        except json.JSONDecodeError:
            import re
            json_match = re.search(r'\{[\s\S]*\}', cleaned)
            if json_match:
                try:
                    parsed = json.loads(json_match.group())
                except json.JSONDecodeError:
                    pass
        
        if parsed is None:
            return {
                "file_name": "unknown",
                "duration_seconds": 0,
                "audio_quality": {
                    "silence_ratio": 0,
                    "clipping_detected": False,
                    "avg_volume_db": 0
                },
                "issues": [],
                "llm_insights": {
                    "summary": content,
                    "recommended_actions": ["Gagal mem-parsing output JSON dari LLM."],
                    "_raw_response": content
                }
            }
        
        return self._normalize_schema(parsed, self._current_tool_results)
    
    def _normalize_schema(self, raw: dict, tool_results: dict = None) -> dict:
        """Normalisasi output LLM ke schema assessment secara deterministik.
        
        Menangani baik schema lama (file_metadata/audio_metrics) maupun
        schema baru (file_name/audio_quality/issues) yang diminta LLM.
        
        Args:
            raw: Dict hasil parsing JSON dari respons LLM.
            tool_results: Dict raw tool results yang dikumpulkan selama ReAct loop.
        """
        tool_results = tool_results or {}
        
        # --- Resolusi file_name ---
        file_name = raw.get("file_name")
        if not file_name:
            fm = raw.get("file_metadata", {})
            file_name = fm.get("filename", fm.get("file_name", "unknown"))
        
        # --- Resolusi duration_seconds ---
        duration = raw.get("duration_seconds")
        if duration is None:
            fm = raw.get("file_metadata", {})
            duration = fm.get("duration_seconds", 0)
        
        # --- Resolusi audio_quality ---
        aq = raw.get("audio_quality", {})
        am = raw.get("audio_metrics", {})
        
        silence_ratio = aq.get("silence_ratio", am.get("silence_ratio", 0))
        clipping_detected = aq.get("clipping_detected", am.get("volume_clipping", am.get("clipping_detected", False)))
        avg_volume_db = aq.get("avg_volume_db", am.get("avg_volume_db", am.get("mean_volume_db", 0)))
        
        # --- Resolusi issues ---
        issues = raw.get("issues")
        if issues is None:
            issues = []
            if silence_ratio and silence_ratio > 0.1:
                pct = round(silence_ratio * 100, 1)
                base_issue = f"High silence ratio ({pct}%) - audio contains significant silent segments"
                
                silence_data = tool_results.get("detect_silence", {})
                silence_segments = (
                    raw.get("silence_segments", []) or
                    silence_data.get("silence_segments", [])
                )
                if silence_segments:
                    longest = sorted(
                        silence_segments,
                        key=lambda s: s.get("duration", 0),
                        reverse=True
                    )[:3]
                    segment_strs = [
                        f"{s['start']:.1f}s\u2013{s['end']:.1f}s ({s['duration']:.1f}s)"
                        for s in longest
                        if all(k in s for k in ("start", "end", "duration"))
                    ]
                    if segment_strs:
                        base_issue += f". Longest silent segments: {', '.join(segment_strs)}"
                
                issues.append(base_issue)
            if clipping_detected:
                max_vol = am.get("max_volume_db", aq.get("max_volume_db", "N/A"))
                issues.append(f"Audio clipping detected (max volume: {max_vol} dB)")
            if avg_volume_db and avg_volume_db < -35:
                issues.append(f"Unusually low average volume ({avg_volume_db} dB)")
        
        # --- Resolusi llm_insights ---
        insights = raw.get("llm_insights", {})
        summary = insights.get("summary", "")
        actions = insights.get("recommended_actions", [])
        
        return {
            "file_name": file_name,
            "duration_seconds": duration,
            "audio_quality": {
                "silence_ratio": silence_ratio,
                "clipping_detected": clipping_detected,
                "avg_volume_db": avg_volume_db
            },
            "issues": issues,
            "llm_insights": {
                "summary": summary,
                "recommended_actions": actions
            }
        }
