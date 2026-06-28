"""Compose: Skript-JSON + Echtdaten-Chart + ElevenLabs-TTS -> fertiger 9:16-Short.

Pipeline:
  shorts-skripter-JSON (scripts/video/scripts/<slug>.json)
    -> TTS je Beat (ElevenLabs)  -> Timeline
    -> Chart-Clip (render_vertical_chart --video-mode, Dauer = VO-Länge)
    -> eingebrannte Untertitel (Beat-onscreen) + Disclaimer-Einblender + Branding (ASS)
    -> ffmpeg-Mux -> out/<slug>_<lang>.mp4

  py -3.14 scripts/video/compose.py --script scripts/video/scripts/dax-q4.json --lang de

Voraussetzung: ELEVENLABS_API_KEY in .env (siehe tts.py). ffmpeg/ffprobe auf PATH.
"""
from __future__ import annotations
import argparse
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE.parent.parent))
from scripts.video import tts  # noqa: E402

GAP = 0.5           # Pause zwischen Beats (s)
ANIM = 5.5          # Chart-Animationsdauer (s), danach Standbild
TAIL = 0.5          # Video etwas länger als Audio, -shortest trimmt
FPS = 30


def _dur(path: Path) -> float:
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                        "-of", "default=nokey=1:noprint_wrappers=1", str(path)],
                       capture_output=True, text=True)
    return float(r.stdout.strip())


def _ass_t(sec: float) -> str:
    cs = int(round(sec * 100))
    h, cs = divmod(cs, 360000)
    m, cs = divmod(cs, 6000)
    s, cs = divmod(cs, 100)
    return f"{h}:{m:02d}:{s:02d}.{cs:02d}"


def _ass(events, total, lang):
    """ASS-Datei: Beat-Untertitel + Disclaimer-Einblender + Dauer-Branding/Disclaimer."""
    foot = ("seasonalpha.ai  ·  keine Anlageberatung" if lang == "de"
            else "seasonalpha.ai  ·  not investment advice")
    head = (
        "[Script Info]\nScriptType: v4.00+\nPlayResX: 1080\nPlayResY: 1920\nWrapStyle: 0\n\n"
        "[V4+ Styles]\n"
        "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, "
        "BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, "
        "BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding\n"
        # weiß, fett, kräftiger Rand — große Keyword-Caption (hoch im freien Band)
        "Style: Cap,Arial,58,&H00FFFFFF,&H00FFFFFF,&H00000000,&H64000000,-1,0,0,0,100,100,0,0,1,5,1,2,70,70,250,1\n"
        # Gold — Disclaimer-Einblender (Standard-Variante, ggf. 2 Zeilen)
        "Style: Disc,Arial,34,&H0025A4E8,&H0025A4E8,&H00000000,&H64000000,-1,0,0,0,100,100,0,0,1,4,0,2,70,70,126,1\n"
        # gedämpft — Dauer-Branding + Disclaimer (ganz unten)
        "Style: Foot,Arial,28,&H00857060,&H00857060,&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,3,0,2,40,40,30,1\n\n"
        "[Events]\nFormat: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n"
    )
    lines = [head]

    def ev(style, start, end, text):
        text = text.replace("\n", r"\N")
        lines.append(f"Dialogue: 0,{_ass_t(start)},{_ass_t(end)},{style},,0,0,0,,{text}")

    # Dauer-Branding/Disclaimer (ganzes Video)
    ev("Foot", 0, total, foot)
    # Disclaimer-Einblender (Pflicht) — STANDARD-Variante aus dem Skript (Teil 3, docs/YOUTUBE_DISCLAIMER.md)
    ev("Disc", 0.2, 4.3, events["disclaimer_overlay"])
    # Beat-Untertitel (Keyword je Sprech-Fenster)
    for (start, end, txt) in events["beats"]:
        ev("Cap", start, end, txt)
    return "\n".join(lines) + "\n"


_CATALOG = _HERE / "catalog.json"


def _assign_number(slug, topic="", ticker="", chart=""):
    """Laufnummer aus catalog.json holen (oder neu vergeben + eintragen)."""
    cat = json.loads(_CATALOG.read_text(encoding="utf-8")) if _CATALOG.exists() else []
    for e in cat:
        if e.get("slug") == slug:
            return e["nr"]
    nr = max((e["nr"] for e in cat), default=0) + 1
    cat.append({"nr": nr, "slug": slug, "topic": topic, "ticker": ticker, "chart": chart,
                "status": "draft"})
    _CATALOG.write_text(json.dumps(cat, indent=2, ensure_ascii=False), encoding="utf-8")
    return nr


def _write_seo(out_dir, nr, slug, spec, lang):
    """Schreibt eine fertige Posting-/SEO-Datei (YT/TikTok/FB) je Sprache."""
    b = spec[lang]
    cap = b["caption"]
    cap_tt = cap.replace("utm_source=youtube", "utm_source=tiktok")
    cap_fb = cap.replace("utm_source=youtube", "utm_source=facebook")
    link_yt = f"https://seasonalpha.ai/monatszyklus?utm_source=youtube&utm_medium=short&utm_campaign={slug}"
    q = ("Welches saisonale Muster überrascht dich am meisten?" if lang == "de"
         else "Which seasonal pattern surprises you most?")
    ks = spec.get("key_stat", {})
    cs = spec["chart_spec"]
    kws = ", ".join(spec.get("keywords") or [t.lstrip("#") for t in b.get("hashtags", [])])
    tags = ' '.join(b.get('hashtags', []))
    cat = "Bildung" if lang == "de" else "Education"
    md = f"""# SEO / Posting — Video {nr:03d} · {slug} ({lang})

**Thema:** {spec.get('topic','')}
**Kernzahl:** {ks.get('label','')} {ks.get('value','')} — {ks.get('note','')}
**Chart:** {cs.get('type')} · {cs.get('ticker')} · {cs.get('years')}J  ·  **Datei:** {slug}_{lang}.mp4
**Kategorie:** {cat} (Finanzen)  ·  **Sprache:** {lang}

## 🏷️ META-TAGS / Keywords  →  ins YouTube-„Tags"-Feld (kommagetrennt)
{kws}

## # Hashtags  →  in Beschreibung/Caption
{tags}

⚠️ **Beim Upload: KI-Inhalt deklarieren** ("verändert/synthetisch" — KI-Stimme).

## ▶️ YouTube Shorts
**Titel:** {b['video_title']}

**Beschreibung:**
{cap}

**Pinned Comment:** {q} 👇 {link_yt}

## TikTok  (Link in Bio → seasonalpha.ai)
**Caption:** {cap_tt}

## Facebook (Reel)
**Caption:** {cap_fb}
"""
    (out_dir / f"{slug}_{lang}_seo.md").write_text(md, encoding="utf-8")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--script", required=True)
    ap.add_argument("--lang", default="de", choices=["de", "en"])
    ap.add_argument("--music", help="optionales royalty-free Musikbett (mp3)")
    ap.add_argument("--out")
    ap.add_argument("--seo-only", action="store_true", help="nur SEO-Datei schreiben (kein Render/TTS)")
    a = ap.parse_args()

    spec = json.loads(Path(a.script).read_text(encoding="utf-8"))
    block = spec[a.lang]
    cs = spec["chart_spec"]
    slug = spec.get("slug", "short")
    beats = block["beats"]

    nr = _assign_number(slug, spec.get("topic", ""), cs.get("ticker", ""), cs.get("type", ""))
    out_root = _HERE / "out" / f"{nr:03d}_{slug}"
    out_root.mkdir(parents=True, exist_ok=True)
    _write_seo(out_root, nr, slug, spec, a.lang)
    if a.seo_only:
        print(f"[compose] SEO-only -> {out_root}/{slug}_{a.lang}_seo.md")
        return
    out = Path(a.out) if a.out else out_root / f"{slug}_{a.lang}.mp4"
    tmp = Path(tempfile.mkdtemp(prefix="compose_"))

    try:
        # 1) TTS je Beat + Dauern
        print(f"[compose] TTS {len(beats)} Beats ({a.lang}, Stimme {tts.voice_for(a.lang)})…")
        durs = []
        for i, b in enumerate(beats):
            mp3 = tmp / f"beat_{i:03d}.mp3"
            tts.synth(b["vo"], mp3, a.lang)
            durs.append(_dur(mp3))

        # 2) Timeline (Beats + Pausen)
        timeline = []
        t = 0.0
        for i, d in enumerate(durs):
            timeline.append((t, t + d, beats[i]["onscreen"]))
            t += d + GAP
        total_vo = t - GAP
        total = total_vo + TAIL
        print(f"[compose] VO {total_vo:.1f}s, Video {total:.1f}s")

        # 3) Audio concat (mit Stille-Pausen)
        subprocess.run(["ffmpeg", "-y", "-f", "lavfi", "-i", "anullsrc=r=44100:cl=mono",
                        "-t", f"{GAP}", "-q:a", "9", str(tmp / "sil.mp3")],
                       capture_output=True)
        listf = tmp / "list.txt"
        parts = []
        for i in range(len(durs)):
            parts.append(f"file 'beat_{i:03d}.mp3'")
            if i < len(durs) - 1:
                parts.append("file 'sil.mp3'")
        listf.write_text("\n".join(parts) + "\n", encoding="utf-8")
        subprocess.run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(listf),
                        "-c:a", "aac", "-b:a", "160k", str(tmp / "vo.m4a")],
                       capture_output=True)

        # 4) Chart-Clip (Video-Mode, Dauer = total)
        hold = max(0.4, total - ANIM)
        print(f"[compose] Chart rendern ({cs['type']} {cs['ticker']})…")
        render_cmd = [sys.executable, str(_HERE / "render_vertical_chart.py"),
                      "--type", cs["type"], "--ticker", cs["ticker"],
                      "--years", str(cs["years"]), "--lang", a.lang, "--video-mode",
                      "--fps", str(FPS), "--seconds", f"{ANIM}", "--hold", f"{hold:.2f}",
                      "--out", str(tmp / "chart.mp4")]
        if cs.get("highlight_month"):
            render_cmd += ["--highlight-month", str(cs["highlight_month"])]
        if cs.get("month"):
            render_cmd += ["--month", str(cs["month"])]
        r = subprocess.run(render_cmd, capture_output=True, text=True)
        if not (tmp / "chart.mp4").exists():
            sys.exit("[compose] Chart-Render fehlgeschlagen:\n" + r.stdout[-800:] + r.stderr[-800:])

        # 5) ASS-Untertitel
        (tmp / "cap.ass").write_text(
            _ass({"beats": timeline, "disclaimer_overlay": block["disclaimer_overlay"]},
                 total, a.lang), encoding="utf-8")

        # 6) Mux: Chart + (Musik+VO) + eingebrannte ASS  — ffmpeg läuft in tmp (Pfad-Escaping)
        if a.music:
            amix = ["-i", str(Path(a.music).resolve()),
                    "-filter_complex",
                    "[1:a]volume=1.0[a1];[2:a]volume=0.12[a2];[a1][a2]amix=inputs=2:duration=first[a]",
                    "-map", "0:v", "-map", "[a]"]
        else:
            amix = ["-map", "0:v", "-map", "1:a"]
        cmd = (["ffmpeg", "-y", "-i", "chart.mp4", "-i", "vo.m4a"] + amix +
               ["-vf", "ass=cap.ass", "-c:v", "libx264", "-pix_fmt", "yuv420p",
                "-c:a", "aac", "-b:a", "160k", "-shortest", "-movflags", "+faststart",
                "-metadata", f"title={block['video_title']}",
                "-metadata", f"comment={', '.join(spec.get('keywords', []))}",
                str(out.resolve())])
        r = subprocess.run(cmd, cwd=tmp, capture_output=True, text=True)
        if r.returncode != 0:
            sys.exit("[compose] ffmpeg-Mux-Fehler:\n" + r.stderr[-1500:])
        # Hero-Still mitspeichern
        still_src = tmp / "chart_still.png"
        if still_src.exists():
            shutil.copyfile(still_src, out_root / f"{slug}_{a.lang}_still.png")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    print(f"[compose] OK   -> {out}")
    print(f"[compose] SEO  -> {out_root}/{slug}_{a.lang}_seo.md")
    print(f"[compose] Titel: {block['video_title']}")


if __name__ == "__main__":
    main()
