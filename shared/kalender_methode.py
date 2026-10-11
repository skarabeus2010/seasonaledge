"""Lesermethode der Kalender-Umstellung (docs/KALENDER_UMSTELLUNG.md, Plan v3 §1; Gegenstück zu landing/js/methode.js).

- LESER: was Seiten, Mails und Python-Leser anzeigen. Wird je Berechnung EINMAL gelesen und als Argument
  weitergereicht. Konstante — Produktion ist nicht über die Umgebung umschaltbar; Tests übergeben die Methode als
  Argument.
- Produktionsmethode (was ein Statistiklauf erzeugt) ist ein Argument des Laufs, nicht diese Konstante.

Gewechselt wird nur in V9 (Aktivierung), gemeinsam mit `SA.kalenderMethode` in landing/js/methode.js; der
Einbindungswächter verlangt, dass beide übereinstimmen.
"""
from __future__ import annotations

METHODEN = ("alt", "kalender_v1")
LESER = "alt"


def pruefe(methode: str) -> str:
    """Gibt `methode` zurück, wenn sie bekannt ist, sonst ValueError (kein stiller Rückfall)."""
    if methode not in METHODEN:
        raise ValueError("unbekannte Kalendermethode %r (erlaubt: %s)" % (methode, ", ".join(METHODEN)))
    return methode
