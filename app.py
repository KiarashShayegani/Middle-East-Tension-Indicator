"""
Middle-East Tension Indicator (METI) – Gradio application entrypoint.

Runs locally and on Hugging Face Spaces (Gradio SDK).
"""

from __future__ import annotations

import sys
from pathlib import Path

# Ensure src/ is on the path when running from project root
ROOT = Path(__file__).resolve().parent
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

import gradio as gr
import plotly.graph_objects as go

from meti.config import get_settings
from meti.indicators.tension import calculate_tension_index
from meti.data.history import get_recent_snapshots, init_db
from meti.viz.charts import (
    create_tension_gauge,
    create_history_chart,
    create_contribution_bar,
)

# ---------------------------------------------------------------------------
# Theme & CSS
# ---------------------------------------------------------------------------

CUSTOM_CSS = """
.gradio-container {
    max-width: 1100px !important;
    margin: auto;
}
.main-title {
    text-align: center;
    font-size: 2.2rem !important;
    font-weight: 800;
    color: #f8fafc;
    margin-bottom: 0.2rem;
}
.subtitle {
    text-align: center;
    color: #94a3b8;
    font-size: 1.05rem;
    margin-bottom: 1.5rem;
}
.score-box {
    background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
    border: 1px solid rgba(148, 163, 184, 0.25);
    border-radius: 16px;
    padding: 1.2rem 1.5rem;
    text-align: center;
}
.regime-calm { color: #10b981; font-weight: 700; }
.regime-elevated { color: #facc15; font-weight: 700; }
.regime-high { color: #f97316; font-weight: 700; }
.regime-critical { color: #ef4444; font-weight: 700; }
.asset-card {
    background: rgba(30, 41, 59, 0.85);
    border: 1px solid rgba(100, 116, 139, 0.3);
    border-radius: 12px;
    padding: 1rem;
    margin-bottom: 0.5rem;
}
footer { visibility: hidden; }
"""

# ---------------------------------------------------------------------------
# Core update function
# ---------------------------------------------------------------------------

def refresh_data():
    """Fetch latest data and build all UI components."""
    settings = get_settings()
    try:
        result = calculate_tension_index(settings=settings, persist=True)
    except Exception as e:
        # Graceful fallback so the UI never fully dies
        empty_gauge = go.Figure()
        empty_gauge.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            height=340,
            annotations=[{
                "text": f"Data temporarily unavailable<br>{type(e).__name__}",
                "xref": "paper", "yref": "paper",
                "x": 0.5, "y": 0.5, "showarrow": False,
                "font": {"color": "#ef4444", "size": 16},
            }],
        )
        return (
            empty_gauge,
            "—",
            "Error",
            "Could not fetch market data. Please try again shortly.",
            empty_gauge,
            empty_gauge,
            "Last update failed",
        )

    score = result["tension_score"]
    regime = result["regime"]
    raw = result["raw_index"]

    # Gauge
    gauge = create_tension_gauge(score, settings)

    # Regime styling
    regime_class = {
        "Calm": "regime-calm",
        "Elevated": "regime-elevated",
        "High": "regime-high",
        "Critical": "regime-critical",
    }.get(regime, "")

    score_md = f"""
<div class="score-box">
  <div style="font-size: 3.2rem; font-weight: 800; color: #f8fafc;">{score}</div>
  <div class="{regime_class}" style="font-size: 1.3rem; margin-top: 0.3rem;">{regime}</div>
  <div style="color: #94a3b8; margin-top: 0.6rem; font-size: 0.95rem;">
    Raw index: {raw:+.3f}
  </div>
</div>
"""

    # Asset cards markdown
    cards = []
    for ticker, info in result["contributions"].items():
        change = info["weighted_change"]
        sign = "▲" if change >= 0 else "▼"
        color = "#10b981" if change >= 0 else "#ef4444"
        price = info["current_price"]
        price_str = f"${price:,.2f}" if price else "—"
        cards.append(
            f"""
<div class="asset-card">
  <div style="display:flex; justify-content:space-between; align-items:center;">
    <div>
      <span style="font-size:1.4rem;">{info['emoji']}</span>
      <strong style="color:{info['color']}; margin-left:0.4rem;">{info['name']}</strong>
      <span style="color:#64748b; font-size:0.85rem; margin-left:0.5rem;">({info['weight']*100:.0f}%)</span>
    </div>
    <div style="text-align:right;">
      <div style="font-family:monospace; color:#e2e8f0;">{price_str}</div>
      <div style="color:{color}; font-weight:600;">{sign} {abs(change):.2f}%</div>
    </div>
  </div>
</div>
"""
        )
    assets_md = "\n".join(cards)

    # Contribution chart
    contrib_fig = create_contribution_bar(result["contributions"])

    # History
    snapshots = get_recent_snapshots(days=30)
    history_fig = create_history_chart(snapshots)

    ts = result["timestamp"][:19].replace("T", " ") + " UTC"
    status = f"Last updated: {ts}"

    return gauge, score_md, regime, assets_md, contrib_fig, history_fig, status


# ---------------------------------------------------------------------------
# Build the Gradio interface
# ---------------------------------------------------------------------------

def build_demo() -> gr.Blocks:
    settings = get_settings()
    init_db()

    with gr.Blocks(
        title=f"{settings.app.short_name} – {settings.app.title}",
        theme=gr.themes.Soft(
            primary_hue="blue",
            secondary_hue="slate",
            neutral_hue="slate",
            font=[gr.themes.GoogleFont("Inter"), "Arial", "sans-serif"],
        ).set(
            body_background_fill="#0f172a",
            body_text_color="#e2e8f0",
            block_background_fill="#1e293b",
            block_border_color="rgba(100,116,139,0.3)",
            block_label_text_color="#94a3b8",
            button_primary_background_fill="#3b82f6",
            button_primary_text_color="#ffffff",
        ),
        css=CUSTOM_CSS,
    ) as demo:

        gr.HTML(
            f"""
            <h1 class="main-title">⚡ {settings.app.title}</h1>
            <p class="subtitle">{settings.app.description}</p>
            """
        )

        with gr.Row():
            refresh_btn = gr.Button("🔄 Refresh Data", variant="primary", scale=1)
            status_text = gr.Markdown("Click refresh to load the latest reading.", elem_id="status")

        with gr.Tabs():
            # ---------- Dashboard ----------
            with gr.Tab("Dashboard", id="dashboard"):
                with gr.Row():
                    with gr.Column(scale=3):
                        gauge_plot = gr.Plot(label="Tension Gauge")
                    with gr.Column(scale=2):
                        score_html = gr.HTML("<div class='score-box'>Loading…</div>")
                        regime_state = gr.State("—")

                gr.Markdown("### Market Assets")
                assets_html = gr.HTML("Loading asset data…")

                gr.Markdown("### Contribution Breakdown")
                contrib_plot = gr.Plot(label="Asset Contributions")

            # ---------- History ----------
            with gr.Tab("History"):
                gr.Markdown(
                    "Historical tension scores (stored locally / on the Space). "
                    "Data accumulates as the dashboard is used."
                )
                history_plot = gr.Plot(label="Tension History")

            # ---------- Methodology ----------
            with gr.Tab("Methodology"):
                gr.Markdown(
                    """
## How the Middle-East Tension Index works

METI turns real-time market movements into a single **0–100 tension score**.

### Assets & Weights
| Asset | Weight | Rationale |
|-------|--------|-----------|
| **Crude Oil (CL=F)** | 38% | Direct exposure to Middle-East supply risk |
| **Gold (GC=F)** | 28% | Classic safe-haven during geopolitical stress |
| **Bitcoin (BTC-USD)** | 24% | Modern risk-off / liquidity indicator |
| **Lockheed Martin (LMT)** | 10% | Defense spending proxy |

### Multi-timeframe view
Each asset’s percent change is measured across four windows and then weighted:

- 1 Hour → 10%
- 4 Hours → 30%
- 1 Day → 40%
- 1 Week → 20%

This reduces noise from very short-term moves while still reacting quickly.

### Normalization
A raw weighted sum is mapped to the 0–100 scale:
- Neutral (raw ≈ 0) sits around **20**
- Strong positive moves raise the score linearly
- Negative moves decay logarithmically so the gauge does not collapse too easily

### Important notes
- This is **not** a prediction engine. It is a *market-implied stress gauge*.
- Markets can be wrong, delayed, or driven by other factors.
- The index is most useful as an early-warning *complement* to news and analysis.
                    """
                )

            # ---------- About ----------
            with gr.Tab("About"):
                gr.Markdown(
                    f"""
## About METI

**Middle-East Tension Indicator** was born from personal experience during the June 2025 Iran-Israel conflict.

> On June 13th, 2025, at 3:20 AM in Tehran, distant booms that first seemed like thunder turned out to be the start of a war. Weeks later, looking at the markets, a clear pattern appeared: Oil, Gold and Bitcoin had begun moving *hours* before the public news broke.

This project turns that observation into an open, transparent tool so anyone can see the same market stress signal without a Bloomberg terminal.

### Version
`{settings.app.version}`

### Philosophy
- Transparent methodology
- Citizen-built, not institutional
- Educational first, actionable second
- Free and open

### Source
The full source code, configuration and history of the project live on GitHub.

---
*Built with Gradio • Data via Yahoo Finance • Designed to run locally and on Hugging Face Spaces*
                    """
                )

        # Wire the refresh
        outputs = [
            gauge_plot,
            score_html,
            regime_state,
            assets_html,
            contrib_plot,
            history_plot,
            status_text,
        ]

        refresh_btn.click(fn=refresh_data, inputs=None, outputs=outputs)
        demo.load(fn=refresh_data, inputs=None, outputs=outputs)

    return demo


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

demo = build_demo()

if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=7860)
