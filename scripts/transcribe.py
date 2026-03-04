#!/usr/bin/env python3
import sys
import os
import whisper
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()
model_name = os.getenv("WHISPER_MODEL", "base")  # base|small|medium|large


def transcribe_audio(in_path: Path, out_path: Path):
    model = whisper.load_model(model_name)
    result = model.transcribe(str(in_path))
    out_path.write_text(result["text"], encoding="utf-8")
    print(f"✔️  Transcribed {in_path.name} → {out_path.name}")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: transcribe.py <audio_file> <output_txt>")
        sys.exit(1)

    audio_file = Path(sys.argv[1])
    output_txt = Path(sys.argv[2])

    if not audio_file.is_file():
        print(f"❌  Audio file not found: {audio_file}")
        sys.exit(1)

    transcribe_audio(audio_file, output_txt)
