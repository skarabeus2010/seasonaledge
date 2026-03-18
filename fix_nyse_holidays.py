"""
Einmalig ausführen:
py fix_nyse_holidays.py
"""
import pathlib
from datetime import timedelta

f = pathlib.Path("shared/nyse_holidays.py")
content = f.read_text(encoding="utf-8")

additions = []

if "_easter_monday" not in content:
    additions.append("""
def _easter_monday(year: int):
    \"\"\"Ostermontag = Ostersonntag + 1 Tag.\"\"\"
    return _easter_sunday(year) + timedelta(days=1)
""")

if "_whit_monday" not in content:
    additions.append("""
def _whit_monday(year: int):
    \"\"\"Pfingstmontag = Ostersonntag + 49 Tage.\"\"\"
    return _easter_sunday(year) + timedelta(days=49)
""")

if "_ascension_day" not in content:
    additions.append("""
def _ascension_day(year: int):
    \"\"\"Christi Himmelfahrt = Ostersonntag + 39 Tage.\"\"\"
    return _easter_sunday(year) + timedelta(days=39)
""")

if additions:
    # timedelta Import sicherstellen
    if "from datetime import" in content and "timedelta" not in content:
        content = content.replace(
            "from datetime import date",
            "from datetime import date, timedelta"
        )
    elif "import datetime" in content and "timedelta" not in content:
        content += "\nfrom datetime import timedelta\n"

    content += "\n" + "\n".join(additions)
    f.write_text(content, encoding="utf-8")
    print(f"✅ {len(additions)} Funktionen hinzugefügt: _easter_monday, _whit_monday, _ascension_day")
else:
    print("✅ Alle Funktionen bereits vorhanden.")

# Verifikation
import importlib.util
spec = importlib.util.spec_from_file_location("nyse_holidays", f)
mod  = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
print("Verfügbare Funktionen:", [x for x in dir(mod) if x.startswith("_") and "easter" in x or "monday" in x or "whit" in x])
