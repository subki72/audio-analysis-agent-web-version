import os
import sys
import json
import click
from dotenv import load_dotenv

from src.utils.helpers import load_config
from src.audio.processor import AudioProcessor
from src.transcription.transcriber import Transcriber
from src.agent.orchestrator import AudioAnalysisAgent
from src.tools.silence import configure as configure_silence
from src.tools.volume import configure as configure_volume

load_dotenv()

CONFIG_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config', 'settings.yaml')

SUPPORTED_EXTENSIONS = {'.mp3', '.wav', '.m4a', '.webm', '.ogg', '.flac', '.aac', '.wma'}


@click.group()
def cli():
    """VoiceScript - Audio Analysis Agent & Transcription Tool (Groq API)."""
    pass


# ============================================================
# Perintah Transkripsi 
# ============================================================

@cli.command()
@click.argument('audio_path', type=click.Path(exists=True))
@click.option('--output-format', '-f', default=None, type=click.Choice(['txt', 'srt', 'vtt', 'json']), help='Format output transkripsi.')
@click.option('--language', '-l', default='id', help='Kode bahasa audio (contoh: id, en).')
def transcribe(audio_path, output_format, language):
    """Mentranskripsi file audio ke format teks/script."""
    settings = load_config(CONFIG_PATH)
    
    if not output_format:
        output_format = settings.get('output', {}).get('default_format', 'txt')
        
    click.echo(f"[*] Menggunakan provider: GROQ")
    click.echo(f"[*] Model transkripsi: {settings.get('api', {}).get('model', 'whisper-large-v3')}")
    click.echo(f"[*] File audio: {audio_path}")
    click.echo(f"[*] Bahasa target: {language} | Format output: {output_format}")
    
    try:
        processor = AudioProcessor(settings)
        transcriber = Transcriber(settings)
        
        meta = processor.get_metadata(audio_path)
        click.echo(f"[*] Ukuran audio: {meta['size_bytes'] / (1024*1024):.2f} MB")
        
        max_size_mb = settings.get('audio', {}).get('max_size_mb', 25)
        audio_files = processor.split_audio(audio_path, max_size_mb=max_size_mb)
        
        full_transcript = []
        for i, file_segment in enumerate(audio_files):
            if len(audio_files) > 1:
                click.echo(f"[*] Mentranskripsi bagian {i+1}/{len(audio_files)}...")
            else:
                click.echo("[*] Mengirim audio ke API...")
                
            response = transcriber.transcribe_file(
                file_path=file_segment,
                language=language,
                response_format=output_format
            )
            full_transcript.append(response)
            
        combined_text = "\n\n".join(full_transcript)
        
        filename = os.path.basename(audio_path)
        name_without_ext = os.path.splitext(filename)[0]
        out_dir = settings.get('output', {}).get('dir', 'data/transcripts')
        out_path = os.path.join(out_dir, f"{name_without_ext}.{output_format}")
        
        transcriber.save_output(combined_text, out_path)
        click.echo(click.style(f"[+] Transkripsi selesai! Output disimpan ke: {out_path}", fg='green'))
        
    except Exception as e:
        click.echo(click.style(f"[-] Terjadi kesalahan: {e}", fg='red'), err=True)
        sys.exit(1)


@cli.command()
@click.argument('audio_path', type=click.Path(exists=True))
def info(audio_path):
    """Menampilkan detail dan informasi metadata dari file audio."""
    settings = load_config(CONFIG_PATH)
    processor = AudioProcessor(settings)
    
    try:
        meta = processor.get_metadata(audio_path)
        click.echo(f"File Path        : {meta['path']}")
        click.echo(f"Format           : {meta['format'].upper()}")
        click.echo(f"Ukuran File      : {meta['size_bytes'] / (1024*1024):.2f} MB ({meta['size_bytes']} bytes)")
        click.echo(f"Durasi Estimasi  : {meta['duration_seconds']} detik")
    except Exception as e:
        click.echo(click.style(f"[-] Gagal membaca file: {e}", fg='red'), err=True)


# ============================================================
# Perintah Audio Analysis Agent 
# ============================================================

@cli.command()
@click.argument('audio_path', type=click.Path(exists=True))
@click.option('--verbose', '-v', is_flag=True, help='Tampilkan langkah-langkah agent secara detail.')
@click.option('--no-cache', is_flag=True, help='Abaikan cache, paksa analisis ulang.')
def analyze(audio_path, verbose, no_cache):
    """Menganalisis kualitas file audio menggunakan Agent (ffmpeg + LLM).
    
    Agent akan secara dinamis memanggil tools ffmpeg untuk mengekstrak metadata,
    mendeteksi silence, dan mengukur volume/clipping. Kemudian LLM akan
    menghasilkan summary dan rekomendasi perbaikan.
    
    Output: <filename>_report.json
    """
    settings = load_config(CONFIG_PATH)
    
    analysis_cfg = settings.get("analysis", {})
    configure_silence(analysis_cfg)
    configure_volume(analysis_cfg)
    
    click.echo(click.style("+==========================================+", fg='cyan'))
    click.echo(click.style("|   Audio Analysis Agent (ffmpeg + LLM)    |", fg='cyan'))
    click.echo(click.style("+==========================================+", fg='cyan'))
    click.echo(f"[*] File target: {audio_path}")
    click.echo(f"[*] Model LLM : {os.getenv('GROQ_MODEL', 'llama-3.3-70b-versatile')}")
    click.echo()
    
    try:
        agent = AudioAnalysisAgent(settings, use_cache=not no_cache)
        
        click.echo("[*] Memulai loop ReAct Agent...")
        report = agent.analyze(audio_path, verbose=verbose)
        
        if "error" in report:
            click.echo(click.style(f"[-] Error: {report['error']}", fg='red'), err=True)
            sys.exit(1)
        
        filename = os.path.basename(audio_path)
        name_without_ext = os.path.splitext(filename)[0]
        report_dir = os.path.dirname(audio_path) or "."
        report_path = os.path.join(report_dir, f"{name_without_ext}_report.json")
        
        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        click.echo()
        click.echo(click.style("=== Laporan Analisis ===", fg='yellow', bold=True))
        
        insights = report.get("llm_insights", {})
        summary = insights.get("summary", "Tidak ada summary.")
        actions = insights.get("recommended_actions", [])
        
        click.echo(f"\n[Summary]\n   {summary}")
        
        if actions:
            click.echo(f"\n[Rekomendasi]")
            for i, action in enumerate(actions, 1):
                click.echo(f"   {i}. {action}")
        
        click.echo()
        click.echo(click.style(f"[+] Laporan lengkap disimpan ke: {report_path}", fg='green'))
        
        click.echo()
        click.echo(click.style("=== JSON Report ===", fg='yellow'))
        click.echo(json.dumps(report, ensure_ascii=False, indent=2))
        
    except Exception as e:
        click.echo(click.style(f"[-] Terjadi kesalahan: {e}", fg='red'), err=True)
        sys.exit(1)


@cli.command(name="analyze-batch")
@click.argument('directory', type=click.Path(exists=True, file_okay=False))
@click.option('--verbose', '-v', is_flag=True, help='Tampilkan langkah-langkah agent secara detail.')
@click.option('--no-cache', is_flag=True, help='Abaikan cache, paksa analisis ulang.')
def analyze_batch(directory, verbose, no_cache):
    """Menganalisis semua file audio dalam satu direktori (Batch Processing).
    
    Setiap file audio valid akan dianalisis oleh Agent secara individual.
    Semua hasil dikumpulkan dalam file master: batch_insights_report.json
    """
    settings = load_config(CONFIG_PATH)
    
    analysis_cfg = settings.get("analysis", {})
    configure_silence(analysis_cfg)
    configure_volume(analysis_cfg)
    
    click.echo(click.style("+==========================================+", fg='cyan'))
    click.echo(click.style("|   Batch Audio Analysis (ffmpeg + LLM)    |", fg='cyan'))
    click.echo(click.style("+==========================================+", fg='cyan'))
    click.echo(f"[*] Direktori target: {directory}")
    click.echo()
    
    audio_files = []
    for fname in sorted(os.listdir(directory)):
        ext = os.path.splitext(fname)[1].lower()
        if ext in SUPPORTED_EXTENSIONS:
            audio_files.append(os.path.join(directory, fname))
    
    if not audio_files:
        click.echo(click.style(f"[-] Tidak ditemukan file audio di: {directory}", fg='red'))
        sys.exit(1)
    
    click.echo(f"[*] Ditemukan {len(audio_files)} file audio:")
    for af in audio_files:
        click.echo(f"    - {os.path.basename(af)}")
    click.echo()
    
    try:
        agent = AudioAnalysisAgent(settings, use_cache=not no_cache)
        batch_results = []
        
        for idx, audio_path in enumerate(audio_files, 1):
            click.echo(click.style(f"--- [{idx}/{len(audio_files)}] {os.path.basename(audio_path)} ---", fg='cyan'))
            
            report = agent.analyze(audio_path, verbose=verbose)
            
            if "error" in report:
                click.echo(click.style(f"  [-] Error: {report['error']}", fg='red'))
            else:
                filename = os.path.basename(audio_path)
                name_without_ext = os.path.splitext(filename)[0]
                individual_path = os.path.join(directory, f"{name_without_ext}_report.json")
                with open(individual_path, "w", encoding="utf-8") as f:
                    json.dump(report, f, ensure_ascii=False, indent=2)
                
                insights = report.get("llm_insights", {})
                summary = insights.get("summary", "N/A")
                click.echo(f"  [+] {summary[:100]}...")
                click.echo(click.style(f"  [+] Disimpan: {individual_path}", fg='green'))
            
            batch_results.append(report)
            click.echo()
        
        master_path = os.path.join(directory, "batch_insights_report.json")
        with open(master_path, "w", encoding="utf-8") as f:
            json.dump(batch_results, f, ensure_ascii=False, indent=2)
        
        click.echo(click.style("===========================================", fg='yellow'))
        click.echo(click.style(f"[+] Batch selesai! {len(audio_files)} file dianalisis.", fg='green', bold=True))
        click.echo(click.style(f"[+] Master report: {master_path}", fg='green'))
        
    except Exception as e:
        click.echo(click.style(f"[-] Terjadi kesalahan: {e}", fg='red'), err=True)
        sys.exit(1)


if __name__ == '__main__':
    cli()
