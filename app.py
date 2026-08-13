"""
Middle-East Tension Indicator (METI) – Gradio application entrypoint.

Runs locally and on Hugging Face Spaces (Gradio SDK).
Compatible with ZeroGPU hardware (harmless @spaces.GPU stub).
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
# ZeroGPU compatibility (HF Spaces)
# ---------------------------------------------------------------------------
# When the Space runs on ZeroGPU hardware, HF requires at least one
# function decorated with @spaces.GPU. This app is pure CPU, so we
# provide a no-op stub that satisfies the runtime check.
try:
    import spaces

    @spaces.GPU(duration=1)
    def _gpu_warmup():
        """No-op to satisfy ZeroGPU startup check."""
        return True

except ImportError:
    # Running locally or on CPU hardware — spaces package not present
    def _gpu_warmup():
        return True


# ---------------------------------------------------------------------------
# Theme & CSS
# ---------------------------------------------------------------------------

CUSTOM_CSS = """
/* Global */
.gradio-container {
    max-width: 1080px !important;
    margin: 0 auto !important;
    font-family: 'Inter', system-ui, -apple-system, sans-serif !important;
}

/* Header */
.main-title {
    text-align: center;
    font-size: 2.1rem !important;
    font-weight: 800 !important;
    color: #f8fafc !important;
    margin: 0.4rem 0 0.15rem 0 !important;
    letter-spacing: -0.02em;
}
.subtitle {
    text-align: center;
    color: #94a3b8 !important;
    font-size: 0.98rem !important;
    margin-bottom: 1.25rem !important;
}

/* Score box */
.score-box {
    background: linear-gradient(160deg, #1e293b 0%, #0f172a 100%);
    border: 1px solid rgba(148, 163, 184, 0.22);
    border-radius: 16px;
    padding: 1.4rem 1.2rem;
    text-align: center;
    box-shadow: 0 4px 24px rgba(0,0,0,0.25);
}
.score-value {
    font-size: 3.4rem;
    font-weight: 800;
    color: #f8fafc;
    line-height: 1.1;
    letter-spacing: -0.03em;
}
.regime-calm { color: #34d399; font-weight: 700; font-size: 1.25rem; }
.regime-elevated { color: #fbbf24; font-weight: 700; font-size: 1.25rem; }
.regime-high { color: #fb923c; font-weight: 700; font-size: 1.25rem; }
.regime-critical { color: #f87171; font-weight: 700; font-size: 1.25rem; }
.raw-index {
    color: #64748b;
    font-size: 0.88rem;
    margin-top: 0.55rem;
}

/* Asset cards */
.asset-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 0.75rem;
    margin-top: 0.5rem;
}
@media (max-width: 700px) {
    .asset-grid { grid-template-columns: 1fr; }
}
.asset-card {
    background: rgba(30, 41, 59, 0.9);
    border: 1px solid rgba(100, 116, 139, 0.28);
    border-radius: 14px;
    padding: 1rem 1.1rem;
    transition: border-color 0.2s ease, transform 0.15s ease;
}
.asset-card:hover {
    border-color: rgba(148, 163, 184, 0.45);
    transform: translateY(-1px);
}
.asset-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 0.45rem;
}
.asset-name {
    font-weight: 600;
    font-size: 0.98rem;
}
.asset-weight {
    color: #64748b;
    font-size: 0.78rem;
    font-weight: 500;
}
.asset-price {
    font-family: ui-monospace, 'Cascadia Code', 'SF Mono', monospace;
    color: #e2e8f0;
    font-size: 1.05rem;
    font-weight: 600;
}
.asset-change-up { color: #34d399; font-weight: 600; font-size: 0.95rem; }
.asset-change-down { color: #f87171; font-weight: 600; font-size: 0.95rem; }
.tf-row {
    display: flex;
    gap: 0.4rem;
    margin-top: 0.55rem;
    flex-wrap: wrap;
}
.tf-chip {
    background: rgba(15, 23, 42, 0.7);
    border: 1px solid rgba(100, 116, 139, 0.25);
    border-radius: 6px;
    padding: 0.15rem 0.45rem;
    font-size: 0.72rem;
    color: #94a3b8;
    font-family: ui-monospace, monospace;
}

/* Section headers */
.section-label {
    color: #94a3b8 !important;
    font-size: 0.85rem !important;
    font-weight: 600 !important;
    text-transform: uppercase;
    letter-spacing: 0.04em;
    margin: 1.1rem 0 0.5rem 0 !important;
}

/* Status line */
#status {
    color: #64748b !important;
    font-size: 0.85rem !important;
}

/* Hide Gradio footer */
footer { display: none !important; }
"""

# ---------------------------------------------------------------------------
# Core update function
# ---------------------------------------------------------------------------

def refresh_data():
    """Fetch latest data and build all UI components."""
    settings = get_settings()
    try:
        # Touch the GPU stub once so ZeroGPU runtime is happy
        _gpu_warmup()
        result = calculate_tension_index(settings=settings, persist=True)
    except Exception as e:
        empty = go.Figure()
        empty.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            height=300,
            annotations=[{
                "text": f"Data temporarily unavailable<br><span style='font-size:13px'>{type(e).__name__}</span>",
                "xref": "paper", "yref": "paper",
                "x": 0.5, "y": 0.5, "showarrow": False,
                "font": {"color": "#f87171", "size": 15},
            }],
        )
        err_html = """
        <div class="score-box">
          <div class="score-value">—</div>
          <div class="regime-critical">Error</div>
          <div class="raw-index">Could not fetch market data</div>
        </div>
        """
        return empty, err_html, "Error", "<p style='color:#94a3b8'>Retry in a moment.</p>", empty, empty, "Update failed"

    score = result["tension_score"]
    regime = result["regime"]
    raw = result["raw_index"]

    gauge = create_tension_gauge(score, settings)

    regime_class = {
        "Calm": "regime-calm",
        "Elevated": "regime-elevated",
        "High": "regime-high",
        "Critical": "regime-critical",
    }.get(regime, "regime-calm")

    score_html = f"""
    <div class="score-box">
      <div class="score-value">{score}</div>
      <div class="{regime_class}">{regime}</div>
      <div class="raw-index">Raw index: {raw:+.3f}</div>
    </div>
    """

    # Richer asset cards with per-timeframe chips
    tf_labels = {"1h": "1H", "4h": "4H", "1d": "1D", "1wk": "1W"}
    cards = ['<div class="asset-grid">']
    for ticker, info in result["contributions"].items():
        change = info["weighted_change"]
        sign = "▲" if change >= 0 else "▼"
        ch_class = "asset-change-up" if change >= 0 else "asset-change-down"
        price = info["current_price"]
        price_str = f"${price:,.2f}" if price else "—"

        chips = []
        for tf_key, pct in info.get("changes", {}).items():
            label = tf_labels.get(tf_key, tf_key)
            chip_color = "#34d399" if pct >= 0 else "#f87171"
            chips.append(
                f'<span class="tf-chip" style="color:{chip_color}">{label} {pct:+.2f}%</span>'
            )
        chips_html = "".join(chips)

        cards.append(f"""
        <div class="asset-card">
          <div class="asset-header">
            <div>
              <span style="font-size:1.25rem">{info['emoji']}</span>
              <span class="asset-name" style="color:{info['color']}; margin-left:0.35rem">{info['name']}</span>
              <span class="asset-weight"> · {info['weight']*100:.0f}%</span>
            </div>
            <div style="text-align:right">
              <div class="asset-price">{price_str}</div>
              <div class="{ch_class}">{sign} {abs(change):.2f}%</div>
            </div>
          </div>
          <div class="tf-row">{chips_html}</div>
        </div>
        """)
    cards.append("</div>")
    assets_html = "\n".join(cards)

    contrib_fig = create_contribution_bar(result["contributions"])
    snapshots = get_recent_snapshots(days=30)
    history_fig = create_history_chart(snapshots)

    ts = result["timestamp"][:19].replace("T", " ") + " UTC"
    status = f"Last updated: **{ts}**"

    return gauge, score_html, regime, assets_html, contrib_fig, history_fig, status


# ---------------------------------------------------------------------------
# Build the Gradio interface
# ---------------------------------------------------------------------------

def build_demo() -> gr.Blocks:
    settings = get_settings()
    init_db()

    # Gradio 6+: theme & css belong on launch(), not Blocks()
    with gr.Blocks(title=f"{settings.app.short_name} – {settings.app.title}") as demo:

        gr.HTML(
            f"""
            <h1 class="main-title">⚡ {settings.app.title}</h1>
            <p class="subtitle">{settings.app.description}</p>
            """
        )

        with gr.Row():
            refresh_btn = gr.Button("↻  Refresh Data", variant="primary", scale=0, min_width=160)
            status_text = gr.Markdown("Loading…", elem_id="status")

        with gr.Tabs():
            # ---------- Dashboard ----------
            with gr.Tab("Dashboard"):
                with gr.Row(equal_height=True):
                    with gr.Column(scale=5):
                        gauge_plot = gr.Plot(label="", show_label=False)
                    with gr.Column(scale=3, min_width=220):
                        score_html = gr.HTML(
                            "<div class='score-box'><div class='score-value'>…</div></div>"
                        )
                        regime_state = gr.State("—")

                gr.HTML("<div class='section-label'>Market Assets</div>")
                assets_html = gr.HTML("<p style='color:#64748b'>Loading…</p>")

                gr.HTML("<div class='section-label'>Contribution to Index</div>")
                contrib_plot = gr.Plot(label="", show_label=False)

            # ---------- History ----------
            with gr.Tab("History"):
                gr.Markdown(
                    "Snapshots are saved automatically each time data is refreshed. "
                    "History lives in a local SQLite file (or on the Space volume)."
                )
                history_plot = gr.Plot(label="", show_label=False)

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

| Window | Weight |
|--------|--------|
| 1 Hour | 10% |
| 4 Hours | 30% |
| 1 Day | 40% |
| 1 Week | 20% |

This reduces noise from very short-term moves while still reacting quickly.

### Normalization

A raw weighted sum is mapped to the 0–100 scale:

- Neutral (raw ≈ 0) sits around **20**
- Strong positive moves raise the score linearly toward 100
- Negative moves decay logarithmically so the gauge does not collapse too easily

### Important notes

- This is **not** a prediction engine. It is a *market-implied stress gauge*.
- Markets can be wrong, delayed, or driven by non-geopolitical factors.
- The index is most useful as an early-warning **complement** to news and analysis.
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

---
*Built with Gradio · Data via Yahoo Finance · Runs locally and on Hugging Face Spaces*
                    """
                )

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

# Theme + CSS are passed to launch() (Gradio 6+ requirement)
_THEME = gr.themes.Soft(
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
    button_primary_background_fill_hover="#2563eb",
)

if __name__ == "__main__":
    demo.launch(
        server_name="0.0.0.0",
        server_port=7860,
        theme=_THEME,
        css=CUSTOM_CSS,
    )
else:
    # When imported by HF Spaces / Gradio loader, attach theme & css
    # so the runtime still picks them up.
    demo.theme = _THEME
    # HF Gradio loader often respects css on the Blocks object as well
    try:
        demo.css = CUSTOM_CSS
    except Exception:
        pass
