"""Seitenprobe True Seasonal auf /jahreszyklus (Plan v3: docs/review_prompts/2026-10-16_true_seasonal_plan_v3.md).

Fährt die ECHTE Seite in jsdom (scripts/js/probe_seiten_kurse.js, deterministische Kurse, feste Uhr 09.10.2026) und
prüft gegen Sollwerte:
  * Standard = Durchschnitt wie bisher, Rückblick eingeklappt lädt nichts nach (keine Abfrage ohne Untergrenze);
  * gemerkter Modus „true": Hauptkurve „True Seasonal (10J)" aus 2016–2025, die goldene Linie des laufenden Jahres bleibt;
  * Rückblick lädt die volle Historie erst beim Aufklappen und lässt den Hauptchart unverändert;
  * Tickerwechsel während der Rückblick-Ladung: Ergebnis = direkt gewählter Ticker (verspätete Antwort verworfen);
  * Ladefehler ist sichtbar und mit „Erneut laden" behebbar.
Die Rechnung selbst prüft verify_seasonal_twins.py (Block 8).

Aufruf: py -3.14 scripts/verify_true_seasonal_seite.py   (braucht: npm ci --prefix scripts/perf)
"""
import concurrent.futures
import json
import pathlib
import subprocess
import sys

WURZEL = pathlib.Path(__file__).resolve().parent.parent
PROBE = WURZEL / "scripts" / "js" / "probe_seiten_kurse.js"
FAELLE = ("normal", "saison_true", "rueckblick", "rueckblick_wechsel", "rueckblick_direkt", "rueckblick_fehler",
          "embed_true", "embed_true_wenig", "saison_true_neu")


def lauf(fall):
    seite = "embed" if fall.startswith("embed_") else "jahreszyklus"
    try:
        r = subprocess.run(["node", str(PROBE), str(WURZEL / "landing"), seite, fall],
                           capture_output=True, text=True, encoding="utf-8", timeout=240)
    except subprocess.TimeoutExpired:
        return None, "Frist überschritten"
    try:
        d = json.loads(r.stdout)
    except ValueError:
        return None, "kein JSON: " + (r.stdout or r.stderr)[-300:]
    if d.get("absturz"):
        return None, "Absturz: " + d["absturz"][:300]
    return (d, None) if d.get("ende") is True else (None, "ohne Endmarker")


def endstand(d, el):
    aus = None
    for c in d["charts"]:
        if c["el"] == el:
            aus = c["updates"][-1] if c["updates"] else c["series"]
    return aus


def namen(d, el):
    s = endstand(d, el)
    return [x.get("name") for x in json.loads(s)] if s and s not in ("null", "[]") else []


def main():
    erg, ok = [], True

    def pruefe(name, bed, detail=""):
        nonlocal ok
        erg.append(("ok  " if bed else "FEHL") + " [%s] %s" % (name, detail))
        ok = ok and bool(bed)

    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as ex:
        res = dict(zip(FAELLE, ex.map(lauf, FAELLE)))
    d = {}
    for f in FAELLE:
        x, fehler = res[f]
        pruefe(f + " läuft", x is not None, fehler or "")
        if x is not None:
            pruefe(f + " Ruhe erreicht", x["ruhig"])
            pruefe(f + " ohne Seitenfehler", not x["seitenfehler"], " | ".join(x["seitenfehler"])[:300])
            d[f] = x
    if len(d) != len(FAELLE):
        return fertig(erg, False)

    voll = lambda x: [u for u in x["kursanfragen"] if "/prices" in u and "date=gte." not in u]
    n = d["normal"]
    nm = namen(n, "chart-main")
    pruefe("Standard: Durchschnitt, kein True Seasonal", any(s.startswith("Saisonaler Ø (") for s in nm)
           and not any("True Seasonal" in s for s in nm), str(nm))
    pruefe("Standard: Bildunterschrift nennt den Durchschnitt inkl. laufendem Jahr", "Durchschnitt inkl." in (n["caption"] or ""),
           n["caption"])
    pruefe("Standard: Rückblick eingeklappt lädt keine volle Historie", not voll(n), str(voll(n))[:200])

    t = d["saison_true"]
    tm = namen(t, "chart-main")
    pruefe("True-Modus: Hauptkurve True Seasonal aus 10 Vorjahren", "True Seasonal (10J)" in tm, str(tm))
    pruefe("True-Modus: goldene Linie des laufenden Jahres bleibt", any(s.startswith("2026 (") for s in tm), str(tm))
    pruefe("True-Modus: Bildunterschrift 2016–2025, kein Hinweis auf zu wenig Jahre",
           "2016–2025" in (t["caption"] or "") and "True Seasonal" in (t["caption"] or "") and not t["ts_hinweis"],
           "%s | %s" % (t["caption"], t["ts_hinweis"]))
    pruefe("True-Modus: Einzeljahre/Detrend gezeichnet, Hauptkurve weicht vom Durchschnitt ab",
           endstand(t, "chart-main") != endstand(n, "chart-main"))

    r = d["rueckblick"]
    pruefe("Rückblick: volle Historie erst nach dem Aufklappen geladen", len(voll(r)) >= 1, str(voll(r))[:200])
    pruefe("Rückblick: Chart mit zwei Reihen", len(namen(r, "chart-rueckblick")) == 2, str(namen(r, "chart-rueckblick")))
    pruefe("Rückblick: Status nennt die bewerteten Jahre", "Jahre bewertet" in (r["rb_status"] or ""), r["rb_status"])
    pruefe("Rückblick: Hauptchart unverändert", endstand(r, "chart-main") == endstand(n, "chart-main"))

    w, di = d["rueckblick_wechsel"], d["rueckblick_direkt"]
    pruefe("Wechsel: angezeigter Ticker QQQ", w["titel"] == "QQQ" and di["titel"] == "QQQ", "%s / %s" % (w["titel"], di["titel"]))
    pruefe("Wechsel: Rückblick = direkt gewählt (verspätete SPY-Antwort verworfen)",
           endstand(w, "chart-rueckblick") == endstand(di, "chart-rueckblick") and w["rb_status"] == di["rb_status"]
           and endstand(w, "chart-rueckblick") not in (None, "null", "[]"), "%s / %s" % (w["rb_status"], di["rb_status"]))
    pruefe("Wechsel: Hauptchart = direkt gewählt", endstand(w, "chart-main") == endstand(di, "chart-main"))

    f = d["rueckblick_fehler"]
    pruefe("Fehler: Ladefehler sichtbar mit „Erneut laden\"", "konnte nicht geladen" in (f["rb_status_vorher"] or "")
           and "Erneut laden" in (f["rb_status_vorher"] or ""), f["rb_status_vorher"])
    pruefe("Fehler: nach „Erneut laden\" bewertet", "Jahre bewertet" in (f["rb_status"] or "")
           and endstand(f, "chart-rueckblick") == endstand(r, "chart-rueckblick"), f["rb_status"])
    e, ew = d["embed_true"], d["embed_true_wenig"]
    en = [c for c in e["charts"] if c["el"] == "chart"]
    ser = json.loads(en[-1]["series"]) if en else []
    pruefe("Embed saison=true: Reihe True Seasonal (10J), Titel ohne Rückfall",
           bool(ser) and ser[0]["name"] == "True Seasonal (10J)" and "nicht verfügbar" not in (en[-1].get("titel") or ""),
           "%s | %s" % ([x["name"] for x in ser], en[-1].get("titel") if en else None))
    seite = json.loads(endstand(t, "chart-main") or "[]")
    ts = next((x["data"] for x in seite if x.get("name") == "True Seasonal (10J)"), None)
    werte = [(ser[0]["data"][i], ts[i]) for i in (30, 100, 200, 300) if ser and ts and ts[i] is not None]
    pruefe("Embed = Seite: dieselbe True-Seasonal-Kurve (Tag 31/101/201/301, Rundung 0,01)",
           len(werte) == 4 and all(abs(a - b) <= 0.006 for a, b in werte), str(werte))
    enw = [c for c in ew["charts"] if c["el"] == "chart"]
    serw = json.loads(enw[-1]["series"]) if enw else []
    pruefe("Embed zu wenige Vorjahre: Durchschnitt mit sichtbarem Hinweis (6/8)",
           bool(serw) and serw[0]["name"].startswith("Saisonaler Ø")
           and "True Seasonal nicht verfügbar (6/8 Vorjahre)" in (enw[-1].get("titel") or ""),
           "%s | %s" % ([x["name"] for x in serw], enw[-1].get("titel") if enw else None))
    sn = d["saison_true_neu"]
    snm = json.loads(endstand(sn, "chart-main") or "[]")
    sav = next((x for x in snm if (x.get("name") or "").startswith("Saisonaler Ø (")), None)
    pruefe("Seite zu wenige Vorjahre (LUECKE): sichtbarer Hinweis und Durchschnitt",
           sav is not None and "nicht verfügbar" in (sn["ts_hinweis"] or ""), "%s | %s" % (sav and sav["name"], sn["ts_hinweis"]))
    werte = [(serw[0]["data"][i], sav["data"][i]) for i in (30, 100, 200) if serw and sav and sav["data"][i] is not None]
    pruefe("Embed-Rückfall = Seiten-Rückfall: gleiche Jahresmenge und Kurve (Tag 31/101/201, Rundung 0,01)",
           bool(serw) and sav is not None and serw[0]["name"] == sav["name"] and len(werte) == 3
           and all(abs(a - b) <= 0.006 for a, b in werte), "%s / %s %s" % (serw[0]["name"] if serw else None,
                                                                         sav and sav["name"], werte))
    return fertig(erg, ok)


def fertig(erg, ok):
    for e in erg:
        sys.stdout.write(e + "\n")
    n_pr = sum(1 for e in erg if e.startswith(("ok", "FEHL")))
    sys.stdout.write("verify_true_seasonal_seite: %s (%d Prüfungen)\n" % ("BESTANDEN" if ok else "DURCHGEFALLEN", n_pr))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
