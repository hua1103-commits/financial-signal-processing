# Runtime & Space Complexity in Financial Signal Processing

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
| Strategy | # Ticks | Runtime (s) | Peak Memory (MB) |
|---|---:|---:|---:|
| NaiveMovingAverageStrategy | 1,000 | 0.002204 | 0.009 |
| NaiveMovingAverageStrategy | 10,000 | 0.185883 | 0.081 |
| NaiveMovingAverageStrategy | 100,000 | TIMEOUT | - |
| OptimizedNaiveMovingAverageStrategy | 1,000 | 0.000582 | 0.000 |
| OptimizedNaiveMovingAverageStrategy | 10,000 | 0.006097 | 0.000 |
| OptimizedNaiveMovingAverageStrategy | 100,000 | 0.062412 | 0.000 |
| WindowedMovingAverageStrategy_k=10 | 1,000 | 0.000835 | 0.000 |
| WindowedMovingAverageStrategy_k=10 | 10,000 | 0.008525 | 0.000 |
| WindowedMovingAverageStrategy_k=10 | 100,000 | 0.083116 | 0.000 |


## Scaling plots
### Runtime vs input size
![Runtime vs input](runtime_vs_input.png)

### Memory vs input size
![Memory vs input](memory_vs_input.png)

## Narrative comparison
- The **naive strategy** grows superlinearly because every tick rescans a longer history list; at 100k ticks it can exceed practical runtime limits (**TIMEOUT** in the table if capped).
- The **windowed strategy** stays stable per tick because it does constant work and stores only the last **k** prices.
- The **optimized naive strategy** demonstrates how replacing repeated scans with **incremental state** can cut both time and memory, at the cost of changing from a windowed average to a cumulative average.

## Profiling notes
See `profiles/` for cProfile output (top cumulative-time functions). TIMEOUT runs are not profiled.


