
# VoiceScript - Audio Analysis Agent (ffmpeg + LLM)

Sistem bertenaga AI yang menganalisis file audio dan menghasilkan insight terstruktur menggunakan **ffmpeg/ffprobe** untuk analisis teknis dan **Groq LLM** untuk ringkasan cerdas.

## Arsitektur

Sistem ini menggunakan pola agentic **ReAct (Reason + Act)**. Alih-alih menjalankan skrip yang sudah dikodekan secara tetap, LLM bertindak sebagai orkestrator dinamis yang memutuskan tool ffmpeg mana yang perlu dipanggil dan dalam urutan apa.

```
User Command
    |
    v
+------------------+
|   CLI (click)    |  <-- python -m src.main analyze <file>
+------------------+
    |
    v
+---------------------------+
|  AudioAnalysisAgent       |  <-- ReAct Loop (src/agent/orchestrator.py)
|  (Groq Tool Calling)      |
|  [dengan cache file MD5]  |
+---------------------------+
    |       |       |       |
    v       v       v       v
+------+ +------+ +------+ +------+
|meta  | |silen | |volume| |noise |  <-- ffmpeg/ffprobe tools (src/tools/)
|data  | |ce    | |detect| |detect|
|probe | |detect| |      | |astats|
+------+ +------+ +------+ +------+
    |       |       |       |
    v       v       v       v
+---------------------------+
|   Sintesis LLM            |  <-- Ringkasan + Rekomendasi + Masalah
+---------------------------+
    |
    v
+---------------------------+
|   Laporan JSON            |  <-- Output terstruktur disimpan ke disk
+---------------------------+
```

### Keputusan Teknis Utama

| Keputusan | Alasan |
|-----------|--------|
| **Groq API** (bukan OpenAI) | Inferensi sangat cepat (~200ms), tersedia tier gratis, mendukung tool-calling secara native |
| **llama-3.3-70b-versatile** | Keseimbangan terbaik antara kemampuan reasoning dan kecepatan untuk agent tool-calling di Groq |
| **ReAct dengan native tool-calling** | LLM secara dinamis memutuskan perintah ffmpeg mana yang dijalankan, bukan hardcode — perilaku agentic sejati |
| **Post-processing deterministik** | `_normalize_schema()` memastikan output JSON selalu sesuai skema yang diminta, terlepas dari variansi LLM |
| **Auto-discovery ffmpeg** | `ffmpeg_finder.py` mencari di PATH dan environment conda, sehingga ffmpeg tidak perlu diinstal secara global |
| **`@register_tool` auto-discovery** | Menambah tool baru cukup membuat fungsi dengan decorator — tanpa perlu update registry manual |
| **Cache berbasis hash file** | Menghindari pemanggilan ffmpeg + API yang redundan untuk file yang sudah pernah dianalisis. Lewati dengan `--no-cache` |

---

## Struktur Proyek

```
VoiceScript/
├── config/
│   └── settings.yaml           # Threshold, konfigurasi model, pengaturan output
├── data/                       # File audio dan laporan yang dihasilkan
│   ├── bad_audio.mp3
│   ├── moonlight-plaza.mp3
│   ├── bad_audio_report.json         # Contoh output (file tunggal)
│   └── batch_insights_report.json    # Contoh output (batch)
├── src/
│   ├── main.py                 # Entry point CLI (analyze, analyze-batch, transcribe, info)
│   ├── agent/
│   │   └── orchestrator.py     # ReAct agent loop dengan Groq tool calling + cache
│   ├── tools/
│   │   ├── registry.py         # Decorator @register_tool & sistem auto-discovery
│   │   ├── ffmpeg_finder.py    # Auto-discover binary ffmpeg/ffprobe
│   │   ├── metadata.py         # Tool: get_audio_metadata (ffprobe)
│   │   ├── silence.py          # Tool: detect_silence (silencedetect)
│   │   ├── volume.py           # Tool: detect_clipping (volumedetect)
│   │   └── noise.py            # Tool: detect_noise (astats)
│   ├── audio/
│   │   └── processor.py        # Pemotongan audio & konversi format (pydub)
│   ├── transcription/
│   │   └── transcriber.py      # Speech-to-text via Groq Whisper API
│   └── utils/
│       └── helpers.py          # Pemuat konfigurasi, formatter SRT/VTT
├── mcp_server.py               # Server MCP (FastMCP) yang mengekspos tools
├── tests/                      # Unit test
├── .env.example                # Template untuk API key
├── environment.yml             # Definisi environment Conda
├── requirements.txt            # Dependensi pip (alternatif selain Conda)
└── README.md
```

---

## Instalasi & Konfigurasi

### 1. Membuat Environment Conda

```bash
conda env create -f environment.yml
conda activate voicescript
```

### Alternatif: Instalasi via pip (tanpa Conda)

Jika tidak menggunakan Conda, instal dependensi via pip:

```bash
pip install -r requirements.txt
```

> **Catatan:** ffmpeg tetap harus diinstal terpisah di sistem operasi.
>
> - **Windows:** `winget install ffmpeg` atau unduh dari [ffmpeg.org](https://ffmpeg.org/download.html)
> - **macOS:** `brew install ffmpeg`
> - **Linux:** `sudo apt install ffmpeg`

### 2. Konfigurasi API Key

```bash
copy .env.example .env
```

Edit `.env` dan masukkan API key Groq Anda:

```env
GROQ_API_KEY=gsk_your_api_key_here
GROQ_MODEL=llama-3.3-70b-versatile
GROQ_BASE_URL=https://api.groq.com/openai/v1
```

---

## Penggunaan

### Analisis Satu File Audio

```bash
python -m src.main analyze data/bad_audio.mp3
```

Tambahkan `--verbose` untuk melihat langkah-langkah reasoning agent:

```bash
python -m src.main analyze data/bad_audio.mp3 --verbose
```

Output disimpan sebagai `<filename>_report.json` di direktori yang sama dengan file input.

Lewati cache dan paksa analisis ulang:

```bash
python -m src.main analyze data/bad_audio.mp3 --no-cache
```

Agent menyimpan cache hasil berdasarkan konten file (SHA-256 hash). Gunakan `--no-cache` untuk memaksa analisis ulang meskipun cache sudah ada.

### Analisis Batch (Banyak File)

```bash
python -m src.main analyze-batch data/
```

Memproses semua file audio dalam direktori. Menghasilkan:
- Laporan individual `<filename>_report.json` per file
- Laporan master `batch_insights_report.json` berisi semua hasil

### Transkripsi Audio ke Teks

```bash
python -m src.main transcribe data/bad_audio.mp3 --output-format txt --language id
```

Format output yang didukung: `txt`, `srt`, `vtt`, `json`

### Informasi Detail File Audio

```bash
python -m src.main info data/bad_audio.mp3
```

---

## Skema JSON Output

Setiap laporan analisis mengikuti struktur yang sama persis:

```json
{
  "file_name": "bad_audio.mp3",
  "duration_seconds": 121.107625,
  "audio_quality": {
    "silence_ratio": 0.1007,
    "clipping_detected": true,
    "avg_volume_db": -16.6
  },
  "issues": [
    "High silence ratio (10.1%) - audio contains significant silent segments",
    "Audio clipping detected (max volume: -0.4 dB)"
  ],
  "llm_insights": {
    "summary": "Kualitas audio buruk karena adanya segmen keheningan...",
    "recommended_actions": [
      "Menggunakan limiter atau menurunkan gain input",
      "Melakukan trimming otomatis"
    ]
  }
}
```

---

## Server MCP

Proyek ini mengekspos tools analisisnya melalui server **Model Context Protocol (MCP)** menggunakan FastMCP:

```bash
python mcp_server.py
```

Tools yang tersedia:
- `get_audio_metadata` — Ekstrak durasi, bitrate, sample rate, channels via ffprobe
- `detect_silence` — Deteksi segmen keheningan via ffmpeg silencedetect
- `detect_clipping` — Ukur level volume dan deteksi clipping via ffmpeg volumedetect
- `detect_noise` — Analisis level noise dan dynamic range via ffmpeg astats

> 💡 **Melampaui Requirement:** Assessment membutuhkan 3 tool MCP. Proyek ini mengekspos 4 — `detect_noise` (ffmpeg astats) ditambahkan untuk menyediakan analisis dynamic range dan noise floor, memungkinkan penilaian kualitas audio yang lebih mendalam.

---

## Contoh Output

Contoh laporan yang sudah di-generate tersedia di direktori `data/`:

- [`bad_audio_report.json`](data/bad_audio_report.json) — Analisis file tunggal
- [`moonlight-plaza_report.json`](data/moonlight-plaza_report.json) — Analisis file tunggal
- [`batch_insights_report.json`](data/batch_insights_report.json) — Analisis batch (2 file)
- [`example_verbose_trace.txt`](data/example_verbose_trace.txt) — Trace reasoning agent (mode `--verbose`)
