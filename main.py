"""main.py
Orchestrates ingestion, strategy execution, profiling, and report generation.

Usage:
    python main.py --csv market_data.csv --out .

If market_data.csv does not exist, it will generate a synthetic CSV for demo purposes.
"""

from __future__ import annotations

import argparse
from pathlib import Path

from data_loader import generate_synthetic_csv, load_market_data
from profiler import benchmark_strategies
from reporting import make_plots, write_report
from strategies import NaiveMovingAverageStrategy, OptimizedNaiveMovingAverageStrategy, WindowedMovingAverageStrategy


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--csv", type=str, default="market_data.csv", help="Path to market_data.csv")
    parser.add_argument("--window", type=int, default=10, help="Window size for windowed strategy")
    parser.add_argument("--out", type=str, default=".", help="Output directory (report, plots, profiles)")
    parser.add_argument("--time_limit", type=float, default=5.0, help="Per-strategy time limit (seconds) before TIMEOUT")
    args = parser.parse_args()

    out_dir = Path(args.out)
    csv_path = Path(args.csv)

    if not csv_path.exists():
        csv_path = out_dir / "market_data_synthetic.csv"
        generate_synthetic_csv(csv_path, n=100_000)

    ticks = load_market_data(csv_path)

    sizes = [1_000, 10_000, 100_000]
    sizes = [s for s in sizes if s <= len(ticks)]

    factories = {
        "NaiveMovingAverageStrategy": lambda: NaiveMovingAverageStrategy(),
        f"WindowedMovingAverageStrategy_k={args.window}": lambda: WindowedMovingAverageStrategy(window_size=args.window),
        "OptimizedNaiveMovingAverageStrategy": lambda: OptimizedNaiveMovingAverageStrategy(),
    }

    all_results = []
    profile_dir = out_dir / "profiles"

    for n in sizes:
        subset = ticks[:n]

        # For large n, keep repeats low; cap worst-case strategies via time_limit.
        repeats = 3 if n <= 10_000 else 1

        all_results.extend(
            benchmark_strategies(
                subset,
                factories,
                repeats=repeats,
                time_limit_s=args.time_limit,
                cprofile_dir=profile_dir,
                measure_memory=True,
            )
        )

    plot_dir = out_dir / "plots"
    plots = make_plots(all_results, plot_dir)
    report_path = out_dir / "complexity_report.md"
    write_report(all_results, plots, report_path)

    print(f"Report written to: {report_path.resolve()}")
    print(f"Plots written to: {plot_dir.resolve()}")
    print(f"cProfile outputs written to: {profile_dir.resolve()}")


if __name__ == "__main__":
    main()
