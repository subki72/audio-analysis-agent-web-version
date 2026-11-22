# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 1.0.x   | :white_check_mark: |
| < 1.0   | :x:                |

## Reporting a Vulnerability

If you discover a security vulnerability in **VoiceScript (Audio Analysis Agent)**:

1. **Do NOT open a public GitHub issue** for undisclosed vulnerabilities.
2. Submit a private report via GitHub Security Advisories (`Security -> Advisories -> Report a vulnerability`).
3. Provide affected endpoints, reproduction steps, and severity impact.

## Security Controls

- **Upload Sanitization & TTL**: Only allow-listed audio extensions are saved with randomized UUID filenames; uploaded files expire automatically after 30 minutes.
- **Pydantic Validation & Rate Limiting**: Request contracts enforced via Pydantic v2 (`src/schemas.py`) with sliding-window IP throttling (`RateLimiter`).
- **Automated Scanning**: Dependabot weekly alerts, Semgrep SAST, and Trivy Docker scanning run in CI.
