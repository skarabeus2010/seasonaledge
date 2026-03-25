"""
SeasonAlpha — shared/logger.py
================================
Zentrales Logging-Modul für alle Module und Pages.

3 Kanäle:
  app_logger    → logs/app.log    (INFO+)  — allgemeine Events
  error_logger  → logs/error.log  (ERROR+) — Exceptions + Tracebacks
  access_logger → logs/access.log (INFO+)  — Logins, Seitenaufrufe, Ticker

Verwendung:
    from shared.logger import app_logger, error_logger, access_logger

    app_logger.info(f"Download gestartet: {ticker}")
    error_logger.error(f"Download fehlgeschlagen: {ticker}", exc_info=True)
    access_logger.info(f"LOGIN | user={email} | ip={ip} | status=success")

WICHTIG:
    - Niemals print() für Debugging — immer logger verwenden
    - Niemals Passwörter, API-Keys oder Token in Logs schreiben
    - logs/ ist in .gitignore — niemals committen
"""

import logging
import os
import pathlib
from logging.handlers import RotatingFileHandler

# ── Log-Verzeichnis ────────────────────────────────────────────────────────────
# Liegt im Projekt-Root (eine Ebene über shared/)
_HERE = pathlib.Path(__file__).resolve().parent          # shared/
_PROJECT_ROOT = _HERE.parent                             # Saisonalcharts/
LOG_DIR = _PROJECT_ROOT / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)

# ── Format ─────────────────────────────────────────────────────────────────────
_FMT = "%(asctime)s | %(levelname)-8s | %(name)-24s | %(message)s"
_DATE_FMT = "%Y-%m-%d %H:%M:%S"

# ── Rotation: 5 MB pro Datei, max. 5 Backups (= 30 MB pro Kanal) ──────────────
_MAX_BYTES = 5 * 1024 * 1024
_BACKUP_COUNT = 5


def _build_logger(name: str, filename: str, level: int) -> logging.Logger:
    """Erstellt einen benannten Logger mit RotatingFileHandler + Console-Handler."""
    logger = logging.getLogger(name)

    # Verhindert doppelte Handler wenn das Modul mehrfach importiert wird
    if logger.handlers:
        return logger

    logger.setLevel(logging.DEBUG)  # Logger selbst alles durchlassen — Handler filtern

    # ── File Handler (rotierend) ───────────────────────────────────────────────
    fh = RotatingFileHandler(
        LOG_DIR / filename,
        maxBytes=_MAX_BYTES,
        backupCount=_BACKUP_COUNT,
        encoding="utf-8",
    )
    fh.setLevel(level)
    fh.setFormatter(logging.Formatter(_FMT, datefmt=_DATE_FMT))
    logger.addHandler(fh)

    # ── Console Handler (nur WARNING+ damit Streamlit-UI nicht zumüllt) ────────
    ch = logging.StreamHandler()
    ch.setLevel(logging.WARNING)
    ch.setFormatter(logging.Formatter(_FMT, datefmt=_DATE_FMT))
    logger.addHandler(ch)

    # Verhindert Weitergabe an Root-Logger (würde doppelt loggen)
    logger.propagate = False

    return logger


# ── Die 3 öffentlichen Logger ──────────────────────────────────────────────────

app_logger = _build_logger(
    name="seasonaledge.app",
    filename="app.log",
    level=logging.INFO,
)
"""Allgemeines App-Log: Downloads, Berechnungen, App-Events."""

error_logger = _build_logger(
    name="seasonaledge.error",
    filename="error.log",
    level=logging.ERROR,
)
"""Fehler-Log: Exceptions, Tracebacks, kritische Zustände. Immer exc_info=True übergeben."""

access_logger = _build_logger(
    name="seasonaledge.access",
    filename="access.log",
    level=logging.INFO,
)
"""Zugriffs-Log: Logins, Logouts, Seitenaufrufe, Ticker-Anfragen."""


# ── Hilfsfunktionen ────────────────────────────────────────────────────────────

def log_login(email: str, ip: str = "unknown", success: bool = True) -> None:
    """Loggt einen Login-Versuch."""
    status = "success" if success else "failed"
    access_logger.info(f"LOGIN  | user={email} | ip={ip} | status={status}")


def log_logout(email: str) -> None:
    """Loggt einen Logout."""
    access_logger.info(f"LOGOUT | user={email}")


def log_page(email: str, page: str, ticker: str = "") -> None:
    """Loggt einen Seitenaufruf."""
    ticker_part = f" | ticker={ticker}" if ticker else ""
    access_logger.info(f"PAGE   | user={email} | page={page}{ticker_part}")


def log_download(ticker: str, source: str, rows: int, duration_ms: float) -> None:
    """Loggt einen abgeschlossenen Daten-Download."""
    app_logger.info(
        f"DOWNLOAD | ticker={ticker} | source={source} | "
        f"rows={rows} | duration={duration_ms:.0f}ms"
    )


def log_error(module: str, message: str, exc: Exception | None = None) -> None:
    """Loggt einen Fehler mit optionalem Traceback."""
    if exc is not None:
        error_logger.error(f"{module} | {message}", exc_info=exc)
    else:
        error_logger.error(f"{module} | {message}")


def log_supabase(operation: str, table: str, rows: int = 0) -> None:
    """Loggt eine Supabase-Datenbankoperation."""
    app_logger.info(f"SUPABASE | op={operation} | table={table} | rows={rows}")


def log_ai(model: str, ticker: str, duration_ms: float) -> None:
    """Loggt einen KI-Modell-Aufruf."""
    app_logger.info(f"AI     | model={model} | ticker={ticker} | duration={duration_ms:.0f}ms")


# ── Startup-Message ────────────────────────────────────────────────────────────
app_logger.info("=" * 60)
app_logger.info("SeasonAlpha gestartet")
app_logger.info(f"Log-Verzeichnis: {LOG_DIR}")
app_logger.info("=" * 60)
