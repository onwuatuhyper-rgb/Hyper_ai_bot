# HYPER AI BOT (Deriv Edition) — Project Context

- **Developer / Device:** Hypervynx | Android phone only | $0 free budget
- **Repo Structure (`Hyper_ai_bot` on GitHub):**
  - `main.py`: Flet web app UI (`ft.AppView.WEB_BROWSER` bound to `0.0.0.0:$PORT` for Render free hosting)
  - `api/deriv_client.py`: Async Deriv WebSocket client (`wss://://derivws.com`) for `frxXAUUSD` (Gold) and `frxEURUSD`, Demo & Real API Token auth, and Multiplier trades (`MULTUP`/`MULTDOWN`) with stop-loss and take-profit
  - `core/features.py`: `FeatureEngineer` computing candle body, upper/lower wicks, range, returns, EMAs, ATR, and RSI
  - `core/ai_engine.py`: `MarketAIModel` training & comparing RandomForest vs GradientBoosting with chronological 80/20 unseen-data validation
  - `core/risk_manager.py`: `RiskManager` enforcing min confidence, stake size, max daily loss, and max consecutive loss limits (always overrides AI signals)
  - `requirements.txt`: `flet>=0.25.2`, `websockets`, `pandas`, `numpy`, `scikit-learn`
- **Deployment Target:** Render Web Service (`pip install -r requirements.txt` -> `python main.py`), added to Android Home Screen via Chrome PWA.
