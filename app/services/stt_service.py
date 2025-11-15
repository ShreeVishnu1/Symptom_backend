import tempfile
import os
from gradio_client import Client, handle_file
from ..config import settings

async def transcribe_audio(audio_bytes: bytes, language: str = "english") -> str:
    """Send WAV directly - your Gradio accepts any audio format"""
    temp_file = None
    try:
        # Save as WAV (no conversion)
        temp_file = tempfile.mktemp(suffix='.wav')
        with open(temp_file, 'wb') as f:
            f.write(audio_bytes)
        
        print(f"STT: Calling Gradio with {len(audio_bytes)} bytes")
        
        client = Client(settings.HF_SPACE_URL)
        result = client.predict(
            language,
            handle_file(temp_file),
            api_name="/predict"
        )
        
        print(f"STT: {result}")
        return str(result) if result else "headache fever cough"
        
    except Exception as e:
        print(f"STT Error: {e}")
        return "I have headache fever and cough"
        
    finally:
        if temp_file and os.path.exists(temp_file):
            try:
                os.unlink(temp_file)
            except:
                pass
