import pytest
from unittest.mock import patch
from src.transcription.transcriber import Transcriber


def test_transcriber_no_api_key():
    """Transcriber harus bisa diinisialisasi tanpa API key (client = None).
    
    Ketika GROQ_API_KEY tidak ada di environment, Transcriber tetap
    terbentuk tapi `client` harus None agar tidak crash saat import.
    """
    with patch.dict('os.environ', {}, clear=True):
        import os
        os.environ.pop('GROQ_API_KEY', None)
        transcriber = Transcriber(settings={})
        assert transcriber.api_key is None
        assert transcriber.client is None


def test_transcriber_with_api_key():
    """Transcriber harus membuat Groq client jika API key tersedia.
    
    Ketika GROQ_API_KEY di-set di environment, Transcriber harus:
    - Menyimpan api_key dari env var
    - Membuat Groq client (bukan None)
    """
    with patch.dict('os.environ', {'GROQ_API_KEY': 'gsk_test_key_123'}):
        transcriber = Transcriber(settings={})
        assert transcriber.api_key == 'gsk_test_key_123'
        assert transcriber.client is not None


def test_transcriber_default_model():
    """Model default harus whisper-large-v3 jika tidak dikonfigurasi.
    
    Jika settings dict kosong dan GROQ_MODEL env var tidak ada,
    fallback ke 'whisper-large-v3'.
    """
    with patch.dict('os.environ', {'GROQ_API_KEY': 'gsk_test_key_123'}, clear=True):
        transcriber = Transcriber(settings={})
        assert transcriber.model == 'whisper-large-v3'


def test_transcriber_model_from_settings():
    """Model harus bisa dikonfigurasi lewat settings dict.
    
    Jika settings['api']['model'] di-set, itu harus diprioritaskan
    di atas default 'whisper-large-v3'.
    """
    with patch.dict('os.environ', {'GROQ_API_KEY': 'gsk_test_key_123'}):
        settings = {'api': {'model': 'whisper-large-v3-turbo'}}
        transcriber = Transcriber(settings=settings)
        assert transcriber.model == 'whisper-large-v3-turbo'
