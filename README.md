# Bloxflip Crash Passive Research Tool (Python 3.11)

Professional CLI + optional web dashboard for passive crash-data research.

## Safety and scope
- No betting.
- No auto-cashout.
- No bypass of CAPTCHA/Cloudflare/login/rate limits.
- Only use endpoints visible in normal DevTools.

## Setup (Windows/macOS/Linux)
1. Install Python 3.11.
2. `python -m venv .venv`
3. Activate venv:
   - Windows: `.venv\\Scripts\\activate`
   - macOS/Linux: `source .venv/bin/activate`
4. `pip install -r requirements.txt`
5. Edit `config.yaml` and set `endpoint_url`.

## API/WS discovery
1. Open https://bloxflip.com/crash
2. Press F12
3. Network tab
4. Filter Fetch/XHR + WS
5. Watch round-finish traffic
6. Find result/multiplier endpoint
7. Paste into `config.yaml`

## CLI usage
```bash
python main.py collect
python main.py stats
python main.py graph
python main.py backtest
python main.py export-csv
python main.py import-csv path.csv
python main.py run_all --minutes 10
python main.py dashboard
```

## Dashboard
Run:
```bash
python main.py dashboard
```
Then open http://localhost:8000

Pages:
- Overview
- Live Data
- Graphs
- Backtest Results
- Settings

## Screenshots
- Add screenshots after running dashboard and generating graphs.
