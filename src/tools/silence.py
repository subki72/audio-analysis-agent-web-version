"""
Tool: detect_silence
Mendeteksi segmen keheningan dalam file audio menggunakan ffmpeg silencedetect.
Command: ffmpeg -i <file> -af silencedetect=noise=-50dB:d=2 -f null -
"""
import re
import subprocess
import os
from src.tools.ffmpeg_finder import find_ffmpeg
from src.tools.registry import register_tool

_CONFIG = {
    "noise_threshold": "-50dB",
    "min_silence_duration": 2.0,
}


def configure(analysis_settings: dict) -> None:
    """Override default config dari blok 'analysis' di settings.yaml.
    
    Dipanggil sekali saat startup oleh main.py atau orchestrator.
    """
    if "noise_threshold" in analysis_settings:
        _CONFIG["noise_threshold"] = str(analysis_settings["noise_threshold"])
    if "min_silence_duration" in analysis_settings:
        _CONFIG["min_silence_duration"] = float(analysis_settings["min_silence_duration"])


@register_tool
def detect_silence(file_path: str, noise_threshold: str = None, min_duration: float = None) -> dict:
    """
    Mendeteksi segmen keheningan dalam file audio.
    
    Args:
        file_path: Path ke file audio.
        noise_threshold: Threshold noise level (default: -50dB).
        min_duration: Durasi minimum keheningan yang dianggap signifikan (detik).
    
    Returns:
        dict dengan kunci: silence_detected, silence_segments, total_silence_duration,
        silence_ratio, audio_duration
    """
    if not os.path.exists(file_path):
        return {"error": f"File tidak ditemukan: {file_path}"}
    
    if noise_threshold is None:
        noise_threshold = _CONFIG["noise_threshold"]
    if min_duration is None:
        min_duration = _CONFIG["min_silence_duration"]
    
    ffmpeg = find_ffmpeg()
    
    cmd = [
        ffmpeg,
        "-i", file_path,
        "-af", f"silencedetect=noise={noise_threshold}:d={min_duration}",
        "-f", "null",
        "-"
    ]
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=120
        )
        
        stderr = result.stderr
        
        # Parse pasangan silence_start / silence_end dari output ffmpeg silencedetect
        silence_starts = re.findall(r"silence_start:\s*([\d.]+)", stderr)
        silence_ends = re.findall(r"silence_end:\s*([\d.]+)\s*\|\s*silence_duration:\s*([\d.]+)", stderr)
        
        duration_match = re.search(r"Duration:\s*(\d+):(\d+):(\d+)\.(\d+)", stderr)
        audio_duration = 0.0
        if duration_match:
            h, m, s, cs = duration_match.groups()
            audio_duration = int(h) * 3600 + int(m) * 60 + int(s) + int(cs) / 100
        
        segments = []
        total_silence = 0.0
        
        for i, (end, duration) in enumerate(silence_ends):
            start = float(silence_starts[i]) if i < len(silence_starts) else 0.0
            dur = float(duration)
            segments.append({
                "start": round(start, 3),
                "end": round(float(end), 3),
                "duration": round(dur, 3)
            })
            total_silence += dur
        
        silence_ratio = round(total_silence / audio_duration, 4) if audio_duration > 0 else 0.0
        
        return {
            "silence_detected": len(segments) > 0,
            "silence_segments": segments,
            "total_silence_duration": round(total_silence, 3),
            "silence_ratio": silence_ratio,
            "audio_duration": round(audio_duration, 3),
            "threshold_used": noise_threshold,
            "min_duration_used": min_duration
        }
        
    except subprocess.TimeoutExpired:
        return {"error": "ffmpeg timeout setelah 120 detik."}
    except FileNotFoundError:
        return {"error": "ffmpeg tidak ditemukan. Pastikan ffmpeg terinstal."}
