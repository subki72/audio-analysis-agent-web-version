import subprocess
import warnings
from pathlib import Path

from src.tools.ffmpeg_finder import find_ffmpeg


def _ensure_sample_audio_fixtures() -> None:
    """Generate lightweight sample MP3 fixtures via ffmpeg if absent in CI."""
    ffmpeg_bin = find_ffmpeg()
    if not ffmpeg_bin:
        return
    data_dir = Path("data")
    data_dir.mkdir(parents=True, exist_ok=True)
    for name in ("bad_audio.mp3", "moonlight-plaza.mp3"):
        target = data_dir / name
        if not target.exists():
            subprocess.run(
                [
                    ffmpeg_bin,
                    "-y",
                    "-f",
                    "lavfi",
                    "-i",
                    "sine=frequency=440:duration=2",
                    "-ar",
                    "44100",
                    "-ac",
                    "1",
                    str(target),
                ],
                capture_output=True,
                check=False,
            )


def pytest_configure(config):
    """Configure test warnings and ensure synthetic audio fixtures exist."""
    warnings.filterwarnings(
        "ignore",
        message="Couldn't find ffmpeg or avconv",
        category=RuntimeWarning,
    )
    warnings.filterwarnings(
        "ignore",
        message="Couldn't find ffprobe or avprobe",
        category=RuntimeWarning,
    )
    _ensure_sample_audio_fixtures()
