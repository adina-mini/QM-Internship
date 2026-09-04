import os
from dotenv import load_dotenv
from elevenlabs.client import ElevenLabs

load_dotenv()

client = ElevenLabs(api_key=os.environ.get("ELEVENLABS_API_KEY"))

voices = client.voices.get_all()

for v in voices.voices:
    print(v.voice_id, "-", v.name)
