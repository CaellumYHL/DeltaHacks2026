import os
from elevenlabs import ElevenLabs

def elevenlabs_tts_bytes(
    text: str,
    voice_id: str = "JBFqnCBsd6RMkjVDRZzb",
    model_id: str = "eleven_multilingual_v2",
    output_format: str = "mp3_44100_128",
) -> bytes:
    api_key = os.getenv("ELEVENLABS_API_KEY")
    if not api_key:
        raise RuntimeError("Missing ELEVENLABS_API_KEY in .env")

    text = (text or "").strip()
    if not text:
        raise ValueError("No text to speak.")
    if len(text) > 2500:
        text = text[:2500] + "..."

    client = ElevenLabs(api_key=api_key)
    audio_stream = client.text_to_speech.convert(
        voice_id=voice_id,
        text=text,
        model_id=model_id,
        output_format=output_format,
    )
    return b"".join(audio_stream)
