"""ElevenLabs-TTS für die Social-Video-Pipeline (DE/EN-Brand-Voice).

Key kommt aus der `.env` (ELEVENLABS_API_KEY) — NIE committen (.env ist gitignored).
Stimme via ELEVENLABS_VOICE_ID_DE / ELEVENLABS_VOICE_ID_EN (Fallback ELEVENLABS_VOICE_ID),
sonst eine stabile Premade-Stimme. Modell: eleven_multilingual_v2 (kann Deutsch).

  py -3.14 scripts/video/tts.py --list                         # verfügbare Stimmen anzeigen
  py -3.14 scripts/video/tts.py --text "Hallo" --lang de --out test.mp3
"""
from __future__ import annotations
import argparse
import os
import sys
from pathlib import Path

import requests

_PROJECT_DIR = Path(__file__).resolve().parent.parent.parent
_API = "https://api.elevenlabs.io/v1"
# Stabile Premade-Stimmen (multilingual_v2 spricht damit auch Deutsch). Per .env überschreibbar.
_DEFAULT_VOICE = "pNInz6obpgDQGcFmaJgB"  # "Adam" (männlich, Narration); native DE-Stimme via ELEVENLABS_VOICE_ID_DE in .env
_MODEL = "eleven_multilingual_v2"


def load_env():
    """Liest project-root/.env in os.environ (ohne bestehende Werte zu überschreiben)."""
    env = _PROJECT_DIR / ".env"
    if not env.exists():
        return
    for line in env.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


def get_key() -> str:
    load_env()
    key = os.environ.get("ELEVENLABS_API_KEY")
    if not key:
        sys.exit("[tts] FEHLER: ELEVENLABS_API_KEY fehlt. In c:/dev/SeasonalEdge/.env eintragen.")
    return key


def voice_for(lang: str) -> str:
    load_env()
    return (os.environ.get(f"ELEVENLABS_VOICE_ID_{lang.upper()}")
            or os.environ.get("ELEVENLABS_VOICE_ID")
            or _DEFAULT_VOICE)


def list_voices():
    r = requests.get(f"{_API}/voices", headers={"xi-api-key": get_key()}, timeout=30)
    r.raise_for_status()
    for v in r.json().get("voices", []):
        labels = v.get("labels", {})
        print(f"  {v['voice_id']}  {v.get('name','?'):16} "
              f"{labels.get('language','?')}/{labels.get('accent','?')} "
              f"{labels.get('gender','?')} {labels.get('description','')}")


def synth(text: str, out_path: Path, lang: str = "de", voice_id: str | None = None) -> Path:
    """Erzeugt MP3 aus Text. Returns out_path."""
    vid = voice_id or voice_for(lang)
    url = f"{_API}/text-to-speech/{vid}"
    body = {
        "text": text,
        "model_id": _MODEL,
        "voice_settings": {"stability": 0.45, "similarity_boost": 0.75,
                           "style": 0.0, "use_speaker_boost": True},
    }
    r = requests.post(url, headers={"xi-api-key": get_key(), "accept": "audio/mpeg",
                                    "content-type": "application/json"},
                      json=body, params={"output_format": "mp3_44100_128"}, timeout=120)
    if r.status_code != 200:
        sys.exit(f"[tts] ElevenLabs {r.status_code}: {r.text[:300]}")
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_bytes(r.content)
    return out_path


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--list", action="store_true", help="Verfügbare Stimmen auflisten")
    ap.add_argument("--text")
    ap.add_argument("--textfile")
    ap.add_argument("--lang", default="de", choices=["de", "en"])
    ap.add_argument("--voice")
    ap.add_argument("--out", default="scripts/video/out/tts_test.mp3")
    a = ap.parse_args()
    if a.list:
        list_voices(); return
    text = a.text or (Path(a.textfile).read_text(encoding="utf-8") if a.textfile else None)
    if not text:
        sys.exit("[tts] --text oder --textfile nötig (oder --list).")
    p = synth(text, Path(a.out), a.lang, a.voice)
    print(f"[tts] OK ({voice_for(a.lang)}) -> {p}")


if __name__ == "__main__":
    main()
