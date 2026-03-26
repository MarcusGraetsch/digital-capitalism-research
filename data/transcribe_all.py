#!/usr/bin/env python3
import os
import glob
import subprocess
from pathlib import Path

RESEARCH_DIR = Path("/root/.openclaw/workspace/research")
AUDIO_DIR = RESEARCH_DIR / "podcasts" / "2026-03" / "audio"
TRANSCRIPT_DIR = RESEARCH_DIR / "podcasts" / "2026-03" / "transcripts"

# Verzeichnisse erstellen
TRANSCRIPT_DIR.mkdir(parents=True, exist_ok=True)

# Alle MP3s finden (rekursiv in allen Unterverzeichnissen)
mp3_files = sorted(glob.glob(str(AUDIO_DIR / "**" / "*.mp3"), recursive=True))

print(f"🎙️ Starte Transkription von {len(mp3_files)} Episoden...")
print(f"   Audio: {AUDIO_DIR}")
print(f"   Transkripte: {TRANSCRIPT_DIR}")
print()

for i, mp3_path in enumerate(mp3_files, 1):
    mp3_file = Path(mp3_path)
    transcript_file = TRANSCRIPT_DIR / f"{mp3_file.stem}.txt"
    
    if transcript_file.exists():
        print(f"[{i}/{len(mp3_files)}] ⏭️  Bereits transkribiert: {mp3_file.name}")
        continue
    
    print(f"[{i}/{len(mp3_files)}] 🎯 Transkribiere: {mp3_file.name}")
    print(f"      Größe: {mp3_file.stat().st_size / 1024 / 1024:.1f} MB")
    
    try:
        result = subprocess.run(
            ["whisper", str(mp3_file), "--model", "base", "--language", "en", "--output_format", "txt", "--output_dir", str(TRANSCRIPT_DIR)],
            capture_output=True,
            text=True,
            timeout=3600
        )
        
        if result.returncode == 0:
            print(f"      ✅ Fertig!")
        else:
            print(f"      ❌ Fehler: {result.stderr[:200]}")
    except Exception as e:
        print(f"      ❌ Exception: {str(e)[:200]}")
    
    print()

print("🎉 Alle Transkriptionen abgeschlossen!")
