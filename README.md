# Runtime & Space Complexity in Financial Signal Processing

## Setup
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Run
```bash
python main.py --csv market_data.csv --out .
```

If `market_data.csv` is missing, the script generates `market_data_synthetic.csv` (100k ticks) for demo.

## Project structure
- `data_loader.py` — CSV parsing + `MarketDataPoint` creation (built-in `csv`)
- `models.py` — immutable dataclass + `Strategy` ABC
- `strategies.py` — naive, windowed, and optimized strategy implementations
- `profiler.py` — timeit + cProfile + tracemalloc peak memory
- `reporting.py` — plots + `complexity_report.md`
- `tests/` — unit tests (pytest)

## Notes
- Memory measurement uses `tracemalloc` to avoid external deps.
- cProfile text outputs are saved in `profiles/`.
