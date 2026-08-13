---
title: Middle-East Tension Indicator
emoji: ⚡
colorFrom: blue
colorTo: red
sdk: gradio
sdk_version: 6.24.0
app_file: app.py
pinned: false
license: mit
short_description: Real-time market-based geopolitical tension gauge for the Middle East
---

# ⚡ Middle-East Tension Indicator (METI)

**A real-time, transparent dashboard that turns financial market movements into a clear Middle-East tension score (0–100).**

Born from personal experience during the June 2025 Iran-Israel conflict.

---

## What it does

METI watches four assets that historically react to Middle-East geopolitical stress:

| Asset              | Weight | Why it matters                                      |
|--------------------|--------|-----------------------------------------------------|
| Crude Oil (CL=F)   | 38%    | Direct supply-disruption risk                       |
| Gold (GC=F)        | 28%    | Classic safe-haven                                  |
| Bitcoin (BTC-USD)  | 24%    | Modern risk-off / liquidity signal                  |
| Lockheed Martin    | 10%    | Defense spending proxy                              |

It combines multi-timeframe price changes into a single **Tension Index** and shows:

- Current score + regime (Calm / Elevated / High / Critical)
- Per-asset contribution
- Recent history

This is **not** a prediction engine. It is a market-implied stress gauge meant as an early-warning *complement* to news.

---

## Quick start (local)

```bash
# clone / download the project
cd meti

# create environment (recommended)
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate

# install
pip install -r requirements.txt

# run
python app.py
```

Then open http://localhost:7860

---

## Deploy on Hugging Face Spaces (free)

1. Create a new Space → choose **Gradio** SDK
2. Upload (or git push) the contents of this repository
3. Make sure `app.py` and `requirements.txt` are at the root
4. The Space will build and run automatically

The same code works locally and on Spaces.

---

## Project structure

```
meti/
├── app.py                  # Gradio entrypoint
├── requirements.txt
├── config/default.yaml     # Assets, weights, thresholds
├── src/meti/
│   ├── config.py
│   ├── data/               # providers, cache, history
│   ├── indicators/         # tension calculation
│   └── viz/                # Plotly charts
├── data/                   # SQLite history (auto-created)
└── README.md
```

---

## Methodology (short)

1. For each asset, compute percent change over 1h / 4h / 1d / 1wk windows
2. Weight the timeframes (default: 10% / 30% / 40% / 20%)
3. Weight the assets (Oil 38%, Gold 28%, BTC 24%, LMT 10%)
4. Normalize the raw sum onto a 0–100 scale (baseline ≈ 20 when markets are quiet)

All weights and parameters live in `config/default.yaml` and can be changed without touching code.

---

## Roadmap

- [x] Core indicator + Gradio dashboard
- [x] Local history (SQLite)
- [x] HF Spaces ready
- [ ] Richer historical event annotations
- [ ] Optional news / social sentiment layer
- [ ] Simple alert thresholds

---

## License

MIT

---

*Built by someone who was awake at 3:20 AM in Tehran when the first strikes began.*
