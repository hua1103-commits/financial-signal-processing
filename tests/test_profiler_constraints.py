import time
from datetime import datetime, timedelta

import pytest

from models import MarketDataPoint
from profiler import run_strategy
from strategies import OptimizedNaiveMovingAverageStrategy, WindowedMovingAverageStrategy


def _ticks(n, symbol="ABC"):
    t0 = datetime(2026, 1, 1, 9, 30, 0)
    out = []
    price = 100.0
    for i in range(n):
        price += (i % 7 - 3) * 0.01
        out.append(MarketDataPoint(timestamp=t0 + timedelta(minutes=i), symbol=symbol, price=price))
    return out


@pytest.mark.slow
def test_optimized_under_time_budget_100k():
    ticks = _ticks(100_000)
    strat = OptimizedNaiveMovingAverageStrategy()

    t0 = time.perf_counter()
    run_strategy(strat, ticks)
    dt = time.perf_counter() - t0

    # This should pass on most modern machines; if CI is slow, adjust threshold.
    assert dt < 1.0


def test_windowed_fast_enough_100k():
    ticks = _ticks(100_000)
    strat = WindowedMovingAverageStrategy(window_size=10)

    t0 = time.perf_counter()
    run_strategy(strat, ticks)
    dt = time.perf_counter() - t0
    assert dt < 1.0
