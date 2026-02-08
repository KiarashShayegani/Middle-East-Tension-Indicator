import streamlit as st
import yfinance as yf
import time
import plotly.graph_objects as go
import math

# --- CONFIG ---
REFRESH_INTERVAL = 180  # seconds (3 minutes)

# --- FUNCTIONS ---
def get_percent_change(ticker):
    """
    Fetch percent change for a ticker over the last day (5m interval).
    Always returns a float.
    """
    try:
        # Explicitly set auto_adjust to avoid future warning
        data = yf.download(ticker, period="1d", interval="5m", auto_adjust=False)
        if len(data) < 2:
            return 0.0
        # Use .item() instead of float(Series) to avoid deprecation warning
        start_price = data['Close'].iloc[0].item()
        end_price = data['Close'].iloc[-1].item()
        return ((end_price - start_price) / start_price) * 100.0
    except Exception as e:
        st.warning(f"Error fetching {ticker}: {e}")
        return 0.0

def calculate_war_index(oil, gold, btc, other):
    """Weighted formula for War Index raw value."""
    return float((0.38 * oil) + (0.28 * gold) + (0.24 * btc) + (0.10 * other))

def normalize(raw_value, min_val=-5.0, max_val=5.0, baseline=20):
    """
    Map raw_value (-5 to +5) into 0–100 scale with baseline tension.
    - Neutral (raw=0) ~ baseline (20).
    - Negative raw → logarithmic decay below baseline.
    - Positive raw → linear growth above baseline.
    """
    raw_value = float(raw_value)

    if raw_value >= 0:
        # Positive raw → linear growth above baseline
        scaled = (raw_value / max_val) * (100 - baseline)
        normalized = baseline + scaled
    else:
        # Negative raw → logarithmic decay below baseline
        decay = (math.log1p(abs(raw_value)) / math.log1p(abs(min_val))) * baseline
        normalized = baseline - decay

    # Clamp
    if normalized < 0:
        normalized = 0
    if normalized > 100:
        normalized = 100

    return int(normalized)

# --- STREAMLIT UI ---
st.title("Middle-East Tension Index (v0.1)")

# --- OPTION 1: Manual Refresh Button ---
if st.button("Manual Refresh"):
    st.rerun()

# --- OPTION 2: Automatic Refresh (comment out if not needed) ---
placeholder = st.empty()
with placeholder.container():
    # Fetch market signals
    oil_change = get_percent_change("CL=F")   # Crude Oil Futures
    gold_change = get_percent_change("GC=F")  # Gold Futures
    btc_change = get_percent_change("BTC-USD") # Bitcoin
    other_change = get_percent_change("LMT")  # Example: Lockheed Martin

    # Calculate index
    raw_index = calculate_war_index(oil_change, gold_change, btc_change, other_change)
    war_index = normalize(raw_index)

    # --- Speedometer Gauge first ---
    fig = go.Figure(go.Indicator(
        mode = "gauge+number",
        value = war_index,
        title = {'text': "War Predictor Index"},
        gauge = {
            'axis': {'range': [0, 100]},
            'bar': {'color': "darkred"},
            'steps': [
                {'range': [0, 20], 'color': "green"},
                {'range': [20, 50], 'color': "yellow"},
                {'range': [50, 80], 'color': "orange"},
                {'range': [80, 100], 'color': "red"}
            ],
        }
    ))
    st.plotly_chart(fig, width='stretch')

    # --- Metrics in one row ---
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Oil", f"{oil_change:.2f}%")
    col2.metric("Gold", f"{gold_change:.2f}%")
    col3.metric("BTC", f"{btc_change:.2f}%")
    col4.metric("LMT", f"{other_change:.2f}%")

    # --- Index values below ---
    st.write(f"**Raw War Index:** {raw_index:.2f}")
    st.write(f"**Normalized War Index (0–100):** {war_index}")

# Sleep + rerun for auto-refresh
time.sleep(REFRESH_INTERVAL)
st.rerun()
