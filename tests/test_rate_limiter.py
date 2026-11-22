"""Unit tests for in-memory sliding-window RateLimiter."""

from src.schemas import RateLimiter


def test_rate_limiter_allows_within_quota() -> None:
    """Allows consecutive requests up to max_requests."""
    limiter = RateLimiter(max_requests=3, window_seconds=60)
    assert limiter.allow("127.0.0.1") is True
    assert limiter.allow("127.0.0.1") is True
    assert limiter.allow("127.0.0.1") is True
    assert limiter.allow("127.0.0.1") is False


def test_rate_limiter_isolates_clients() -> None:
    """Tracks rate quotas independently per client identifier."""
    limiter = RateLimiter(max_requests=1, window_seconds=60)
    assert limiter.allow("client-a") is True
    assert limiter.allow("client-a") is False
    assert limiter.allow("client-b") is True
