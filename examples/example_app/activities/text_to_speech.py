from temporalio import activity
from gtts import gTTS
import os

@activity.defn
async def text_to_speech(text: str, response_text: str, user_id: str) -> str:
    """Convert text to speech and save as an audio file.
    
    Args:
        text: Text to convert to speech
        
    Returns:
        str: Path to the saved audio file
    """
    try:
        print(f"Activity: Converting text to speech: {text}")
        tts = gTTS(text)
        os.makedirs("audio", exist_ok=True)
        audio_path = os.path.join("audio", "audio_"+user_id+".mp3")
        tts.save(audio_path)
        print(f"Activity: Saved audio to {audio_path}")
        return {
            "audio_path": audio_path,
            "response": response_text,
            "user_id": user_id
        }
    except Exception as e:
        print(f"Activity Error: {str(e)}")
        raise 