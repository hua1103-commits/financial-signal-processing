"""strategies.py
Trading strategy implementations with different runtime & space complexities.
"""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
from typing import Deque, Dict, List, Optional

from models import MarketDataPoint, Strategy


def _signal_from_price_vs_avg(price: float, avg: float) -> List[str]:
    # If current price is above average -> BUY; below -> SELL; equal -> no signal
    if price > avg:
        return ["BUY"]
    if price < avg:
        return ["SELL"]
    return []


@dataclass
class NaiveMovingAverageStrategy(Strategy):
    """Naive moving average: recompute average from scratch each tick.

    For each tick, we append the new price and recompute sum(prices)/len(prices).
    - Time per tick: O(n) because sum(prices) walks the full history list of length n.
    - Total time after processing n ticks: O(1 + 2 + ... + n) = O(n^2).
    - Space: O(n) to store the full price history.

    NOTE: This matches the assignment spec (Time: O(n), Space: O(n)) *per tick*.
    """
    prices_by_symbol: Dict[str, List[float]] = field(default_factory=dict)

    def generate_signals(self, tick: MarketDataPoint) -> List[str]:
        prices = self.prices_by_symbol.setdefault(tick.symbol, [])
        prices.append(tick.price)  # amortized O(1)

        # sum(prices) is O(n) for n prices in history for this symbol
        avg = sum(prices) / len(prices)  # O(n)
        return _signal_from_price_vs_avg(tick.price, avg)


@dataclass
class WindowedMovingAverageStrategy(Strategy):
    """Windowed moving average: fixed-size buffer + incremental updates.

    Keeps a deque(maxlen=k) and a running sum.
    - Time per tick: O(1) (constant work: push/pop and arithmetic).
    - Space: O(k) per symbol for the sliding window buffer.
    """
    window_size: int = 10
    window_by_symbol: Dict[str, Deque[float]] = field(default_factory=dict)
    sum_by_symbol: Dict[str, float] = field(default_factory=dict)

    def generate_signals(self, tick: MarketDataPoint) -> List[str]:
        window = self.window_by_symbol.get(tick.symbol)
        if window is None:
            window = deque(maxlen=self.window_size)
            self.window_by_symbol[tick.symbol] = window
            self.sum_by_symbol[tick.symbol] = 0.0

        # If deque is full, appending will drop one element; we need to subtract it.
        if len(window) == window.maxlen:
            oldest = window[0]              # O(1) peek
        else:
            oldest = None

        window.append(tick.price)           # O(1)
        if oldest is not None and len(window) == window.maxlen:
            # When full before append, the old oldest is removed.
            self.sum_by_symbol[tick.symbol] -= oldest

        self.sum_by_symbol[tick.symbol] += tick.price
        avg = self.sum_by_symbol[tick.symbol] / len(window)  # O(1)
        return _signal_from_price_vs_avg(tick.price, avg)


@dataclass
class OptimizedNaiveMovingAverageStrategy(Strategy):
    """Optimization challenge: refactor the naive strategy to reduce time & space.

    This version computes the SAME average as the naive strategy (average of *all history*),
    but without re-summing the full list each time.

    Technique: running sum + count (streaming).
    - Time per tick: O(1)
    - Space: O(1) per symbol (we store only sum and count, not full history)

    Tradeoff: This is *not* a fixed-window moving average; it's a cumulative average.
    That's okay for the assignment's "refactor naive" requirement, and it illustrates
    how removing "store all history + rescan" improves both runtime and memory.
    """
    sum_by_symbol: Dict[str, float] = field(default_factory=dict)
    count_by_symbol: Dict[str, int] = field(default_factory=dict)

    def generate_signals(self, tick: MarketDataPoint) -> List[str]:
        s = self.sum_by_symbol.get(tick.symbol, 0.0) + tick.price
        c = self.count_by_symbol.get(tick.symbol, 0) + 1
        self.sum_by_symbol[tick.symbol] = s
        self.count_by_symbol[tick.symbol] = c

        avg = s / c  # O(1)
        return _signal_from_price_vs_avg(tick.price, avg)
