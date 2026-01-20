"""models.py
Core data models and the Strategy interface.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import List


@dataclass(frozen=True)
class MarketDataPoint:
    """Immutable tick (timestamp, symbol, price).

    Space: O(1) per tick (but stored in a list becomes O(n) overall).
    """
    timestamp: datetime
    symbol: str
    price: float


class Strategy(ABC):
    """Strategy interface for streaming signal generation."""

    @abstractmethod
    def generate_signals(self, tick: MarketDataPoint) -> List[str]:
        """Process one tick and return zero or more signals (e.g., ["BUY"], ["SELL"], [])."""
        raise NotImplementedError
