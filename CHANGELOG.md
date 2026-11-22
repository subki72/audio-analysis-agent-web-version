# Changelog

All notable changes to **audio-analysis-agent-web-version (VoiceScript)** will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2026-11-22

### Added
- Pydantic v2 request/response schemas and sliding-window `RateLimiter` (`src/schemas.py`), integrated into `web_api.py`.
- 4 new unit test suites (`tests/test_schemas.py`, `tests/test_rate_limiter.py`, `tests/test_web_api.py`, `tests/test_orchestrator_unit.py`).
- GitHub Actions CI pipeline (`.github/workflows/ci.yml`) executing Ruff lint, Pytest, Docker build, Semgrep SAST, and Trivy scanning.
- Pinned dependencies in `requirements.txt`, `requirements-lock.txt`, `uv.lock`, and `ruff.toml`.
- Single-command `Makefile`, `docker-compose.yml`, `.github/dependabot.yml`, `SECURITY.md`, `runbook.md`, `LICENSE`, `CONTRIBUTING.md`, and `.pre-commit-config.yaml`.

### Changed
- Added structured leveled logging to `src/agent/orchestrator.py`.
