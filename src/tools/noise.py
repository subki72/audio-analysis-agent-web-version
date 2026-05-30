"""
Tool: detect_noise
Menganalisis noise level dan dynamic range audio menggunakan ffmpeg astats filter.
Command: ffmpeg -i <file> -af astats=metadata=1:reset=1 -f null -
"""
import re
import subprocess
import os
from src.tools.ffmpeg_finder import find_ffmpeg
from src.tools.registry import register_tool


@register_tool
def detect_noise(file_path: str) -> dict:
    """
    Menganalisis noise level dan dynamic range file audio.
    
    Menggunakan ffmpeg astats filter untuk mengukur RMS level, peak level,
    dynamic range, dan crest factor. Memberikan penilaian noise berdasarkan
    dynamic range audio.
    
    Args:
        file_path: Path ke file audio.
    
    Returns:
        dict dengan kunci: rms_level_db, peak_level_db, dynamic_range_db,
        crest_factor_db, noise_assessment, assessment_reason
    """
    if not os.path.exists(file_path):
        return {"error": f"File tidak ditemukan: {file_path}"}
    
    ffmpeg = find_ffmpeg()
    
    cmd = [
        ffmpeg,
        "-i", file_path,
        "-af", "astats=metadata=1:reset=1",
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
        
        # Parse metrik astats keseluruhan dari stderr
        rms_match = re.search(r"RMS level dB:\s*([-\d.]+)", stderr)
        peak_match = re.search(r"Peak level dB:\s*([-\d.]+)", stderr)
        crest_match = re.search(r"Crest factor:\s*([-\d.]+)", stderr)
        
        rms_level = float(rms_match.group(1)) if rms_match else None
        peak_level = float(peak_match.group(1)) if peak_match else None
        crest_factor = float(crest_match.group(1)) if crest_match else None
        
        dynamic_range = None
        if peak_level is not None and rms_level is not None:
            dynamic_range = round(peak_level - rms_level, 2)
        
        noise_assessment = "unknown"
        assessment_reason = "Tidak dapat menentukan — data metrik tidak lengkap."
        
        if dynamic_range is not None:
            if dynamic_range > 20:
                noise_assessment = "clean"
                assessment_reason = (
                    f"Dynamic range {dynamic_range} dB menunjukkan audio memiliki "
                    f"dinamika yang baik dengan noise floor yang rendah."
                )
            elif dynamic_range >= 10:
                noise_assessment = "moderate_noise"
                assessment_reason = (
                    f"Dynamic range {dynamic_range} dB mengindikasikan adanya noise "
                    f"latar belakang, namun masih dalam batas yang dapat ditoleransi."
                )
            else:
                noise_assessment = "high_noise"
                assessment_reason = (
                    f"Dynamic range {dynamic_range} dB sangat rendah — audio terdengar "
                    f"flat, kemungkinan besar terdapat noise latar belakang yang signifikan."
                )
        
        return {
            "rms_level_db": round(rms_level, 2) if rms_level is not None else None,
            "peak_level_db": round(peak_level, 2) if peak_level is not None else None,
            "dynamic_range_db": dynamic_range,
            "crest_factor_db": round(crest_factor, 2) if crest_factor is not None else None,
            "noise_assessment": noise_assessment,
            "assessment_reason": assessment_reason
        }
        
    except subprocess.TimeoutExpired:
        return {"error": "ffmpeg timeout setelah 120 detik."}
    except FileNotFoundError:
        return {"error": "ffmpeg tidak ditemukan. Pastikan ffmpeg terinstal."}
