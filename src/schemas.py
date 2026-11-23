"""
Pydantic v2 validation schemas and sliding-window rate limiter for VoiceScript API.
"""

import time
from collections import defaultdict
from typing import Dict, List, Optional

from pydantic import BaseModel, Field


class AudioAnalysisRequest(BaseModel):
    """Validated parameters for audio analysis requests."""

    filename: str = Field(..., min_length=1, max_length=255)
    use_cache: bool = Field(default=True, description="Enable MD5 file-hash response caching")
    language: Optional[str] = Field(default=None, max_length=16, description="Optional ISO language code")


class AudioQualityMetrics(BaseModel):
    """Normalized audio quality metrics produced by ffmpeg tools."""

    silence_ratio: float = Field(..., ge=0.0, le=1.0)
    clipping_detected: bool
    avg_volume_db: float


class HealthStatusResponse(BaseModel):
    """Standardized liveness & configuration health response."""

    status: str = Field(default="ok")
    service: str = Field(default="voicescript-api")
    version: str = Field(default="1.0.0")
    supported_formats: List[str] = Field(default_factory=list)


class RateLimiter:
    """In-memory sliding-window IP rate limiter for API protection."""

    def __init__(self, max_requests: int = 30, window_seconds: int = 60) -> None:
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._hits: Dict[str, List[float]] = defaultdict(list)

    def allow(self, client_id: str) -> bool:
        """Return True if client is within rate limit window, else False."""
        now = time.monotonic()
        cutoff = now - self.window_seconds
        recent = [ts for ts in self._hits[client_id] if ts >= cutoff]
        if len(recent) >= self.max_requests:
            self._hits[client_id] = recent
            return False
        recent.append(now)
        self._hits[client_id] = recent
        return True
