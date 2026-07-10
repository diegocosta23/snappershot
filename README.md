# SnapperShot V2

SnapperShot V2 is a data collection tool that builds AI-ready stock analysis ZIP packages.

## Purpose

Create structured stock research packages for later analysis in ChatGPT.

## Workflow

1. Search company
2. Resolve ticker
3. Capture TradingView charts
4. Collect financial data
5. Export ZIP
6. Upload ZIP to ChatGPT

## ZIP Contents

Each ZIP contains:

- `1W` chart
- `1D` chart
- `4H` chart
- `45M` chart
- `analysis_package.json`

## Data Sources

### Yahoo Finance

- fundamentals
- valuation
- market data

### Finnhub

- analyst data
- fallback metrics

## Notes

- SnapperShot is only a data collector.
- No AI scoring is performed in the application.
- No recommendations or buy/sell signals are generated.
