"""Unit tests for Pydantic v2 validation schemas."""

import pytest
from pydantic import ValidationError

from src.schemas import AudioAnalysisRequest, AudioQualityMetrics, HealthStatusResponse


def test_audio_analysis_request_valid() -> None:
    """Accepts valid filename and default cache configuration."""
    req = AudioAnalysisRequest(filename="deposition_01.mp3")
    assert req.filename == "deposition_01.mp3"
    assert req.use_cache is True


def test_audio_analysis_request_rejects_empty_filename() -> None:
    """Rejects empty filename strings."""
    with pytest.raises(ValidationError):
        AudioAnalysisRequest(filename="")


def test_audio_quality_metrics_bounds() -> None:
    """Validates silence_ratio stays within [0.0, 1.0]."""
    metrics = AudioQualityMetrics(silence_ratio=0.15, clipping_detected=False, avg_volume_db=-18.5)
    assert metrics.clipping_detected is False
    with pytest.raises(ValidationError):
        AudioQualityMetrics(silence_ratio=1.5, clipping_detected=True, avg_volume_db=-5.0)


def test_health_status_response_defaults() -> None:
    """Verifies HealthStatusResponse default contract."""
    resp = HealthStatusResponse(supported_formats=[".mp3", ".wav"])
    assert resp.status == "ok"
    assert ".mp3" in resp.supported_formats
