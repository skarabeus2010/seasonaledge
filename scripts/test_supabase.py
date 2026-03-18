"""
Schnelltest: Supabase-Verbindung prüfen und Testdaten einfügen.
Aufruf: py scripts/test_supabase.py
"""

import os
import sys
import pathlib

# Projekt-Root in sys.path
project_dir = str(pathlib.Path(__file__).resolve().parent.parent)
sys.path.insert(0, project_dir)

# Secrets laden (für lokale Entwicklung)
secrets_path = os.path.join(project_dir, ".streamlit", "secrets.toml")
if os.path.exists(secrets_path):
    import tomllib
    with open(secrets_path, "rb") as f:
        secrets = tomllib.load(f)
    for key, value in secrets.items():
        os.environ.setdefault(key, value)

from shared.supabase_client import get_client


def main():
    print("🔌 Verbinde mit Supabase...")
    try:
        client = get_client()
        print("✅ Verbindung erfolgreich!")
    except Exception as e:
        print(f"❌ Verbindung fehlgeschlagen: {e}")
        return

    # Test: Tabellen abfragen
    print("\n📊 Prüfe Tabellen...")
    for table in ["prices", "seasonality", "app_logs"]:
        try:
            result = client.table(table).select("*").limit(1).execute()
            print(f"  ✅ {table}: OK ({len(result.data)} Zeilen)")
        except Exception as e:
            print(f"  ❌ {table}: {e}")

    # Test: Log-Eintrag schreiben
    print("\n📝 Schreibe Test-Log...")
    try:
        from shared.supabase_client import log_to_db
        log_to_db("INFO", "test", "Supabase-Verbindungstest erfolgreich")
        print("  ✅ Log geschrieben!")

        # Verifizieren
        result = client.table("app_logs").select("*").order(
            "created_at", desc=True
        ).limit(1).execute()
        if result.data:
            print(f"  📋 Letzter Log: {result.data[0]['message']}")
    except Exception as e:
        print(f"  ❌ Log fehlgeschlagen: {e}")

    print("\n🎉 Supabase ist bereit!")


if __name__ == "__main__":
    main()
