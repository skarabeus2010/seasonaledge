"""
SeasonalEdge — Zentrales Logging-Modul

3 Kanäle:
  app_logger    → logs/app.log      (INFO + WARNING)
  error_logger  → logs/error.log    (ERROR + CRITICAL)
  access_logger → logs/access.log   (INFO: Logins, Seitenaufrufe)

Verwendung:
  from shared.logger import app_logger, error_logger, access_logger
  app_logger.info(f"Download gestartet: {ticker}")
  error_logger.error(f"Download fehlgeschlagen: {ticker}", exc_info=True)
  access_logger.info(f"PAGE | user={email} | page=Yearly_Seasonals")
"""

import logging
import os
from logging.handlers import RotatingFileHandler

LOG_DIR = os.path.join(os.path.dirname(__file__), "..", "logs")
os.makedirs(LOG_DIR, exist_ok=True)

_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
_DATEFMT = "%Y-%m-%d %H:%M:%S"


def _make_handler(filename: str, level: int) -> RotatingFileHandler:
    h = RotatingFileHandler(
        os.path.join(LOG_DIR, filename),
        maxBytes=5 * 1024 * 1024,  # 5 MB
        backupCount=5,
        encoding="utf-8",
    )
    h.setLevel(level)
    h.setFormatter(logging.Formatter(_FORMAT, datefmt=_DATEFMT))
    return h


# ── App Logger (INFO + WARNING) ─────────────────────────────
app_logger = logging.getLogger("seasonaledge.app")
app_logger.setLevel(logging.INFO)
app_logger.addHandler(_make_handler("app.log", logging.INFO))

# ── Error Logger (ERROR + CRITICAL) ─────────────────────────
error_logger = logging.getLogger("seasonaledge.error")
error_logger.setLevel(logging.ERROR)
error_logger.addHandler(_make_handler("error.log", logging.ERROR))

# ── Access Logger (INFO: Logins, Seitenaufrufe, Ticker) ─────
access_logger = logging.getLogger("seasonaledge.access")
access_logger.setLevel(logging.INFO)
access_logger.addHandler(_make_handler("access.log", logging.INFO))
