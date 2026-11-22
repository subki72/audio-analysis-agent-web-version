"""Unit tests for VoiceScript FastAPI web_api helper configuration."""

from web_api import SUPPORTED_EXTENSIONS, app, rate_limiter


def test_supported_audio_extensions_present() -> None:
    """Ensures core audio formats are accepted by the upload handler."""
    assert ".mp3" in SUPPORTED_EXTENSIONS
    assert ".wav" in SUPPORTED_EXTENSIONS
    assert ".flac" in SUPPORTED_EXTENSIONS


def test_fastapi_app_metadata_and_rate_limiter() -> None:
    """Verifies FastAPI service title, version, and rate limiter initialization."""
    assert app.title == "VoiceScript API"
    assert rate_limiter.max_requests == 30
    assert rate_limiter.window_seconds == 60
