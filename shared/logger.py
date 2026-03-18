"""
shared/logger.py — Zentrales Logging für SeasonalEdge

3 Log-Kanäle:
  app.log    — INFO + WARNING: App-Events (Starts, Downloads, Berechnungen)
  error.log  — ERROR + CRITICAL: Exceptions + Tracebacks
  access.log — INFO: Logins, Seitenaufrufe, Ticker-Anfragen
"""
import logging
import os
from logging.handlers import RotatingFileHandler

LOG_DIR = os.path.join(os.path.dirname(__file__), "..", "logs")
os.makedirs(LOG_DIR, exist_ok=True)

_FMT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
_DATEFMT = "%Y-%m-%d %H:%M:%S"


def _make_handler(filename: str, level: int) -> RotatingFileHandler:
    h = RotatingFileHandler(
        os.path.join(LOG_DIR, filename),
        maxBytes=5 * 1024 * 1024,  # 5 MB
        backupCount=5,
    )
    h.setLevel(level)
    h.setFormatter(logging.Formatter(_FMT, datefmt=_DATEFMT))
    return h


# ── Logger-Instanzen ────────────────────────────────

app_logger = logging.getLogger("seasonaledge.app")
app_logger.setLevel(logging.INFO)
app_logger.addHandler(_make_handler("app.log", logging.INFO))

error_logger = logging.getLogger("seasonaledge.error")
error_logger.setLevel(logging.ERROR)
error_logger.addHandler(_make_handler("error.log", logging.ERROR))

access_logger = logging.getLogger("seasonaledge.access")
access_logger.setLevel(logging.INFO)
access_logger.addHandler(_make_handler("access.log", logging.INFO))


def log_to_supabase(level: str, channel: str, message: str, user_email: str = None):
    """Optional: Logs auch in Supabase schreiben (für Streamlit Cloud)."""
    try:
        from shared.supabase_client import insert_log
        insert_log(level, channel, message, user_email)
    except Exception:
        pass  # DB-Logging ist nice-to-have, nie crashen
