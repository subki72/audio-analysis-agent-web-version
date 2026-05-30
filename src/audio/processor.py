import os
from pydub import AudioSegment

class AudioProcessor:
    """Kelas untuk menangani pemrosesan audio lokal seperti konversi, pemisahan file besar, dll."""
    
    def __init__(self, settings: dict = None):
        self.settings = settings or {}

    def get_metadata(self, file_path: str) -> dict:
        """Mengembalikan metadata file audio seperti durasi, format, dan ukuran."""
        try:
            audio = AudioSegment.from_file(file_path)
            duration_seconds = len(audio) / 1000.0
        except Exception:
            duration_seconds = 0.0

        return {
            "path": file_path,
            "size_bytes": os.path.getsize(file_path),
            "duration_seconds": duration_seconds,
            "format": os.path.splitext(file_path)[1][1:]
        }

    def convert_format(self, file_path: str, target_format: str) -> str:
        """Mengonversi file audio ke format target (misalnya mp3)."""
        audio = AudioSegment.from_file(file_path)
        base, _ = os.path.splitext(file_path)
        output_path = f"{base}.{target_format}"
        audio.export(output_path, format=target_format)
        return output_path

    def split_audio(self, file_path: str, max_size_mb: int = 25) -> list:
        """Membagi file audio menjadi beberapa segmen jika ukurannya melebihi batas (misal 25MB)."""
        file_size_mb = os.path.getsize(file_path) / (1024 * 1024)
        if file_size_mb <= max_size_mb:
            return [file_path]

        # Jika melebihi limit, potong audio per chunk_duration
        chunk_duration_sec = self.settings.get('audio', {}).get('chunk_duration_seconds', 600)
        chunk_duration_ms = chunk_duration_sec * 1000
        target_format = self.settings.get('audio', {}).get('target_format', 'mp3')
        
        audio = AudioSegment.from_file(file_path)
        chunks = []
        
        base, _ = os.path.splitext(file_path)
        
        # Pydub split
        for i in range(0, len(audio), chunk_duration_ms):
            part_num = (i // chunk_duration_ms) + 1
            chunk = audio[i:i + chunk_duration_ms]
            chunk_path = f"{base}_part{part_num}.{target_format}"
            chunk.export(chunk_path, format=target_format)
            chunks.append(chunk_path)
            
        return chunks
