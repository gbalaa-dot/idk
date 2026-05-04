# Bloxflip Crash Passive Research Tool (Python 3.11)

This project is a **statistics/research tool** for passively collecting crash multipliers and evaluating predictive signal quality.

## Safety and scope
- Does **not** place bets.
- Does **not** auto-cashout.
- Does **not** bypass login, Cloudflare, CAPTCHA, anti-bot, or rate limits.
- Uses only endpoints you can observe in normal browser DevTools.

## Files
- `main.py`
- `config.yaml`
- `requirements.txt`
- `src/*` modules for collection, parsing, stats, models, backtesting, graphing, configuration, and database.

## Setup
1. Install Python 3.11.
2. Create and activate virtual environment.
3. Install deps:
   ```bash
   pip install -r requirements.txt
   ```
4. Optional: create `.env` with tokens/headers **you already have authorization to use**.
5. Edit `config.yaml` and insert your endpoint URL.

## API/WS endpoint discovery (no bypassing)
1. Open `https://bloxflip.com/crash`.
2. Press `F12`.
3. Open **Network** tab.
4. Filter by **Fetch/XHR** and **WS**.
5. Watch traffic as rounds finish.
6. Identify endpoint messages that include round results/multipliers.
7. Paste endpoint into `config.yaml` (`endpoint_url`).

## Commands
```bash
python main.py collect
python main.py stats
python main.py graph
python main.py backtest
python main.py export-csv
python main.py import-csv path.csv
```

## Outputs
- SQLite DB at `data/crash_results.sqlite`
- Graphs in `graphs/`
- Backtest report with baseline/model comparison and stability warnings.

## Accuracy rule
A pattern should not be treated as real unless it:
1. Beats 50% accuracy.
2. Beats majority baseline.
3. Holds on unseen future data.
4. Stays stable under walk-forward validation.
