"""
MCP Server untuk Audio Analysis Agent.
Meng-expose 4 tools ffmpeg via FastMCP (Model Context Protocol).

Jalankan: python mcp_server.py
"""
from mcp.server.fastmcp import FastMCP

from src.tools.metadata import get_audio_metadata
from src.tools.silence import detect_silence
from src.tools.volume import detect_clipping
from src.tools.noise import detect_noise

mcp = FastMCP(
    "Audio Analysis Agent",
    instructions="MCP server yang menyediakan tools analisis kualitas audio menggunakan ffmpeg/ffprobe."
)


@mcp.tool()
def get_audio_metadata_tool(file_path: str) -> dict:
    """Mengambil metadata dari file audio menggunakan ffprobe.
    
    Mengembalikan informasi format, durasi, sample rate, channels, codec, dan bitrate.
    
    Args:
        file_path: Path absolut atau relatif ke file audio yang akan dianalisis.
    """
    return get_audio_metadata(file_path)


@mcp.tool()
def detect_silence_tool(file_path: str) -> dict:
    """Mendeteksi segmen keheningan (silence) dalam file audio menggunakan ffmpeg silencedetect.
    
    Mengembalikan daftar segmen hening beserta durasi totalnya dan silence ratio.
    
    Args:
        file_path: Path absolut atau relatif ke file audio yang akan dianalisis.
    """
    return detect_silence(file_path)


@mcp.tool()
def detect_clipping_tool(file_path: str) -> dict:
    """Mengukur level volume dan mendeteksi clipping pada file audio menggunakan ffmpeg volumedetect.
    
    Mengembalikan mean volume, max volume, status clipping, dan severity level.
    
    Args:
        file_path: Path absolut atau relatif ke file audio yang akan dianalisis.
    """
    return detect_clipping(file_path)


@mcp.tool()
def detect_noise_tool(file_path: str) -> dict:
    """Menganalisis noise level dan dynamic range audio menggunakan ffmpeg astats.

    Mengembalikan RMS level, peak level, dynamic range, crest factor,
    dan penilaian noise secara keseluruhan.

    Args:
        file_path: Path absolut atau relatif ke file audio yang akan dianalisis.
    """
    return detect_noise(file_path)


if __name__ == "__main__":
    mcp.run()
