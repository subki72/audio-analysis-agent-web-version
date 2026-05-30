import yaml

def load_config(config_path: str) -> dict:
    """Membaca file konfigurasi settings.yaml."""
    try:
        with open(config_path, 'r') as f:
            return yaml.safe_load(f) or {}
    except FileNotFoundError:
        return {}

def format_timestamp(seconds: float, is_vtt: bool = False) -> str:
    """Mengubah detik menjadi format SRT (HH:MM:SS,mmm) atau VTT (HH:MM:SS.mmm) timestamp."""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    milliseconds = int(round((seconds - int(seconds)) * 1000))
    
    if milliseconds >= 1000:
        milliseconds = 999
        
    separator = "." if is_vtt else ","
    return f"{hours:02d}:{minutes:02d}:{secs:02d}{separator}{milliseconds:03d}"

def json_to_srt(segments: list) -> str:
    """Mengubah daftar segmen dari verbose_json menjadi teks format SRT."""
    srt_lines = []
    for i, segment in enumerate(segments):
        start = segment.get('start', 0.0)
        end = segment.get('end', 0.0)
        text = segment.get('text', '').strip()
        
        start_str = format_timestamp(start, is_vtt=False)
        end_str = format_timestamp(end, is_vtt=False)
        
        srt_lines.append(f"{i + 1}")
        srt_lines.append(f"{start_str} --> {end_str}")
        srt_lines.append(text)
        srt_lines.append("")  # Spasi kosong antar segmen
        
    return "\n".join(srt_lines)

def json_to_vtt(segments: list) -> str:
    """Mengubah daftar segmen dari verbose_json menjadi teks format VTT."""
    vtt_lines = ["WEBVTT", ""]
    for i, segment in enumerate(segments):
        start = segment.get('start', 0.0)
        end = segment.get('end', 0.0)
        text = segment.get('text', '').strip()
        
        start_str = format_timestamp(start, is_vtt=True)
        end_str = format_timestamp(end, is_vtt=True)
        
        vtt_lines.append(f"{i + 1}")
        vtt_lines.append(f"{start_str} --> {end_str}")
        vtt_lines.append(text)
        vtt_lines.append("")  # Spasi kosong antar segmen
        
    return "\n".join(vtt_lines)
