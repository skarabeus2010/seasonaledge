"""Wächter für die Produktionssperre (shared/produktionssperre.py, docs/KALENDER_UMSTELLUNG.md V1a).

1. Inventar: jedes Skript unter scripts/ (oberste Ebene) mit einem Schreib- oder Versandaufruf steht in GENAU einer
   der Listen PFLICHT / AUSNAHMEN; jede gelistete Datei existiert. Pflicht-Skripte schreiben nur über
   `get_client()` (kein eigener Client, kein REST-Direktzugriff) — sonst greift der Schreibschutz nicht.
2. Einbau: jedes PFLICHT-Skript betritt `with produktion("<name>")` im `__main__`-Block, und der Hauptaufruf liegt
   darin (AST, nicht Text). Newsletter: `pruefe_schreiben("<name>.versand")` steht vor dem ersten `send_html(`.
3. Verhalten (echtes Modul, Unterprozesse): ohne Marke läuft der Rumpf; Marke ohne/mit falscher Kennung → Exit 75
   ohne Rumpf, mit Betriebsnachweis; passende Kennung nur für freigegebene Läufe/Modi; die Kennung wird nicht an
   Kindprozesse vererbt; ein gehaltener EXKLUSIVER Lock blockiert den Start; `aktivierung_setzen` wartet auf
   laufende Läufe und gibt den Lock danach frei (Lock-Prüfungen nur mit fcntl — sonst UNGEPRÜFT, im Deploy-Gate
   (Linux) Pflicht).
4. Schreibschutz (echter `get_client()` mit Ersatz-Client): Import-Einstieg ohne `produktion()` darf bei Marke nicht
   in geschützte Tabellen/RPCs schreiben; ungeschützte Tabellen und Lesezugriffe bleiben frei; ohne Marke ist alles
   frei; eine lesende Freigabe (Abnahme) schreibt nicht.
5. Echte Skripte — in einer ISOLIERTEN KOPIE (Temp-Verzeichnis, keine Ausgabe landet im Projektbaum, Netz und
   Datenbank tot): jedes ausführbare PFLICHT-Skript endet bei gesetzter Marke mit Exit 75, als Datei und als `-m`.
6. Betrieb: install_timers.sh prüft die Marke vor dem Starten; deploy.yml überspringt `[ohne-deploy]`; die
   systemd-Units der Pflicht-Läufe werten 75 als Erfolg; jeder Workflow, der ein Pflicht-Skript per `docker exec`
   startet, bildet 75 (und nur 75) auf Erfolg ab.
"""
import ast
import os
import pathlib
import re
import shutil
import subprocess
import sys
import tempfile
import textwrap
import time

WURZEL = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(WURZEL))
from shared import produktionssperre as ps  # noqa: E402

SCHREIBMUSTER = re.compile(r"upsert_|\.upsert\(|\.insert\(|\.update\(|\.delete\(|send_email|brevo|smtp|"
                           r"write_json_atomic|landing/data")
ERGEBNIS, OK = [], True


def pruefe(name, bedingung, detail=""):
    global OK
    ERGEBNIS.append(("ok  " if bedingung else "FEHL") + " [%s] %s" % (name, detail))
    OK = OK and bool(bedingung)


def isolierte_kopie(quelle: pathlib.Path, ziel: pathlib.Path) -> pathlib.Path:
    """Kopiert den für Python-Läufe nötigen Teil des Baums (shared/, scripts/, deploy/, .github/, landing/data/
    ohne Cron-Ausgaben-Riesen) nach `ziel`. Keine Logs, keine .env, keine Mounts. Gibt `ziel` zurück."""
    ignor = shutil.ignore_patterns("__pycache__", "node_modules", "*.pyc", ".mutation-tmp")
    for teil in ("shared", "scripts", "deploy", ".github"):
        if (quelle / teil).exists():
            shutil.copytree(quelle / teil, ziel / teil, ignore=ignor)
    daten = quelle / "landing" / "data"
    if daten.exists():
        (ziel / "landing" / "data").mkdir(parents=True)
        for f in daten.iterdir():
            if f.is_file() and f.suffix in (".json", ".ics") and f.stat().st_size < 2_000_000:
                shutil.copy2(f, ziel / "landing" / "data" / f.name)
    return ziel


def inventar():
    gefunden = set()
    for f in sorted((WURZEL / "scripts").glob("*.py")):
        if f.name.startswith("verify_") or f.name.endswith("_mutation.py"):
            continue
        if SCHREIBMUSTER.search(f.read_text(encoding="utf-8", errors="replace")):
            gefunden.add(f.name)
    beide = set(ps.PFLICHT) & set(ps.AUSNAHMEN)
    pruefe("Inventar: keine Datei in beiden Listen", not beide, sorted(beide))
    fehlt = sorted(gefunden - set(ps.PFLICHT) - set(ps.AUSNAHMEN))
    pruefe("Inventar: jedes schreibende Skript eingeordnet", not fehlt, fehlt)
    weg = sorted(n for n in list(ps.PFLICHT) + list(ps.AUSNAHMEN) if not (WURZEL / "scripts" / n).exists())
    pruefe("Inventar: gelistete Dateien existieren", not weg, weg)
    direkt = sorted(n for n in ps.PFLICHT
                    if re.search(r"create_client\(|/rest/v1|requests\.(post|patch|delete)\(",
                                 (WURZEL / "scripts" / n).read_text(encoding="utf-8")))
    pruefe("Inventar: Pflicht-Skripte schreiben nur über get_client()", not direkt, direkt)


def einbau():
    for name in sorted(ps.PFLICHT):
        baum = ast.parse((WURZEL / "scripts" / name).read_text(encoding="utf-8"))
        main_if = [n for n in baum.body if isinstance(n, ast.If)
                   and ast.unparse(n.test).replace("'", '"') == '__name__ == "__main__"']
        ok, detail = False, "kein __main__-Block"
        if len(main_if) == 1:
            withs = [n for n in ast.walk(main_if[0]) if isinstance(n, ast.With)]
            for w in withs:
                for item in w.items:
                    c = item.context_expr
                    if (isinstance(c, ast.Call) and ast.unparse(c.func).endswith("produktion")
                            and c.args and isinstance(c.args[0], ast.Constant) and c.args[0].value == name[:-3]):
                        aufrufe = [n for n in ast.walk(ast.Module(body=w.body, type_ignores=[])) if isinstance(n, ast.Call)]
                        ok = bool(aufrufe)
                        detail = "" if ok else "Rumpf ohne Aufruf"
            if not ok and detail == "kein __main__-Block":
                detail = "kein with produktion(\"%s\")" % name[:-3]
        pruefe("Einbau: %s" % name, ok, detail)
        # Import-Einstieg: `if __name__ != "__main__": modul_sperre("<name>")` auf Modulebene, vor der ersten
        # Funktion/Klasse — sonst schreibt `from scripts.<x> import main; main()` an der Sperre vorbei.
        erste_def = min([n.lineno for n in baum.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef,
                                                                          ast.ClassDef))] or [10**9])
        modul_ok = any(
            isinstance(n, ast.If) and n.lineno < erste_def
            and ast.unparse(n.test).replace("'", '"') == '__name__ != "__main__"'
            and any(isinstance(c, ast.Call) and ast.unparse(c.func).endswith("modul_sperre") and c.args
                    and isinstance(c.args[0], ast.Constant) and c.args[0].value == name[:-3]
                    for c in ast.walk(n))
            for n in baum.body)
        pruefe("Einbau: %s sperrt beim Import" % name, modul_ok)
    for nl in ("daily_newsletter", "weekly_newsletter"):
        q = (WURZEL / "scripts" / (nl + ".py")).read_text(encoding="utf-8")
        schutz = q.find('pruefe_schreiben("%s.versand")' % nl)
        versand = q.find("send_html(")
        pruefe("Einbau: %s prüft vor dem Versand" % nl, 0 <= schutz < versand, "Schutz %d, Versand %d" % (schutz, versand))
    sc = (WURZEL / "shared" / "supabase_client.py").read_text(encoding="utf-8")
    pruefe("Einbau: get_client() liefert den geschützten Client", "_client = _Geschuetzt(create_client(url, key))" in sc)


def lauf_probe(code, env_extra, sperr, argv=()):
    env = {**os.environ, "SA_SPERR_DIR": str(sperr), "PYTHONPATH": str(WURZEL), "SA_SPERRE_KEIN_DB_NACHWEIS": "1",
           "PYTHONUTF8": "1"}
    env.pop("SA_AKTIVIERUNG", None)
    env.update(env_extra)
    return subprocess.run([sys.executable, "-c", code, *argv], capture_output=True, text=True, env=env, timeout=60)


def _code(name):
    return textwrap.dedent(f"""
        import os, subprocess, sys
        from shared.produktionssperre import produktion
        with produktion({name!r}):
            kind = subprocess.run([sys.executable, "-c", "import os; print(os.environ.get('SA_AKTIVIERUNG', ''))"],
                                  capture_output=True, text=True).stdout.strip()
            print("RUMPF", "KIND=" + kind, "ELTERN=" + os.environ.get("SA_AKTIVIERUNG", ""))
    """)


def verhalten():
    with tempfile.TemporaryDirectory() as t:
        sperr = pathlib.Path(t)
        r = lauf_probe(_code("probe"), {}, sperr)
        pruefe("Verhalten: ohne Marke läuft der Rumpf", r.returncode == 0 and "RUMPF" in r.stdout, r.stderr[-200:])
        (sperr / "AKTIVIERUNG").write_text("k-123\n", encoding="utf-8")
        r = lauf_probe(_code("daily_newsletter"), {}, sperr, ["--dry-run"])
        pruefe("Verhalten: Marke ohne Kennung → Exit 75, kein Rumpf", r.returncode == 75 and "RUMPF" not in r.stdout,
               "Exit %s" % r.returncode)
        log = (sperr / "unterdrueckt.log")
        pruefe("Verhalten: Unterdrückung hinterlässt Betriebsnachweis",
               log.exists() and "daily_newsletter" in log.read_text(encoding="utf-8"))
        r = lauf_probe(_code("daily_newsletter"), {"SA_AKTIVIERUNG": "falsch"}, sperr, ["--dry-run"])
        pruefe("Verhalten: falsche Kennung → Exit 75", r.returncode == 75 and "RUMPF" not in r.stdout, "Exit %s" % r.returncode)
        r = lauf_probe(_code("daily_newsletter"), {"SA_AKTIVIERUNG": "k-123"}, sperr, ["--dry-run"])
        pruefe("Verhalten: passende Kennung läuft (freigegebener Modus)", r.returncode == 0 and "RUMPF" in r.stdout,
               "Exit %s %s" % (r.returncode, r.stderr[-150:]))
        pruefe("Verhalten: Kennung wird nicht vererbt", "KIND= " in r.stdout and "ELTERN=" in r.stdout
               and "k-123" not in r.stdout, r.stdout.strip()[:120])
        r = lauf_probe(_code("abnahme:seiten"), {"SA_AKTIVIERUNG": "k-123"}, sperr)
        pruefe("Verhalten: Abnahmeprobe mit Kennung läuft", r.returncode == 0 and "RUMPF" in r.stdout, "Exit %s" % r.returncode)
        r = lauf_probe(_code("daily_newsletter"), {"SA_AKTIVIERUNG": "k-123"}, sperr)
        pruefe("Verhalten: Kennung ohne freigegebenen Modus → 75 (Newsletter ohne --dry-run)",
               r.returncode == 75 and "RUMPF" not in r.stdout, "Exit %s" % r.returncode)
        r = lauf_probe(_code("nightly_refresh"), {"SA_AKTIVIERUNG": "k-123"}, sperr)
        pruefe("Verhalten: Kennung für nicht freigegebenen Lauf → 75 (Nightly)",
               r.returncode == 75 and "RUMPF" not in r.stdout, "Exit %s" % r.returncode)
        verschachtelt = textwrap.dedent("""
            from shared.produktionssperre import produktion
            with produktion("abnahme:aussen"):
                with produktion("nightly_refresh"):
                    print("RUMPF")
        """)
        r = lauf_probe(verschachtelt, {"SA_AKTIVIERUNG": "k-123"}, sperr)
        pruefe("Verhalten: verschachtelter nicht freigegebener Lauf → 75",
               r.returncode == 75 and "RUMPF" not in r.stdout, "Exit %s" % r.returncode)
        (sperr / "AKTIVIERUNG").unlink()
        if ps.fcntl is None:
            ERGEBNIS.append("UNGEPRÜFT [Verhalten: exklusiver Lock blockiert] kein fcntl in dieser Umgebung")
            ERGEBNIS.append("UNGEPRÜFT [Verhalten: aktivierung_setzen wartet und gibt frei] kein fcntl")
            return "ungeprueft"
        lockdatei = str(sperr / "produktion.lock")
        halter = subprocess.Popen([sys.executable, "-c", textwrap.dedent(f"""
            import fcntl, os, time
            fd = os.open({lockdatei!r}, os.O_RDWR | os.O_CREAT, 0o644)
            fcntl.flock(fd, fcntl.LOCK_EX); print("HALTE", flush=True); time.sleep(1.5)
        """)], stdout=subprocess.PIPE, text=True)
        halter.stdout.readline()
        t0 = time.time()
        r = lauf_probe(_code("probe"), {}, sperr)
        dauer = time.time() - t0
        halter.wait(timeout=10)
        pruefe("Verhalten: exklusiver Lock blockiert den Start", r.returncode == 0 and dauer >= 1.0, "%.2f s" % dauer)
        # aktivierung_setzen: wartet auf einen laufenden (geteilten) Lauf, setzt die Marke, gibt den Lock frei
        laeufer = subprocess.Popen([sys.executable, "-c", textwrap.dedent(f"""
            import fcntl, os, time
            fd = os.open({lockdatei!r}, os.O_RDWR | os.O_CREAT, 0o644)
            fcntl.flock(fd, fcntl.LOCK_SH); print("LAEUFT", flush=True); time.sleep(1.5)
        """)], stdout=subprocess.PIPE, text=True)
        laeufer.stdout.readline()
        t0 = time.time()
        r = lauf_probe("from shared.produktionssperre import aktivierung_setzen; aktivierung_setzen('k-9')", {}, sperr)
        warte = time.time() - t0
        laeufer.wait(timeout=10)
        pruefe("Verhalten: aktivierung_setzen wartet auf laufende Läufe",
               r.returncode == 0 and warte >= 1.0 and (sperr / "AKTIVIERUNG").read_text().strip() == "k-9",
               "%.2f s, Exit %s" % (warte, r.returncode))
        t0 = time.time()
        r = lauf_probe(_code("abnahme:x"), {"SA_AKTIVIERUNG": "k-9"}, sperr)
        pruefe("Verhalten: nach aktivierung_setzen ist der Lock frei (Abnahme startet sofort)",
               r.returncode == 0 and "RUMPF" in r.stdout and time.time() - t0 < 5, "Exit %s" % r.returncode)
        r = lauf_probe("from shared.produktionssperre import aktivierung_aufheben as a\n"
                       "try:\n    a('fremd'); print('ENTFERNT')\nexcept ValueError:\n    print('ABGELEHNT')", {}, sperr)
        pruefe("Verhalten: fremde Kennung hebt die Aktivierung nicht auf",
               "ABGELEHNT" in r.stdout and (sperr / "AKTIVIERUNG").exists())
        (sperr / "AKTIVIERUNG").unlink()
        # Import-Einstieg hält den Lock bis Prozessende: aktivierung_setzen wartet auf ihn
        importeur = subprocess.Popen([sys.executable, "-c", textwrap.dedent("""
            import time
            from shared.produktionssperre import modul_sperre
            modul_sperre("probe_import"); print("IMPORTIERT", flush=True); time.sleep(1.5)
        """)], stdout=subprocess.PIPE, text=True,
            env={**os.environ, "SA_SPERR_DIR": str(sperr), "PYTHONPATH": str(WURZEL)})
        importeur.stdout.readline()
        t0 = time.time()
        r = lauf_probe("from shared.produktionssperre import aktivierung_setzen; aktivierung_setzen('k-imp')", {}, sperr)
        warte = time.time() - t0
        importeur.wait(timeout=10)
        pruefe("Verhalten: aktivierung_setzen wartet auf einen Import-Einstieg", r.returncode == 0 and warte >= 1.0,
               "%.2f s" % warte)
        (sperr / "AKTIVIERUNG").unlink()
        # Import INNERHALB eines äußeren Blocks: das Blockende darf den Lock des Imports nicht freigeben
        verschachtelt_import = subprocess.Popen([sys.executable, "-c", textwrap.dedent("""
            import time
            from shared.produktionssperre import modul_sperre, produktion
            with produktion("probe_aussen"):
                modul_sperre("probe_import")
            print("BLOCK-ENDE", flush=True); time.sleep(1.5)
        """)], stdout=subprocess.PIPE, text=True,
            env={**os.environ, "SA_SPERR_DIR": str(sperr), "PYTHONPATH": str(WURZEL)})
        verschachtelt_import.stdout.readline()
        r = lauf_probe("from shared.produktionssperre import aktivierung_setzen\n"
                       "try:\n    aktivierung_setzen('k-vi', frist_s=0.8)\n    print('GESETZT')\n"
                       "except TimeoutError:\n    print('FRIST')", {}, sperr)
        verschachtelt_import.wait(timeout=10)
        pruefe("Verhalten: Import im äußeren Block hält den Lock über das Blockende hinaus",
               "FRIST" in r.stdout and not (sperr / "AKTIVIERUNG").exists(), r.stdout.strip())
        if (sperr / "AKTIVIERUNG").exists():
            (sperr / "AKTIVIERUNG").unlink()
        # Frist: ein hängender Halter führt zu TimeoutError, nicht zu einer Marke
        halter = subprocess.Popen([sys.executable, "-c", textwrap.dedent(f"""
            import fcntl, os, time
            fd = os.open({lockdatei!r}, os.O_RDWR | os.O_CREAT, 0o644)
            fcntl.flock(fd, fcntl.LOCK_SH); print("HALTE", flush=True); time.sleep(3)
        """)], stdout=subprocess.PIPE, text=True)
        halter.stdout.readline()
        r = lauf_probe("from shared.produktionssperre import aktivierung_setzen\n"
                       "try:\n    aktivierung_setzen('k-frist', frist_s=1)\nexcept TimeoutError:\n    print('FRIST')", {}, sperr)
        halter.wait(timeout=10)
        pruefe("Verhalten: aktivierung_setzen mit Frist setzt keine Marke",
               "FRIST" in r.stdout and not (sperr / "AKTIVIERUNG").exists())
    return "geprueft"


SCHREIBSCHUTZ_CODE = textwrap.dedent("""
    import os, sys
    import shared.supabase_client as sc
    from shared.produktionssperre import Gesperrt, produktion
    class Q:
        def __init__(s, n): s.n = n
        def __getattr__(s, a):
            return lambda *x, **k: s
        def execute(s):
            if os.environ.get("SCHLAF"):
                print("AUSFUEHRUNG", flush=True); import time; time.sleep(float(os.environ["SCHLAF"]))
            return type("R", (), {"data": []})()
    class Fake:
        def table(s, n): return Q(n)
        def rpc(s, n, *a, **k): return Q(n)
    sc.create_client = lambda u, k: Fake()
    os.environ.update(SUPABASE_URL="http://127.0.0.1:9", SUPABASE_KEY="x")
    c = sc.get_client(force_new=True)
    def versuch(name, fn):
        try:
            fn(); print(name, "FREI")
        except Gesperrt:
            print(name, "GESPERRT")
    def alle():
        versuch("prices.upsert", lambda: c.table("prices").upsert([]).execute())
        versuch("tdom_stats.delete", lambda: c.table("tdom_stats").delete().eq("x", 1).execute())
        versuch("prices.select", lambda: c.table("prices").select("*").execute())
        versuch("polymarket_prices.insert", lambda: c.table("polymarket_prices").insert({}).execute())
        versuch("rpc.stress_lauf_starten", lambda: c.rpc("stress_lauf_starten", {}).execute())
        versuch("rpc.search_tickers", lambda: c.rpc("search_tickers", {}).execute())
    if sys.argv[1] == "abnahme":
        with produktion("abnahme:schreibschutz"):
            alle()
    elif sys.argv[1] == "spaet":
        # Anfrage OHNE Marke aufbauen, dann Aktivierung setzen, dann ausführen
        q = c.table("prices").upsert([]).eq("ticker", "SPY")
        open(os.path.join(os.environ["SA_SPERR_DIR"], "AKTIVIERUNG"), "w").write("k-spaet\\n")
        versuch("spaet.execute", lambda: q.execute())
    elif sys.argv[1] == "lang":
        c.table("prices").upsert([]).execute()
        print("FERTIG", flush=True)
    else:
        alle()
""")


def schreibschutz():
    with tempfile.TemporaryDirectory() as t:
        sperr = pathlib.Path(t)
        r = lauf_probe(SCHREIBSCHUTZ_CODE, {}, sperr, ["import"])
        pruefe("Schreibschutz: ohne Marke ist alles frei",
               r.returncode == 0 and r.stdout.count("FREI") == 6, r.stderr[-200:])
        (sperr / "AKTIVIERUNG").write_text("k-s\n", encoding="utf-8")
        r = lauf_probe(SCHREIBSCHUTZ_CODE, {}, sperr, ["import"])
        zeilen = dict(z.split() for z in r.stdout.splitlines() if z.count(" ") == 1)
        soll = {"prices.upsert": "GESPERRT", "tdom_stats.delete": "GESPERRT", "prices.select": "FREI",
                "polymarket_prices.insert": "FREI", "rpc.stress_lauf_starten": "GESPERRT", "rpc.search_tickers": "FREI"}
        pruefe("Schreibschutz: Import-Einstieg bei Marke — geschützt gesperrt, Rest frei", zeilen == soll,
               "%s" % zeilen if zeilen != soll else "")
        r = lauf_probe(SCHREIBSCHUTZ_CODE, {"SA_AKTIVIERUNG": "k-s"}, sperr, ["abnahme"])
        zeilen = dict(z.split() for z in r.stdout.splitlines() if z.count(" ") == 1)
        pruefe("Schreibschutz: lesende Freigabe (Abnahme) schreibt nicht", zeilen == soll,
               "%s" % zeilen if zeilen != soll else "")
        (sperr / "AKTIVIERUNG").unlink()
        r = lauf_probe(SCHREIBSCHUTZ_CODE, {}, sperr, ["spaet"])
        pruefe("Schreibschutz: vor der Aktivierung aufgebaute Anfrage wird danach nicht ausgeführt",
               "spaet.execute GESPERRT" in r.stdout,
               "" if "spaet.execute GESPERRT" in r.stdout else (r.stdout + r.stderr)[-200:])
        (sperr / "AKTIVIERUNG").unlink()
        if ps.fcntl is None:
            ERGEBNIS.append("UNGEPRÜFT [Schreibschutz: laufende Ausführung hält aktivierung_setzen auf] kein fcntl")
            return
        env = {**os.environ, "SA_SPERR_DIR": str(sperr), "PYTHONPATH": str(WURZEL), "SCHLAF": "1.5",
               "SA_SPERRE_KEIN_DB_NACHWEIS": "1"}
        env.pop("SA_AKTIVIERUNG", None)
        schreiber = subprocess.Popen([sys.executable, "-c", SCHREIBSCHUTZ_CODE, "lang"], stdout=subprocess.PIPE,
                                     text=True, env=env)
        schreiber.stdout.readline()          # „AUSFUEHRUNG": execute läuft (unter dem Lock)
        t0 = time.time()
        r = lauf_probe("from shared.produktionssperre import aktivierung_setzen; aktivierung_setzen('k-lang')", {}, sperr)
        warte = time.time() - t0
        schreiber.wait(timeout=10)
        pruefe("Schreibschutz: laufende Ausführung hält aktivierung_setzen auf", r.returncode == 0 and warte >= 1.0,
               "%.2f s" % warte)


def echte_skripte():
    with tempfile.TemporaryDirectory() as t:
        kopie = isolierte_kopie(WURZEL, pathlib.Path(t) / "baum")
        sperr = pathlib.Path(t) / "sperre"
        sperr.mkdir()
        (sperr / "AKTIVIERUNG").write_text("k-echt\n", encoding="utf-8")
        def stand():
            # Pfad → Inhalt-Hash: erkennt neue UND überschriebene Dateien (der Kalenderbauer überschreibt eine
            # bestehende market_calendar.json — ein Vergleich nur auf neue Dateien sah das nicht).
            import hashlib
            return {str(p.relative_to(kopie)): hashlib.sha256(p.read_bytes()).hexdigest()
                    for p in kopie.rglob("*")
                    if p.is_file() and "__pycache__" not in p.parts
                    and p.relative_to(kopie).parts[0] != "logs"}      # Logger legt beim Import Logdateien an
        vorher = stand()
        gesperrt, nicht_hier = 0, []
        # ABGESCHOTTET: läuft ein Skript wegen eines Defekts doch an, darf es nichts erreichen — keine Datenbank,
        # kein Mailversand, kein Netz (alle Proxys auf einen toten Port), harte Frist, und es läuft in einer Kopie:
        # Dateiausgaben landen im Temp-Baum, nie im Projekt.
        env = {**os.environ, "SA_SPERR_DIR": str(sperr), "PYTHONUTF8": "1", "SA_SPERRE_KEIN_DB_NACHWEIS": "1",
               "SUPABASE_URL": "http://127.0.0.1:9", "SUPABASE_KEY": "abgeschottet",
               "SUPABASE_SERVICE_ROLE_KEY": "abgeschottet", "BREVO_API_KEY": "", "brevo_api_key": "",
               "HTTP_PROXY": "http://127.0.0.1:9", "HTTPS_PROXY": "http://127.0.0.1:9",
               "http_proxy": "http://127.0.0.1:9", "https_proxy": "http://127.0.0.1:9", "NO_PROXY": "",
               "PYTHONPATH": str(kopie)}
        env.pop("SA_AKTIVIERUNG", None)
        for name in sorted(ps.PFLICHT):
            for art, befehl in (("Datei", [str(kopie / "scripts" / name)]), ("-m", ["-m", "scripts." + name[:-3]]),
                                ("Import", ["-c", "import scripts.%s" % name[:-3]])):
                try:
                    r = subprocess.run([sys.executable, *befehl], capture_output=True, text=True, env=env, timeout=30,
                                       cwd=str(kopie))
                except subprocess.TimeoutExpired:
                    pruefe("Echt: %s (%s) endet mit Exit 75" % (name, art), False, "lief ohne Sperre an (Frist 30 s)")
                    continue
                if r.returncode == 75:
                    gesperrt += 1
                elif "ModuleNotFoundError" in r.stderr or "ImportError" in r.stderr:
                    nicht_hier.append("%s(%s)" % (name, art))
                else:
                    pruefe("Echt: %s (%s) endet mit Exit 75" % (name, art), False,
                           "Exit %s: %s" % (r.returncode, r.stderr[-200:]))
        nachher = stand()
        neu = sorted(k for k in nachher if vorher.get(k) != nachher[k]) + sorted(k for k in vorher if k not in nachher)
        pruefe("Echt: gesperrte Läufe erzeugen keine Ausgabedateien", not neu, neu[:5])
        pruefe("Echt: ausführbare Pflicht-Skripte enden bei Marke mit 75 (Datei, -m, Import)", gesperrt >= 3,
               "%d mit 75, nicht ausführbar hier: %s" % (gesperrt, nicht_hier))


# Workflows, die ein Pflicht-Skript starten, ohne 75 abzubilden — mit Grund.
WORKFLOW_AUSNAHMEN = {
    "deploy.yml": "generate_decade_data läuft mit `|| echo …übersprungen` (jeder Exit ist dort bereits nicht fatal)",
}


def betrieb():
    it = (WURZEL / "deploy" / "install_timers.sh").read_text(encoding="utf-8")
    m = it.find("logs/sperre/AKTIVIERUNG")
    s3 = it.find("# 3) Aktivieren")
    pruefe("Betrieb: install_timers.sh prüft die Marke vor dem Starten", 0 <= m < s3 and "exit 0" in it[m:s3])
    dy = (WURZEL / ".github" / "workflows" / "deploy.yml").read_text(encoding="utf-8")
    pruefe("Betrieb: deploy.yml überspringt [ohne-deploy]",
           "if: ${{ !contains(github.event.head_commit.message, '[ohne-deploy]') }}" in dy)
    for unit in ("sa-nightly.service", "sa-intraday.service"):
        u = (WURZEL / "deploy" / "systemd" / unit).read_text(encoding="utf-8")
        pruefe("Betrieb: %s wertet 75 als Erfolg" % unit, re.search(r"(?m)^SuccessExitStatus=75\s*$", u) is not None)
    namen = "|".join(re.escape(n[:-3]) for n in ps.PFLICHT)
    for wf in sorted((WURZEL / ".github" / "workflows").glob("*.yml")):
        q = wf.read_text(encoding="utf-8")
        startet = re.search(r"(?:docker (?:compose )?exec[^\n]*scripts/(?:%s)\.py)|(?:for s in [^\n]*\b(?:%s)\b)"
                            % (namen, namen), q)
        if not startet or wf.name in WORKFLOW_AUSNAHMEN:
            continue
        # 75 → Erfolg: entweder `rc=0` in derselben Zeile oder (Schleife) 75 getrennt vom Fehlerzweig `elif … != 0`
        bildet = (re.search(r'\[ "\$(rc|RC)" = 75 \]; then[^\n]*(rc|RC)=0', q) is not None
                  or re.search(r'\[ "\$rc" = 75 \]; then[^\n]*\n\s*elif \[ "\$rc" != 0 \]; then[^\n]*fail=1', q) is not None)
        pruefe("Betrieb: %s bildet Exit 75 auf Erfolg ab" % wf.name, bildet)
    fl = (WURZEL / ".github" / "workflows" / "flows_update.yml").read_text(encoding="utf-8")
    pruefe("Betrieb: flows_update.yml nimmt unterdrückte Panels aus der Frischeprüfung",
           re.search(r'= 75 \]; then[^\n]*; continue\n', fl) is not None
           and 'pruefen+=("${s#build_}.json")' in fl
           and 'check_flows_freshness.py --files "${pruefen[@]}"' in fl
           and re.search(r"check_flows_freshness\.py(?! --files)", fl) is None)


def main():
    inventar()
    einbau()
    stand = verhalten()
    schreibschutz()
    echte_skripte()
    betrieb()
    for e in ERGEBNIS:
        sys.stdout.write(e + "\n")
    streng = os.environ.get("SA_SPERRE_STRENG") == "1"     # Deploy-Gate (Linux): Lock-Prüfung ist Pflicht
    if streng and stand != "geprueft":
        sys.stdout.write("FEHL [Verhalten: exklusiver Lock] im strengen Modus nicht geprüft\n")
        return 1
    n = sum(1 for e in ERGEBNIS if e.startswith(("ok", "FEHL")))
    sys.stdout.write("verify_produktionssperre: %s (%d Prüfungen)\n" % ("BESTANDEN" if OK else "DURCHGEFALLEN", n))
    if OK:
        sys.stdout.write("PROBE-ENDE %d Pruefungen\n" % n)
    return 0 if OK else 1


if __name__ == "__main__":
    sys.exit(main())
