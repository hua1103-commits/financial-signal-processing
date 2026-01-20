"""profiler.py
Runtime and memory measurement utilities.

We support:
- perf_counter timing (optionally with a time limit to prevent pathological runs)
- cProfile for hotspots
- tracemalloc for peak memory (works without external dependencies)

Note: The naive O(n^2) strategy can be extremely slow at 100k ticks. To keep
benchmarks tractable, we allow a per-run time limit and record TIMEOUT when exceeded.
"""

from __future__ import annotations

import cProfile
import io
import pstats
import time
import tracemalloc
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Dict, List, Optional, Sequence

from models import MarketDataPoint, Strategy


@dataclass
class BenchmarkResult:
    strategy_name: str
    n_ticks: int
    seconds: Optional[float]          # None => TIMEOUT
    peak_memory_mb: Optional[float]   # None => not measured


def run_strategy(strategy: Strategy, ticks: Sequence[MarketDataPoint]) -> int:
    """Run a strategy over ticks, returning number of signals emitted."""
    signal_count = 0
    for t in ticks:
        signal_count += len(strategy.generate_signals(t))
    return signal_count


def time_strategy(
    factory: Callable[[], Strategy],
    ticks: Sequence[MarketDataPoint],
    repeats: int = 1,
    time_limit_s: Optional[float] = None,
) -> Optional[float]:
    """Measure execution time (seconds). Returns min time, or None if TIMEOUT.

    Time limit is checked between repeats (not during a single run), to avoid
    excessive overhead. For very slow strategies, set repeats=1 and a small limit.
    """
    best: Optional[float] = None
    for _ in range(repeats):
        strategy = factory()
        t0 = time.perf_counter()
        run_strategy(strategy, ticks)
        dt = time.perf_counter() - t0
        if time_limit_s is not None and dt > time_limit_s:
            return None
        best = dt if best is None else min(best, dt)
    return best


def peak_memory_tracemalloc(factory: Callable[[], Strategy], ticks: Sequence[MarketDataPoint]) -> float:
    """Measure peak memory in MB using tracemalloc."""
    tracemalloc.start()
    strategy = factory()
    run_strategy(strategy, ticks)
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    return peak / (1024 * 1024)


def profile_cprofile(factory: Callable[[], Strategy], ticks: Sequence[MarketDataPoint], out_path: Path) -> Path:
    """Write cProfile stats to a text file for inspection."""
    pr = cProfile.Profile()
    pr.enable()
    strategy = factory()
    run_strategy(strategy, ticks)
    pr.disable()

    s = io.StringIO()
    ps = pstats.Stats(pr, stream=s).sort_stats("cumulative")
    ps.print_stats(40)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(s.getvalue(), encoding="utf-8")
    return out_path


def benchmark_strategies(
    ticks: Sequence[MarketDataPoint],
    strategy_factories: Dict[str, Callable[[], Strategy]],
    repeats: int = 1,
    time_limit_s: Optional[float] = None,
    cprofile_dir: Optional[Path] = None,
    measure_memory: bool = True,
) -> List[BenchmarkResult]:
    results: List[BenchmarkResult] = []
    for name, factory in strategy_factories.items():
        secs = time_strategy(factory, ticks, repeats=repeats, time_limit_s=time_limit_s)
        peak_mb: Optional[float] = None
        if measure_memory and secs is not None:
            # Only measure memory if the run finished (otherwise we'd hang again).
            peak_mb = peak_memory_tracemalloc(factory, ticks)

        results.append(BenchmarkResult(strategy_name=name, n_ticks=len(ticks), seconds=secs, peak_memory_mb=peak_mb))

        if cprofile_dir is not None and secs is not None:
            profile_cprofile(factory, ticks, cprofile_dir / f"{name}_{len(ticks)}.txt")

    return results
