"""reporting.py
Plot generation and markdown report creation.
"""

from __future__ import annotations

from pathlib import Path
from typing import List, Optional

import matplotlib.pyplot as plt

from profiler import BenchmarkResult


def _group_by_strategy(results: List[BenchmarkResult]):
    by = {}
    for r in results:
        by.setdefault(r.strategy_name, []).append(r)
    for k in by:
        by[k].sort(key=lambda x: x.n_ticks)
    return by


def make_plots(results: List[BenchmarkResult], out_dir: Path) -> dict:
    out_dir.mkdir(parents=True, exist_ok=True)
    by = _group_by_strategy(results)

    # Runtime plot (skip TIMEOUTs)
    plt.figure()
    for name, rs in by.items():
        xs = [r.n_ticks for r in rs if r.seconds is not None]
        ys = [r.seconds for r in rs if r.seconds is not None]
        if xs:
            plt.plot(xs, ys, marker="o", label=name)
    plt.xscale("log")
    plt.yscale("log")
    plt.xlabel("Input size (ticks, log scale)")
    plt.ylabel("Runtime (seconds, log scale)")
    plt.title("Runtime Scaling by Strategy (TIMEOUTs omitted)")
    plt.legend()
    runtime_path = out_dir / "runtime_vs_input.png"
    plt.savefig(runtime_path, bbox_inches="tight")
    plt.close()

    # Memory plot (skip missing)
    plt.figure()
    for name, rs in by.items():
        xs = [r.n_ticks for r in rs if r.peak_memory_mb is not None]
        ys = [r.peak_memory_mb for r in rs if r.peak_memory_mb is not None]
        if xs:
            plt.plot(xs, ys, marker="o", label=name)
    plt.xscale("log")
    plt.yscale("log")
    plt.xlabel("Input size (ticks, log scale)")
    plt.ylabel("Peak memory (MB, log scale)")
    plt.title("Memory Scaling by Strategy (tracemalloc peak)")
    plt.legend()
    mem_path = out_dir / "memory_vs_input.png"
    plt.savefig(mem_path, bbox_inches="tight")
    plt.close()

    return {"runtime_plot": runtime_path, "memory_plot": mem_path}


def _fmt(v: Optional[float], decimals: int = 6) -> str:
    if v is None:
        return "TIMEOUT"
    return f"{v:.{decimals}f}"


def _fmt_mb(v: Optional[float]) -> str:
    if v is None:
        return "-"
    return f"{v:.3f}"


def write_report(
    results: List[BenchmarkResult],
    plots: dict,
    out_path: Path,
    extra_notes: str = "",
) -> Path:
    out_path.parent.mkdir(parents=True, exist_ok=True)

    header = "| Strategy | # Ticks | Runtime (s) | Peak Memory (MB) |\n|---|---:|---:|---:|\n"
    lines = []
    for r in sorted(results, key=lambda x: (x.strategy_name, x.n_ticks)):
        lines.append(f"| {r.strategy_name} | {r.n_ticks:,} | {_fmt(r.seconds)} | {_fmt_mb(r.peak_memory_mb)} |")
    table = header + "\n".join(lines) + "\n"

    md = f"""# Runtime & Space Complexity in Financial Signal Processing

## What was implemented
- **MarketDataPoint**: frozen dataclass (immutable tick object)
- **Strategies**:
  - **NaiveMovingAverageStrategy**: rescans history to compute average each tick
  - **WindowedMovingAverageStrategy**: deque + running sum for sliding window
  - **OptimizedNaiveMovingAverageStrategy**: running sum + count (cumulative average)

## Complexity annotations (theoretical)
### Data ingestion
- `load_market_data`: **Time O(n)**, **Space O(n)** (stores all ticks in a list)

### NaiveMovingAverageStrategy
- Per tick: `sum(history)` => **Time O(n)**, `history` list => **Space O(n)**
- Over n ticks total: **Time O(n^2)**

### WindowedMovingAverageStrategy (window size k)
- Per tick: constant deque ops + arithmetic => **Time O(1)**
- Buffer size bounded by k => **Space O(k)**

### OptimizedNaiveMovingAverageStrategy
- Per tick: update sum & count => **Time O(1)**
- No history retained => **Space O(1)**

## Benchmark results
{table}

## Scaling plots
### Runtime vs input size
![Runtime vs input]({plots['runtime_plot'].name})

### Memory vs input size
![Memory vs input]({plots['memory_plot'].name})

## Narrative comparison
- The **naive strategy** grows superlinearly because every tick rescans a longer history list; at 100k ticks it can exceed practical runtime limits (**TIMEOUT** in the table if capped).
- The **windowed strategy** stays stable per tick because it does constant work and stores only the last **k** prices.
- The **optimized naive strategy** demonstrates how replacing repeated scans with **incremental state** can cut both time and memory, at the cost of changing from a windowed average to a cumulative average.

## Profiling notes
See `profiles/` for cProfile output (top cumulative-time functions). TIMEOUT runs are not profiled.

{extra_notes}
"""

    out_path.write_text(md, encoding="utf-8")
    return out_path
