"""
Einmalig ausführen um Streamlit-Cache zu löschen:
py clear_cache.py
"""
import shutil, os, pathlib

# Streamlit Cache-Ordner finden und löschen
cache_dirs = [
    pathlib.Path.home() / ".streamlit" / "cache",
    pathlib.Path(".streamlit") / "cache",
    pathlib.Path("__pycache__"),
    pathlib.Path("shared") / "__pycache__",
    pathlib.Path("pages") / "__pycache__",
]

for d in cache_dirs:
    if d.exists():
        shutil.rmtree(d)
        print(f"Gelöscht: {d}")
    else:
        print(f"Nicht gefunden: {d}")

# Streamlit's eigenen Cache-Ordner
import tempfile
tmp = pathlib.Path(tempfile.gettempdir())
for d in tmp.glob("streamlit*"):
    try:
        shutil.rmtree(d)
        print(f"Gelöscht: {d}")
    except:
        pass

print("\nCache geleert! Jetzt App neu starten.")
