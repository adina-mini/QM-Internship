import os
from dotenv import load_dotenv
from deepgram import DeepgramClient

load_dotenv()

client = DeepgramClient(api_key=os.environ.get("DEEPGRAM_API_KEY"))

response = client.speak.v1.audio.generate(
    text="Hello, this is a test of the QM Logics voice assistant."
)

with open("test_output_deepgram.mp3", "wb") as f:
    for chunk in response:
        f.write(chunk)

print("Success — check test_output_deepgram.mp3")
