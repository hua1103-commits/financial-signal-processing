"""data_loader.py
CSV parsing and MarketDataPoint creation using the built-in csv module.

Assumptions:
- CSV columns: timestamp, symbol, price
- timestamp is ISO-8601 (preferred) or '%Y-%m-%d %H:%M:%S'
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Iterable, List, Optional, Union

from models import MarketDataPoint


def _parse_timestamp(raw: str) -> datetime:
    raw = raw.strip()
    # Fast path: ISO-8601 (e.g., '2026-01-20T15:04:05' or with timezone offset)
    try:
        return datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except ValueError:
        pass

    # Fallback: common timestamp format
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y/%m/%d %H:%M:%S"):
        try:
            return datetime.strptime(raw, fmt)
        except ValueError:
            continue

    raise ValueError(f"Unsupported timestamp format: {raw!r}")


def load_market_data(csv_path: Union[str, Path]) -> List[MarketDataPoint]:
    """Load all rows into memory as a list of MarketDataPoint.

    Time complexity: O(n) to read and parse n rows.
    Space complexity: O(n) to store n immutable MarketDataPoint objects in a list.
    """
    csv_path = Path(csv_path)
    data: List[MarketDataPoint] = []

    with csv_path.open("r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        required = {"timestamp", "symbol", "price"}
        if not required.issubset(set(reader.fieldnames or [])):
            raise ValueError(f"CSV must contain columns {sorted(required)}; got {reader.fieldnames}")

        for row in reader:
            ts = _parse_timestamp(row["timestamp"])
            sym = row["symbol"].strip()
            price = float(row["price"])
            data.append(MarketDataPoint(timestamp=ts, symbol=sym, price=price))

    return data


def stream_market_data(csv_path: Union[str, Path]) -> Iterable[MarketDataPoint]:
    """Yield MarketDataPoint rows one-by-one (streaming).

    Time complexity: O(n)
    Space complexity: O(1) extra space (excluding the file handle), since we don't store all ticks.
    """
    csv_path = Path(csv_path)
    with csv_path.open("r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        required = {"timestamp", "symbol", "price"}
        if not required.issubset(set(reader.fieldnames or [])):
            raise ValueError(f"CSV must contain columns {sorted(required)}; got {reader.fieldnames}")

        for row in reader:
            ts = _parse_timestamp(row["timestamp"])
            sym = row["symbol"].strip()
            price = float(row["price"])
            yield MarketDataPoint(timestamp=ts, symbol=sym, price=price)


def generate_synthetic_csv(
    out_path: Union[str, Path],
    n: int,
    start: Optional[datetime] = None,
    symbol: str = "ABC",
    start_price: float = 100.0,
    seed: int = 42,
) -> Path:
    """Utility for local testing if market_data.csv isn't provided.

    Creates a simple random-walk price series.
    """
    import random

    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    rng = random.Random(seed)

    if start is None:
        start = datetime(2026, 1, 1, 9, 30, 0)

    price = start_price
    with out_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["timestamp", "symbol", "price"])
        for i in range(n):
            # 1-minute ticks
            ts = start + timedelta(minutes=i)
            # random walk with small drift
            price += rng.uniform(-0.5, 0.5)
            writer.writerow([ts.isoformat(), symbol, f"{price:.4f}"])

    return out_path
