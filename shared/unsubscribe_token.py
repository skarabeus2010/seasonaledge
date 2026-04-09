"""
shared/unsubscribe_token.py — HMAC-Token-Generierung für Unsubscribe-Links

Der Token verhindert, dass jemand beliebige E-Mail-Adressen per URL-Parameter
abmelden kann (CSRF-Schutz). Das Secret liegt server-side in der Env-Var
UNSUBSCRIBE_SECRET und wird vom Weekly-Newsletter-Script zum Generieren,
von der Supabase-RPC `unsubscribe_with_token` zum Validieren benutzt.

ACHTUNG: Hash-Algorithmus (SHA-256) + Secret + Länge (16 hex chars) müssen
identisch sein in:
  - shared/unsubscribe_token.py (hier, für Generierung im Newsletter)
  - scripts/create_unsubscribe_rpc.sql (PostgreSQL-Funktion, für Validierung)

Wird das Secret gedreht, müssen alte Unsubscribe-Links weiter funktionieren
oder die Nutzer erhalten einen ungültigen Link. Für die erste Version:
Secret NICHT drehen, oder Grace-Period einplanen.
"""
from __future__ import annotations

import hashlib
import os
from urllib.parse import quote


DEFAULT_SECRET = "seasonaledge-unsub-2026"
DEFAULT_BASE_URL = "https://seasonalpha.ai"
TOKEN_LENGTH = 16


def _get_secret() -> str:
    """Secret aus Env-Var oder Fallback."""
    return os.environ.get("UNSUBSCRIBE_SECRET", DEFAULT_SECRET)


def generate_unsubscribe_token(email: str) -> str:
    """
    Generiert einen HMAC-artigen Token für die gegebene E-Mail.

    Format: erste 16 Hex-Zeichen von SHA-256(email.lower() + secret)
    """
    normalized = email.strip().lower()
    secret = _get_secret()
    digest = hashlib.sha256(f"{normalized}{secret}".encode("utf-8")).hexdigest()
    return digest[:TOKEN_LENGTH]


def validate_token(email: str, token: str) -> bool:
    """
    Prüft ob Token zu E-Mail passt.

    Hinweis: Das wird auch serverseitig in der Supabase-RPC geprüft —
    diese Funktion ist primär für lokale Tests / Debugging.
    """
    return generate_unsubscribe_token(email) == (token or "").strip().lower()


def generate_unsubscribe_url(
    email: str,
    base_url: str = DEFAULT_BASE_URL,
) -> str:
    """
    Baut einen kompletten Unsubscribe-Link für die E-Mail.

    Beispiel:
        https://seasonalpha.ai/unsubscribe?email=max%40mustermann.de&token=a1b2c3d4e5f6g7h8
    """
    token = generate_unsubscribe_token(email)
    encoded_email = quote(email.strip().lower())
    return f"{base_url}/unsubscribe?email={encoded_email}&token={token}"


if __name__ == "__main__":
    # Quick self-test: py shared/unsubscribe_token.py test@example.com
    import sys
    test_email = sys.argv[1] if len(sys.argv) > 1 else "test@example.com"
    tok = generate_unsubscribe_token(test_email)
    url = generate_unsubscribe_url(test_email)
    print(f"Email: {test_email}")
    print(f"Token: {tok}")
    print(f"URL:   {url}")
    print(f"Valid: {validate_token(test_email, tok)}")
