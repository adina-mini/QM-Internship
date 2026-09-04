import os
from dotenv import load_dotenv
from elevenlabs.client import ElevenLabs

load_dotenv()

client = ElevenLabs(api_key=os.environ.get("ELEVENLABS_API_KEY"))

audio = client.text_to_speech.convert(
    text="Hello, this is a test.",
    voice_id="21m00Tcm4TlvDq8ikWAM",
    model_id="eleven_flash_v2_5",
)

with open("test_output.mp3", "wb") as f:
    for chunk in audio:
        f.write(chunk)

print("Success — check test_output.mp3")
