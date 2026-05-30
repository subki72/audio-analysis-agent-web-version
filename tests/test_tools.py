"""
Test integrasi untuk tools analisis audio berbasis ffmpeg.

Test dijalankan menggunakan file nyata data/bad_audio.mp3 dengan ffmpeg.
Dilewati otomatis jika ffmpeg tidak terinstal (misal di CI tanpa ffmpeg).
"""
import os
import pytest

from src.tools.metadata import get_audio_metadata
from src.tools.silence import detect_silence
from src.tools.volume import detect_clipping
from src.tools.noise import detect_noise


def _ffmpeg_available() -> bool:
    """Cek ketersediaan ffmpeg menggunakan finder bawaan proyek."""
    try:
        from src.tools.ffmpeg_finder import find_ffmpeg
        find_ffmpeg()
        return True
    except Exception:
        return False


# Decorator skip — semua test integrasi membutuhkan ffmpeg
requires_ffmpeg = pytest.mark.skipif(
    not _ffmpeg_available(),
    reason="ffmpeg not installed"
)

# Path ke file audio test (relatif terhadap root proyek)
AUDIO_FILE = os.path.join("data", "bad_audio.mp3")


# ---------------------------------------------------------------
# get_audio_metadata
# ---------------------------------------------------------------

@requires_ffmpeg
def test_metadata_returns_valid_data():
    result = get_audio_metadata(AUDIO_FILE)
    assert "error" not in result, f"Tool returned error: {result.get('error')}"
    assert result["duration_seconds"] > 0
    assert result["channels"] >= 1
    assert result["sample_rate"] > 0


def test_metadata_file_not_found():
    result = get_audio_metadata("file_yang_tidak_ada.mp3")
    assert "error" in result


# ---------------------------------------------------------------
# detect_silence
# ---------------------------------------------------------------

@requires_ffmpeg
def test_silence_detection_schema():
    result = detect_silence(AUDIO_FILE)
    assert "error" not in result, f"Tool returned error: {result.get('error')}"
    assert isinstance(result["silence_detected"], bool)
    assert 0.0 <= result["silence_ratio"] <= 1.0
    assert isinstance(result["silence_segments"], list)


def test_silence_file_not_found():
    result = detect_silence("file_yang_tidak_ada.mp3")
    assert "error" in result


# ---------------------------------------------------------------
# detect_clipping
# ---------------------------------------------------------------

@requires_ffmpeg
def test_clipping_detection_schema():
    result = detect_clipping(AUDIO_FILE)
    assert "error" not in result, f"Tool returned error: {result.get('error')}"
    assert isinstance(result["volume_clipping"], bool)
    assert result["clipping_severity"] in ("none", "warning", "moderate", "severe")
    assert "mean_volume_db" in result


# ---------------------------------------------------------------
# detect_noise
# ---------------------------------------------------------------

@requires_ffmpeg
def test_noise_detection_schema():
    result = detect_noise(AUDIO_FILE)
    assert "error" not in result, f"Tool returned error: {result.get('error')}"
    assert result["noise_assessment"] in ("clean", "moderate_noise", "high_noise", "unknown")
    assert "dynamic_range_db" in result
    if result["dynamic_range_db"] is not None:
        assert result["dynamic_range_db"] > 0
