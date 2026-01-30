
import sys
import os
import logging
from pathlib import Path
from dotenv import load_dotenv

sys.path.append(str(Path(__file__).resolve().parent.parent))
load_dotenv()

from app.integrations.whisper_client import WhisperClient
from app.integrations.elevenlabs_client import ElevenLabsClient

logging.basicConfig(level=logging.INFO)

def test_voice():
    print("\n>>> TESTING VOICE SYSTEM <<<")
    
    # 0. Check API Key validity
    print("0. Verifying API Key (v1/voices)...")
    eleven = ElevenLabsClient.create_from_env()
    if not eleven:
        print("❌ SKIPPING: ELEVENLABS_API_KEY missing")
    else:
        voices = eleven.list_voices()
        if "error" not in voices:
            print(f"[OK] API Key Valid! Found {len(voices.get('voices', []))} voices.")
            if voices.get('voices'):
                print(f"   First voice: {voices['voices'][0]['name']} ({voices['voices'][0]['voice_id']})")
        else:
            print(f"[ERROR] API Key Invalid (401/403): {voices['error']}")
            return

    # 1. Test TTS
    print("\n1. Testing ElevenLabs TTS...")
    audio = eleven.synthesize("Hello! This is a test of the PresentOS voice system.")
    if audio:
        print(f"[OK] TTS Success! Received {len(audio)} bytes of audio.")
        # Save to temp file to verify
        with open("tts_test.mp3", "wb") as f:
            f.write(audio)
        print("   (Saved to tts_test.mp3)")
    else:
        print("[ERROR] TTS Failed.")

    # 2. Test STT
    print("\n2. Testing Whisper STT...")
    whisper = WhisperClient.create_from_env()
    if not whisper:
        print("❌ SKIPPING STT: OPENAI_API_KEY missing")
        print("SKIPPING STT: OPENAI_API_KEY missing")
    else:
        # We need an audio file to test. I'll use the one we just generated if it exists.
        if os.path.exists("tts_test.mp3"):
            print(f"   Transcribing tts_test.mp3...")
            text = whisper.transcribe("tts_test.mp3")
            if text:
                print(f"[OK] STT Success! Transcription: \"{text}\"")
            else:
                print("[ERROR] STT Failed.")
        else:
            print("Skipping STT test as no audio file was generated.")

if __name__ == "__main__":
    test_voice()
