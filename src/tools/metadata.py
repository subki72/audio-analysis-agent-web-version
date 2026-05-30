"""
Tool: get_audio_metadata
Mengambil metadata file audio menggunakan ffprobe.
Command: ffprobe -v quiet -print_format json -show_format -show_streams <file>
"""
import json
import subprocess
import os
from src.tools.ffmpeg_finder import find_ffprobe
from src.tools.registry import register_tool


@register_tool
def get_audio_metadata(file_path: str) -> dict:
    """
    Mengambil metadata dari file audio menggunakan ffprobe.
    
    Returns:
        dict dengan kunci: filename, format, size_bytes, duration_seconds,
        sample_rate, channels, codec, bitrate
    """
    if not os.path.exists(file_path):
        return {"error": f"File tidak ditemukan: {file_path}"}
    
    ffprobe = find_ffprobe()
    
    cmd = [
        ffprobe,
        "-v", "quiet",
        "-print_format", "json",
        "-show_format",
        "-show_streams",
        file_path
    ]
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode != 0:
            return {"error": f"ffprobe gagal: {result.stderr.strip()}"}
        
        probe_data = json.loads(result.stdout)
        
        fmt = probe_data.get("format", {})
        
        audio_stream = None
        for stream in probe_data.get("streams", []):
            if stream.get("codec_type") == "audio":
                audio_stream = stream
                break
        
        metadata = {
            "filename": os.path.basename(file_path),
            "format": fmt.get("format_name", "unknown"),
            "format_long_name": fmt.get("format_long_name", "unknown"),
            "size_bytes": int(fmt.get("size", 0)),
            "duration_seconds": float(fmt.get("duration", 0.0)),
            "bitrate": int(fmt.get("bit_rate", 0)),
        }
        
        if audio_stream:
            metadata.update({
                "codec": audio_stream.get("codec_name", "unknown"),
                "codec_long_name": audio_stream.get("codec_long_name", "unknown"),
                "sample_rate": int(audio_stream.get("sample_rate", 0)),
                "channels": int(audio_stream.get("channels", 0)),
                "channel_layout": audio_stream.get("channel_layout", "unknown"),
            })
        else:
            metadata.update({
                "codec": "unknown",
                "sample_rate": 0,
                "channels": 0,
            })
        
        return metadata
        
    except subprocess.TimeoutExpired:
        return {"error": "ffprobe timeout setelah 30 detik."}
    except json.JSONDecodeError as e:
        return {"error": f"Gagal parsing output ffprobe: {e}"}
    except FileNotFoundError:
        return {"error": "ffprobe tidak ditemukan. Pastikan ffmpeg terinstal."}
