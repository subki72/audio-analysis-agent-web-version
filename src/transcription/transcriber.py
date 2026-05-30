import os
from dotenv import load_dotenv
from groq import Groq

# Memastikan environment variables dimuat
load_dotenv()

class Transcriber:
    """Kelas untuk mengelola interaksi dengan cloud transcription API Groq."""
    
    def __init__(self, settings: dict = None):
        self.settings = settings or {}
        
        # Ambil konfigurasi API Groq
        api_settings = self.settings.get("api", {})
        self.api_key = os.getenv("GROQ_API_KEY")
        
        # Groq SDK default base_url adalah https://api.groq.com
        # Jika user mengonfigurasi dengan /openai/v1 di belakangnya, kita strip agar tidak double
        base_url = os.getenv("GROQ_BASE_URL")
        if base_url:
            if base_url.endswith("/openai/v1"):
                base_url = base_url[:-10]
            elif base_url.endswith("/openai/v1/"):
                base_url = base_url[:-11]
        
        self.model = api_settings.get("model", os.getenv("GROQ_MODEL", "whisper-large-v3"))
        
        self.client = None
        if self.api_key:
            if base_url:
                self.client = Groq(api_key=self.api_key, base_url=base_url)
            else:
                self.client = Groq(api_key=self.api_key)

    def transcribe_file(self, file_path: str, language: str = 'id', response_format: str = 'txt') -> str:
        """Kirim file audio ke Groq API untuk mendapatkan transkrip."""
        if not self.client:
            raise ValueError(
                "API Key untuk GROQ tidak ditemukan. "
                "Pastikan Anda telah mengonfigurasinya di file .env."
            )
        
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File audio tidak ditemukan: {file_path}")
            
        # Groq hanya menerima: 'json', 'text', 'verbose_json'
        api_format = 'text'
        if response_format == 'json':
            api_format = 'json'
        elif response_format in ['srt', 'vtt']:
            api_format = 'verbose_json'
            
        with open(file_path, "rb") as file:
            # Panggilan API Groq untuk transkripsi audio
            transcription = self.client.audio.transcriptions.create(
                file=(os.path.basename(file_path), file.read()),
                model=self.model,
                language=language,
                response_format=api_format
            )
            
            # Jika format output yang diminta adalah subtitle (srt/vtt)
            if response_format in ['srt', 'vtt']:
                # Dapatkan segments dari respons verbose_json
                segments = getattr(transcription, 'segments', [])
                if not segments and isinstance(transcription, dict):
                    segments = transcription.get('segments', [])
                
                from src.utils.helpers import json_to_srt, json_to_vtt
                if response_format == 'srt':
                    return json_to_srt(segments)
                else:
                    return json_to_vtt(segments)
            
            # Jika format default text
            if isinstance(transcription, str):
                return transcription
            return getattr(transcription, 'text', str(transcription))

    def save_output(self, content: str, output_path: str) -> None:
        """Menyimpan teks transkripsi ke file output."""
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(content)
