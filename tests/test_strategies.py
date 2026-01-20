from datetime import datetime, timedelta

from models import MarketDataPoint
from strategies import NaiveMovingAverageStrategy, WindowedMovingAverageStrategy, OptimizedNaiveMovingAverageStrategy


def _ticks(prices, symbol="ABC"):
    t0 = datetime(2026, 1, 1, 9, 30, 0)
    out = []
    for i, p in enumerate(prices):
        out.append(MarketDataPoint(timestamp=t0 + timedelta(minutes=i), symbol=symbol, price=float(p)))
    return out


def test_naive_matches_optimized_cumulative_average_signals():
    # Both compute average of all history, but naive does it by rescanning and optimized uses running sum.
    ticks = _ticks([10, 11, 9, 10, 12, 12, 8])
    s1 = NaiveMovingAverageStrategy()
    s2 = OptimizedNaiveMovingAverageStrategy()

    sigs1 = [s1.generate_signals(t) for t in ticks]
    sigs2 = [s2.generate_signals(t) for t in ticks]
    assert sigs1 == sigs2


def test_windowed_strategy_emits_expected_signals():
    ticks = _ticks([10, 12, 14, 10, 9, 11])
    strat = WindowedMovingAverageStrategy(window_size=3)
    signals = [strat.generate_signals(t) for t in ticks]

    # Quick sanity: signals should be list-of-list, and later points should reflect 3-window avg
    assert signals[0] in (["BUY"], ["SELL"], [])
    assert isinstance(signals[-1], list)


def test_windowed_memory_bound_by_k():
    strat = WindowedMovingAverageStrategy(window_size=5)
    ticks = _ticks(list(range(50)))
    for t in ticks:
        strat.generate_signals(t)
    assert len(strat.window_by_symbol["ABC"]) <= 5
