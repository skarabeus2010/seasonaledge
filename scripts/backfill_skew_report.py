#!/usr/bin/env python3
"""
backfill_skew_report.py — Statusbericht nach einem Skew-Backfill per E-Mail.

Beantwortet die eine Frage, die nach einem Nacht-Lauf zaehlt: **wie viele Ticker
erscheinen jetzt im Vol-Regime-Radar?** Der Radar rankt nur laufzeitnormierte
Punkte (cm/cm_extrap) und braucht davon mindestens MIN_NORM je Ticker — ein Lauf
kann also technisch sauber durchlaufen und trotzdem kaum Abdeckung bringen, wenn
die Ketten zu duenn sind. Genau das misst dieser Bericht, statt nur "exit 0" zu
melden.

Nutzung (server-seitig, im Container):
    python3 scripts/backfill_skew_report.py --baseline 53 --log /tmp/bf.log
    python3 scripts/backfill_skew_report.py --dry-run        # nur ausgeben

Env: BREVO_API_KEY (Versand), ADMIN_EMAIL (Empfaenger).
"""
from __future__ import annotations
import argparse, json, os, sys
from datetime import datetime, timezone
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))
from shared.env_loader import load_env                      # noqa: E402
load_env()
from shared.options_universe import all_option_tickers      # noqa: E402

MIN_NORM = 20            # muss zu landing/pages/skew.html::MIN_NORM passen
_HIST = _ROOT / "landing/data/options_skew_history.json"


def coverage() -> dict:
    """Je Universums-Ticker die Zahl laufzeitnormierter Punkte + Einteilung."""
    hist = json.loads(_HIST.read_text(encoding="utf-8"))
    uni = all_option_tickers()
    ok, thin, none = [], [], []
    for t in uni:
        n = sum(1 for e in hist.get(t, [])
                if e.get("cm_mode") in ("cm", "cm_extrap"))
        (ok if n >= MIN_NORM else (thin if n else none)).append((t, n))
    return {"universe": len(uni), "ok": ok, "thin": thin, "none": none,
            "points": sum(len(v) for v in hist.values()), "tickers": len(hist)}


def log_summary(path):
    """Abschlusszeile + auffaellige Zeilen aus dem Container-Log."""
    if not path or not Path(path).exists():
        return "", []
    lines = Path(path).read_text(encoding="utf-8", errors="replace").splitlines()
    done = ""
    for line in reversed(lines):
        if line.startswith("[OK]"):
            done = line.strip()
            break
    keys = ("FEHLER", "keine Kursreihe", "keine Kontrakte", "zu wenig Handelstage")
    odd = [l.strip() for l in lines if any(k in l for k in keys)]
    return done, odd[:15]


def progress(path):
    """Position im Lauf aus dem Container-Log: (fertig, gesamt, aktueller Ticker)."""
    if not path or not Path(path).exists():
        return None, None, None
    lines = Path(path).read_text(encoding="utf-8", errors="replace").splitlines()
    fertig = sum(1 for l in lines
                 if "Punkte (Abdeckung" in l or "bereits vollstaendig" in l
                 or "bereits vollständig" in l)
    pos = None
    for line in reversed(lines):
        t = line.strip()
        if t.startswith("[") and "/" in t and "]" in t:
            head = t[1:t.index("]")]
            if "/" in head and head.split("/")[0].isdigit():
                pos = (head, t[t.index("]") + 1:].strip())
                break
    gesamt = pos[0].split("/")[1] if pos else None
    return fertig, gesamt, (pos[1] if pos else None)


def render(cov, baseline, done, odd):
    n_ok, n_uni = len(cov["ok"]), cov["universe"]
    pct = (100.0 * n_ok / n_uni) if n_uni else 0.0
    delta = " (vorher {})".format(baseline) if baseline is not None else ""
    subject = "Skew-Backfill fertig: {}/{} Ticker im Radar ({:.0f}%)".format(n_ok, n_uni, pct)

    # Bewusst schlichtes HTML: Gmail kappt Mails ueber ~102 KB und rendert
    # exotische Zeichen nicht — deshalb Klartext-Labels statt Symbolen.
    css = "font-family:-apple-system,Segoe UI,Arial,sans-serif;font-size:14px;color:#222"

    thin_block = ""
    if cov["thin"]:
        rows = "".join(
            "<tr><td style='padding:2px 10px 2px 0'>{}</td>"
            "<td style='padding:2px 0;text-align:right;color:#a00'>{}</td></tr>".format(t, n)
            for t, n in sorted(cov["thin"], key=lambda x: x[1]))
        thin_block = (
            "<p style='margin:14px 0 4px'><b>Weiterhin unter der Schwelle "
            "({} normierte Tage) &mdash; {} Ticker:</b><br>"
            "<span style='color:#666'>Zu duenne 25-Delta-Liquiditaet. Kein Fehler, "
            "sondern schlicht fehlende Trades &mdash; diese Titel bleiben bewusst aus "
            "dem Radar, statt einen Schein-Percentile zu zeigen.</span></p>"
            "<table style='border-collapse:collapse'>{}</table>"
        ).format(MIN_NORM, len(cov["thin"]), rows)

    none_block = ""
    if cov["none"]:
        none_block = ("<p style='margin:14px 0 0;color:#a00'><b>Ganz ohne normierte "
                      "Punkte:</b> {}</p>").format(", ".join(t for t, _ in cov["none"]))

    odd_block = ""
    if odd:
        odd_block = ("<p style='margin:14px 0 4px'><b>Auffaelligkeiten im Log:</b></p>"
                     "<pre style='background:#f6f6f6;padding:8px;font-size:12px;"
                     "white-space:pre-wrap'>{}</pre>").format("\n".join(odd))

    done_block = "<p style='margin:0 0 10px'><code>{}</code></p>".format(done) if done else ""

    html = (
        '<div style="{css}">'
        '<h2 style="margin:0 0 4px">Skew-Backfill abgeschlossen</h2>'
        '<p style="color:#666;margin:0 0 14px">{stamp} UTC</p>'
        '<p style="font-size:20px;margin:0 0 2px"><b>{n_ok} von {n_uni} Tickern</b> '
        'erscheinen im Vol-Regime-Radar ({pct:.0f}%){delta}</p>'
        '<p style="color:#666;margin:0 0 14px">Historie gesamt: {pts} Punkte ueber '
        '{tks} Ticker</p>'
        '{done_block}{thin_block}{none_block}{odd_block}'
        '<p style="margin:18px 0 0;color:#666;font-size:13px">'
        '<b>Naechste Schritte:</b> <code>--verify</code> gegen die neu gefuellten '
        'Ticker laufen lassen; danach ist der Options-Screener ueber dem vollen '
        'Universum sinnvoll. Details in docs/OPTIONS.md.</p>'
        '</div>'
    ).format(css=css, stamp=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M"),
             n_ok=n_ok, n_uni=n_uni, pct=pct, delta=delta,
             pts="{:,}".format(cov["points"]), tks=cov["tickers"],
             done_block=done_block, thin_block=thin_block,
             none_block=none_block, odd_block=odd_block)

    text = ("Skew-Backfill fertig.\n"
            "{}/{} Ticker im Radar ({:.0f}%){}\n"
            "Historie: {} Punkte / {} Ticker\n{}\n"
            "Zu duenn: {} Ticker\n").format(
        n_ok, n_uni, pct, delta, cov["points"], cov["tickers"], done, len(cov["thin"]))
    return subject, html, text


def render_progress(cov, baseline, fertig, gesamt, aktuell, started):
    """Zwischenstand waehrend eines laufenden Backfills."""
    n_ok, n_uni = len(cov["ok"]), cov["universe"]
    delta = " (Start: {})".format(baseline) if baseline is not None else ""
    pos = "{}/{}".format(fertig, gesamt) if (fertig is not None and gesamt) else "?"
    subject = "Skew-Backfill laeuft: {} Ticker fertig, {}/{} im Radar".format(pos, n_ok, n_uni)

    eta = ""
    if started and fertig and gesamt and int(fertig) > 0:
        import time as _t
        el = _t.time() - started
        rest = el / int(fertig) * (int(gesamt) - int(fertig))
        eta = ("<p style='margin:0 0 14px'>Bisher {:.1f} h gelaufen, "
               "geschaetzt noch <b>{:.1f} h</b>.</p>").format(el / 3600, rest / 3600)

    css = "font-family:-apple-system,Segoe UI,Arial,sans-serif;font-size:14px;color:#222"
    html = (
        '<div style="{css}">'
        '<h2 style="margin:0 0 4px">Skew-Backfill: Zwischenstand</h2>'
        '<p style="color:#666;margin:0 0 14px">{stamp} UTC</p>'
        '<p style="font-size:18px;margin:0 0 2px"><b>{pos} Ticker</b> verarbeitet'
        '{akt}</p>'
        '<p style="font-size:18px;margin:0 0 10px"><b>{n_ok} von {n_uni}</b> Tickern '
        'im Vol-Regime-Radar{delta}</p>{eta}'
        '<p style="color:#666;font-size:13px;margin:0">Historie: {pts} Punkte. '
        'Der Lauf pausiert automatisch von 00:50 bis 02:10 (Berliner Zeit), damit '
        'der naechtliche Cron seine Tagespunkte schreiben kann.</p></div>'
    ).format(css=css, stamp=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M"),
             pos=pos, akt=(" &mdash; aktuell " + aktuell) if aktuell else "",
             n_ok=n_ok, n_uni=n_uni, delta=delta, eta=eta,
             pts="{:,}".format(cov["points"]))
    text = "Skew-Backfill laeuft. {} Ticker fertig, {}/{} im Radar{}.".format(
        pos, n_ok, n_uni, delta)
    return subject, html, text


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--baseline", type=int, default=None,
                    help="Ticker im Radar VOR dem Lauf (Vorher/Nachher-Vergleich)")
    ap.add_argument("--log", default=None, help="Pfad zum Container-Log")
    ap.add_argument("--to", default=None)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--progress", action="store_true",
                    help="Zwischenstand statt Abschlussbericht")
    ap.add_argument("--started", type=float, default=None,
                    help="Startzeit als Unix-Timestamp (fuer die Restzeit-Schaetzung)")
    a = ap.parse_args()

    if not _HIST.exists():
        print("[report] History fehlt:", _HIST)
        return 1
    cov = coverage()
    if a.progress:
        fertig, gesamt, aktuell = progress(a.log)
        subject, html, text = render_progress(cov, a.baseline, fertig, gesamt,
                                              aktuell, a.started)
    else:
        done, odd = log_summary(a.log)
        subject, html, text = render(cov, a.baseline, done, odd)

    print("[report] " + subject)
    print("[report] zu duenn: {} · ohne Punkte: {}".format(len(cov["thin"]), len(cov["none"])))
    if a.dry_run:
        print("[report] --dry-run, kein Versand")
        return 0

    from shared.email_brevo import send_html
    to = a.to or os.environ.get("ADMIN_EMAIL", "heiko.seibel@gmail.com")
    ok = send_html(to, subject, html, text)
    print("[report] Versand an {}: {}".format(to, "OK" if ok else "FEHLGESCHLAGEN"))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
