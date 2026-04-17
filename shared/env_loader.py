"""
shared/env_loader.py — lädt .env aus dem Projekt-Root in os.environ.

Worktree-safe: sucht .env beginnend bei diesem Modul und geht bis zu 6 Ebenen
hoch. Damit findet der Loader das .env des Main-Repos auch aus einem
.claude/worktrees/<name>/ Worktree heraus.

Keine externe Dependency (kein python-dotenv nötig).
"""
from __future__ import annotations

import os
import pathlib


def _find_dotenv() -> pathlib.Path | None:
    """Gehe vom aktuellen File aus nach oben bis eine .env gefunden wird."""
    start = pathlib.Path(__file__).resolve().parent
    for up in range(7):
        if up >= len(start.parents):
            break
        candidate = start.parents[up] / ".env"
        if candidate.is_file():
            return candidate
    return None


def _parse_line(line: str) -> tuple[str, str] | None:
    """
    Einzelne .env-Zeile parsen. Erlaubt KEY=VALUE, optional mit Anführungszeichen.
    Ignoriert Leerzeilen, Kommentare (# ...), und Zeilen ohne =.
    """
    s = line.strip()
    if not s or s.startswith("#"):
        return None
    if "=" not in s:
        return None
    key, _, val = s.partition("=")
    key = key.strip()
    val = val.strip()
    # Einfache Quoting-Behandlung
    if len(val) >= 2 and val[0] == val[-1] and val[0] in ("'", '"'):
        val = val[1:-1]
    if not key:
        return None
    return key, val


def load_env(override: bool = False) -> int:
    """
    Liest .env aus dem Projekt-Root und setzt die Einträge in os.environ.

    Args:
        override: wenn True, überschreibt bereits gesetzte Env-Vars. Default
                  False → bestehende Env-Vars (z.B. vom Docker-Host) gewinnen.

    Returns:
        Anzahl der gesetzten Keys (0 wenn .env nicht existiert).
    """
    path = _find_dotenv()
    if not path:
        return 0

    count = 0
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            parsed = _parse_line(line)
            if not parsed:
                continue
            key, val = parsed
            if override or key not in os.environ:
                os.environ[key] = val
                count += 1
    return count


__all__ = ["load_env"]
