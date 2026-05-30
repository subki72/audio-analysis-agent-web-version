"""
Utilitas untuk menemukan binary ffmpeg dan ffprobe di sistem.
Mencari di PATH, lalu di lokasi umum Conda environments.
"""
import os
import shutil
import glob
import sys


def _find_in_conda(binary_name: str) -> str | None:
    """Cari binary di dalam conda environments yang umum."""
    home = os.path.expanduser("~")
    
    conda_paths = [
        # Miniconda / Anaconda default
        os.path.join(home, "miniconda3", "envs", "voicescript", "Library", "bin"),
        os.path.join(home, "anaconda3", "envs", "voicescript", "Library", "bin"),
        os.path.join(home, "Miniconda3", "envs", "voicescript", "Library", "bin"),
        os.path.join(home, "Anaconda3", "envs", "voicescript", "Library", "bin"),
        os.path.join(os.getenv("CONDA_PREFIX", ""), "Library", "bin"),
    ]
    
    for p in conda_paths:
        candidate = os.path.join(p, binary_name)
        if os.path.isfile(candidate):
            return candidate
    
    # Brute-force: cari di semua conda envs
    for base in [os.path.join(home, "miniconda3"), os.path.join(home, "anaconda3"),
                 os.path.join(home, "Miniconda3"), os.path.join(home, "Anaconda3")]:
        pattern = os.path.join(base, "envs", "*", "Library", "bin", binary_name)
        matches = glob.glob(pattern)
        if matches:
            return matches[0]
    
    return None


def find_ffmpeg() -> str:
    """Mengembalikan path ke binary ffmpeg."""
    exe = "ffmpeg.exe" if sys.platform == "win32" else "ffmpeg"
    
    path = shutil.which("ffmpeg")
    if path:
        return path
    
    path = _find_in_conda(exe)
    if path:
        return path
    
    raise FileNotFoundError(
        "ffmpeg tidak ditemukan. Pastikan ffmpeg terinstal dan ada di PATH, "
        "atau aktifkan conda environment 'voicescript' terlebih dahulu:\n"
        "  conda activate voicescript"
    )


def find_ffprobe() -> str:
    """Mengembalikan path ke binary ffprobe."""
    exe = "ffprobe.exe" if sys.platform == "win32" else "ffprobe"
    
    path = shutil.which("ffprobe")
    if path:
        return path
    
    path = _find_in_conda(exe)
    if path:
        return path
    
    raise FileNotFoundError(
        "ffprobe tidak ditemukan. Pastikan ffprobe terinstal dan ada di PATH, "
        "atau aktifkan conda environment 'voicescript' terlebih dahulu:\n"
        "  conda activate voicescript"
    )
