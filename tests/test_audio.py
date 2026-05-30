import pytest
from src.audio.processor import AudioProcessor

def test_audio_metadata():
    processor = AudioProcessor()
    # Test dasar untuk validasi metadata
    meta = processor.get_metadata("data/bad_audio.mp3")
    assert meta["path"] == "data/bad_audio.mp3"
    assert "size_bytes" in meta
