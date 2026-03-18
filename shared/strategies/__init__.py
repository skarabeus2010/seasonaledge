# shared/strategies/__init__.py
# Zentraler Export für alle Saisonalstrategien
# Import-Beispiel in einer Page:
#   from shared.strategies import STRATEGIES, get_strategies_by_category
#   from shared.strategies import januar_trifecta, kaeppel

from shared.strategies.definitions import (
    STRATEGIES,
    get_strategies_by_category,
    get_strategies_by_strength,
    KATEGORIEN,
    STAERKEN,
)

from shared.strategies import januar_trifecta
from shared.strategies import kaeppel

__all__ = [
    "STRATEGIES",
    "get_strategies_by_category",
    "get_strategies_by_strength",
    "KATEGORIEN",
    "STAERKEN",
    "januar_trifecta",
    "kaeppel",
]
