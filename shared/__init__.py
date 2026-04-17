# SeasonAlpha - Shared Modules
# .env aus Projekt-Root automatisch laden (für lokale Dev-Scripts und Tests)
from shared.env_loader import load_env as _load_env
_load_env()
