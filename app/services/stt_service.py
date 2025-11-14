from gradio_client import Client
from ..config import settings
import time

def transcribe_audio(audio_file_path: str, language: str = "english") -> str:
    """
    Calls the deployed Hugging Face Spaces API to transcribe audio.
    This is a blocking, slow operation (can take 1-2 minutes).
    """
    print(f"STT: Connecting to Whisper API at {settings.HF_SPACE_URL}...")
    try:
        client = Client(settings.HF_SPACE_URL, verbose=False)
        
        start_time = time.time()
        print(f"STT: Transcribing {audio_file_path} (Language: {language}). This will be slow...")
        
        # This function must match the 'fn' in your Hugging Face Space's app.py
        # The order of arguments must be exact.
        result = client.predict(
            language,         # Arg 1: The language dropdown
            audio_file_path,  # Arg 2: The audio file
            api_name="/predict" 
        )
        
        end_time = time.time()
        print(f"STT: Transcription complete in {end_time - start_time:.2f} seconds.")
        
        if isinstance(result, str):
            return result
        else:
            # Handle potential tuple or other non-string results
            return str(result)
        
    except Exception as e:
        print(f"STT Error: {e}")
        return f"Error during transcription: {e}"