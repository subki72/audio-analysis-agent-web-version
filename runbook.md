# Operational Runbook — VoiceScript Audio Analysis Agent

## 1. Service Overview
- **REST API**: FastAPI (`web_api:app`, port `8000` local / `7860` Docker & Hugging Face Spaces).
- **MCP Server**: `python mcp_server.py` (Model Context Protocol server exposing ffmpeg tools).
- **Health Endpoint**: `GET /api/health` returns operational status and active configuration.

## 2. Standard Operations
- **Local Startup**: `make run` (backend) and `cd web && npm run dev` (React frontend).
- **Container Startup**: `docker compose up --build -d`.
- **Upload TTL Cleanup**: Background asyncio loop purges temporary uploads older than 30 minutes every 15 minutes.

## 3. Incident Response
| Symptom | Probable Cause | Remediation |
|---|---|---|
| `ffmpeg/ffprobe not found` | Missing binary in container or PATH | Confirm `ffmpeg` package installed in Dockerfile / environment. |
| Groq API 429 or timeout | Upstream LLM quota or rate spike | Rely on MD5 file-hash cache (`use_cache=True`) and verify `GROQ_API_KEY`. |
| HTTP `400` on upload | Unsupported file extension | Verify client uploads one of `.mp3`, `.wav`, `.m4a`, `.webm`, `.ogg`, `.flac`, `.aac`, `.wma`. |

## 4. Rollback Procedure
Revert deployment to pinned semantic git tag `v1.0.0` and rebuild container image via `make docker-build`.
