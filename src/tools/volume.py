"""
Tool: detect_clipping
Mengukur level volume dan mendeteksi clipping pada file audio menggunakan ffmpeg volumedetect.
Command: ffmpeg -i <file> -af volumedetect -f null -
"""
import re
import subprocess
import os
from src.tools.ffmpeg_finder import find_ffmpeg
from src.tools.registry import register_tool

_CONFIG = {
    "clipping_threshold_db": -1.0,
    "low_volume_threshold_db": -35.0,
}


def configure(analysis_settings: dict) -> None:
    """Override default config dari blok 'analysis' di settings.yaml.
    
    Dipanggil sekali saat startup oleh main.py atau orchestrator.
    """
    if "clipping_threshold_db" in analysis_settings:
        _CONFIG["clipping_threshold_db"] = float(analysis_settings["clipping_threshold_db"])
    if "low_volume_threshold_db" in analysis_settings:
        _CONFIG["low_volume_threshold_db"] = float(analysis_settings["low_volume_threshold_db"])


@register_tool
def detect_clipping(file_path: str, clipping_threshold_db: float = None, low_volume_threshold_db: float = None) -> dict:
    """
    Mengukur level volume dan mendeteksi clipping pada file audio.
    
    Args:
        file_path: Path ke file audio.
        clipping_threshold_db: Max volume >= ini dianggap clipping (default: -1.0 dB).
        low_volume_threshold_db: Mean volume < ini dianggap terlalu rendah (default: -35.0 dB).
    
    Returns:
        dict dengan kunci: mean_volume_db, max_volume_db, volume_clipping,
        clipping_severity, histogram
    """
    if not os.path.exists(file_path):
        return {"error": f"File tidak ditemukan: {file_path}"}
    
    if clipping_threshold_db is None:
        clipping_threshold_db = _CONFIG["clipping_threshold_db"]
    if low_volume_threshold_db is None:
        low_volume_threshold_db = _CONFIG["low_volume_threshold_db"]
    
    ffmpeg = find_ffmpeg()
    
    cmd = [
        ffmpeg,
        "-i", file_path,
        "-af", "volumedetect",
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
        
        # Parse metrik volumedetect: mean_volume, max_volume, histogram
        mean_match = re.search(r"mean_volume:\s*([-\d.]+)\s*dB", stderr)
        max_match = re.search(r"max_volume:\s*([-\d.]+)\s*dB", stderr)
        
        mean_volume = float(mean_match.group(1)) if mean_match else None
        max_volume = float(max_match.group(1)) if max_match else None
        
        histogram = {}
        hist_matches = re.findall(r"histogram_(\d+)db:\s*(\d+)", stderr)
        for db_val, count in hist_matches:
            histogram[f"-{db_val}dB"] = int(count)
        
        clipping_threshold = clipping_threshold_db
        low_vol_threshold = low_volume_threshold_db
        
        clipping = False
        clipping_severity = "none"
        if max_volume is not None:
            if max_volume >= 0.0:
                clipping = True
                clipping_severity = "severe"
            elif max_volume >= clipping_threshold:
                clipping = True
                clipping_severity = "moderate"
            elif max_volume >= clipping_threshold - 2.0:  # warning zone = 2dB sebelum threshold
                clipping_severity = "warning"
        
        low_volume = False
        if mean_volume is not None and mean_volume < low_vol_threshold:
            low_volume = True
        
        return {
            "mean_volume_db": round(mean_volume, 2) if mean_volume is not None else None,
            "max_volume_db": round(max_volume, 2) if max_volume is not None else None,
            "volume_clipping": clipping,
            "clipping_severity": clipping_severity,
            "low_volume_detected": low_volume,
            "histogram": histogram
        }
        
    except subprocess.TimeoutExpired:
        return {"error": "ffmpeg timeout setelah 120 detik."}
    except FileNotFoundError:
        return {"error": "ffmpeg tidak ditemukan. Pastikan ffmpeg terinstal."}
