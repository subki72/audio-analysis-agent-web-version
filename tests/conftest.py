import warnings


def pytest_configure(config):
    """Menyembunyikan RuntimeWarning dari pydub tentang ffmpeg yang tidak ditemukan."""
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
