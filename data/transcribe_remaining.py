#!/usr/bin/env python3
import os
import glob
import subprocess
from pathlib import Path

AUDIO_DIR = Path("/root/.openclaw/workspace/research/podcasts/2026-03/audio")
TRANSCRIPT_DIR = Path("/root/.openclaw/workspace/research/podcasts/2026-03/transcripts")

# Find remaining MP3s
mp3_files = sorted(glob.glob(str(AUDIO_DIR / "*.mp3")))
remaining = []

for mp3 in mp3_files:
    mp3_path = Path(mp3)
    transcript_file = TRANSCRIPT_DIR / f"{mp3_path.stem}.txt"
    if not transcript_file.exists():
        remaining.append(mp3_path)

print(f"🎙️ {len(remaining)} Episoden noch zu transkribieren")
print()

for i, mp3_file in enumerate(remaining, 1):
    print(f"[{i}/{len(remaining)}] Transkribiere: {mp3_file.name}")
    print(f"      Größe: {mp3_file.stat().st_size / 1024 / 1024:.1f} MB")
    
    try:
        result = subprocess.run(
            ["whisper", str(mp3_file), "--model", "base", "--language", "en", 
             "--output_format", "txt", "--output_dir", str(TRANSCRIPT_DIR)],
            capture_output=True,
            text=True,
            timeout=1800  # 30 Min pro Episode
        )
        
        if result.returncode == 0:
            print(f"      ✅ Fertig!")
        else:
            print(f"      ❌ Fehler: {result.stderr[:100]}")
    except Exception as e:
        print(f"      ❌ Exception: {str(e)[:100]}")
    print()

print("🎉 Batch complete!")
