import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
import math
from datetime import datetime, timedelta
import pandas as pd
import base64
from PIL import Image
import io

# --- CONFIG ---
REFRESH_INTERVAL = 180  # seconds (3 minutes)

# Asset configuration with logos
ASSETS = {
    "CL=F": {
        "name": "Crude Oil",
        "weight": 0.38,
        "logo": "🛢️",  # REPLACE WITH IMAGE PATH: "images/oil.png"
        "color": "#FF6B6B"
    },
    "GC=F": {
        "name": "Gold",
        "weight": 0.28,
        "logo": "🥇",  # REPLACE WITH IMAGE PATH: "images/gold.png"
        "color": "#FFD166"
    },
    "BTC-USD": {
        "name": "Bitcoin",
        "weight": 0.24,
        "logo": "₿",  # REPLACE WITH IMAGE PATH: "images/bitcoin.png"
        "color": "#F7931A"
    },
    "LMT": {
        "name": "Lockheed Martin",
        "weight": 0.10,
        "logo": "✈️",  # REPLACE WITH IMAGE PATH: "images/lockheed.png"
        "color": "#06D6A0"
    }
}

# Updated timeframe weights
TIMEFRAME_WEIGHTS = {
    "1h": 0.10,
    "4h": 0.30,
    "1d": 0.40,
    "1wk": 0.20
}

# --- FUNCTIONS ---
def get_background_image_base64():
    """Convert background image to base64 for CSS"""
    # REPLACE WITH YOUR BACKGROUND IMAGE:
    # Option 1: Use a local file
    # try:
    #     with open("background.jpg", "rb") as img_file:
    #         base64_string = base64.b64encode(img_file.read()).decode()
    #     return f"""
    #     background: url('data:image/jpeg;base64,{base64_string}');
    #     background-size: cover;
    #     background-position: center;
    #     background-attachment: fixed;
    #     """
    # except:
    #     # Fallback gradient
    #     return """
    #     background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
    #     """
    
    # Option 2: Use gradient (current)
    return """
    background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
    """

def get_asset_data(ticker, timeframe):
    """
    Fetch price change for a specific timeframe.
    Returns: (percent_change, current_price)
    """
    try:
        if timeframe == "1h":
            data = yf.download(ticker, period="1d", interval="5m", auto_adjust=False)
            if len(data) < 12:
                return 0.0, 0.0
            start_price = data['Close'].iloc[-12].item()
            end_price = data['Close'].iloc[-1].item()
            
        elif timeframe == "4h":
            data = yf.download(ticker, period="5d", interval="15m", auto_adjust=False)
            if len(data) < 16:
                return 0.0, 0.0
            start_price = data['Close'].iloc[-16].item()
            end_price = data['Close'].iloc[-1].item()
            
        elif timeframe == "1d":
            data = yf.download(ticker, period="5d", interval="1h", auto_adjust=False)
            if len(data) < 24:
                return 0.0, 0.0
            start_price = data['Close'].iloc[-24].item()
            end_price = data['Close'].iloc[-1].item()
            
        elif timeframe == "1wk":
            data = yf.download(ticker, period="1mo", interval="1d", auto_adjust=False)
            if len(data) < 5:
                return 0.0, 0.0
            start_price = data['Close'].iloc[-5].item()
            end_price = data['Close'].iloc[-1].item()
        
        current_price = end_price
        percent_change = ((end_price - start_price) / start_price) * 100.0
        return percent_change, current_price
        
    except Exception as e:
        st.warning(f"Error fetching {ticker} for {timeframe}: {e}")
        return 0.0, 0.0

def get_all_asset_data(ticker):
    """Get all timeframe data for a single asset"""
    data = {}
    current_price = None
    
    for timeframe in ["1wk", "1d", "4h", "1h"]:
        change, price = get_asset_data(ticker, timeframe)
        data[timeframe] = change
        if current_price is None and price > 0:
            current_price = price
    
    return data, current_price

def calculate_weighted_change(asset_data):
    """Calculate weighted change for an asset using all timeframes"""
    weighted_sum = 0
    for timeframe, change in asset_data.items():
        weighted_sum += change * TIMEFRAME_WEIGHTS[timeframe]
    return weighted_sum

def calculate_war_index(all_assets_data):
    """Calculate War Index using weighted assets with multi-timeframe data"""
    total_index = 0
    for ticker, asset_info in ASSETS.items():
        asset_data = all_assets_data[ticker]["data"]
        weighted_change = calculate_weighted_change(asset_data)
        total_index += weighted_change * asset_info["weight"]
    return float(total_index)

def normalize(raw_value, min_val=-5.0, max_val=5.0, baseline=20):
    """Normalize to 0-100 scale"""
    raw_value = float(raw_value)

    if raw_value >= 0:
        scaled = (raw_value / max_val) * (100 - baseline)
        normalized = baseline + scaled
    else:
        decay = (math.log1p(abs(raw_value)) / math.log1p(abs(min_val))) * baseline
        normalized = baseline - decay

    return max(0, min(100, int(normalized)))

# --- STREAMLIT UI ENHANCEMENTS ---
def set_page_config():
    """Set enhanced page configuration"""
    st.set_page_config(
        page_title="Middle-East Tension Index",
        page_icon="⚡",
        layout="wide",
        initial_sidebar_state="collapsed"
    )
    
    # Custom CSS for styling
    st.markdown(f"""
    <style>
    .stApp {{
        {get_background_image_base64()}
        background-attachment: fixed;
        background-size: cover;
    }}
    
    .main-header {{
        font-family: 'Arial Black', sans-serif;
        font-size: 3rem;
        color: white;
        text-align: center;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.5);
        margin-bottom: 1rem;
        padding-top: 1rem;
    }}
    
    .sub-header {{
        font-family: 'Arial', sans-serif;
        font-size: 1.2rem;
        color: #94a3b8;
        text-align: center;
        margin-bottom: 2rem;
    }}
    
    /* Updated asset card colors - dark blue theme */
    .asset-card {{
        background: rgba(30, 41, 59, 0.85);  /* Dark blue matching background */
        border: 1px solid rgba(100, 116, 139, 0.3);
        border-radius: 15px;
        padding: 20px;
        margin: 10px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.2);
        transition: transform 0.3s ease, box-shadow 0.3s ease;
        height: 220px;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
        backdrop-filter: blur(10px);
    }}
    
    .asset-card:hover {{
        transform: translateY(-5px);
        box-shadow: 0 8px 16px rgba(0,0,0,0.3);
        background: rgba(41, 51, 71, 0.9);
    }}
    
    .price-display {{
        font-family: 'Courier New', monospace;
        font-size: 1.5rem;
        font-weight: bold;
        color: #e2e8f0;
        margin: 10px 0;
    }}
    
    .positive-change {{
        color: #10b981;
        font-weight: bold;
        font-size: 1.5rem;
        text-shadow: 0 0 10px rgba(16, 185, 129, 0.3);
    }}
    
    .negative-change {{
        color: #ef4444;
        font-weight: bold;
        font-size: 1.5rem;
        text-shadow: 0 0 10px rgba(239, 68, 68, 0.3);
    }}
    
    .timeframe-selector {{
        background: rgba(30, 41, 59, 0.9);
        border: 1px solid rgba(100, 116, 139, 0.3);
        border-radius: 15px;
        padding: 20px;
        margin: 30px 0;
        text-align: center;
        backdrop-filter: blur(10px);
    }}
    
    .metric-box {{
        background: linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%);
        color: white;
        padding: 20px;
        border-radius: 15px;
        margin: 10px;
        text-align: center;
        border: 1px solid rgba(255, 255, 255, 0.1);
    }}
    
    .refresh-button {{
        position: absolute;
        top: 20px;
        right: 20px;
    }}
    
    .timeframe-btn {{
        margin: 5px;
    }}
    
    .asset-name {{
        font-size: 1.2rem;
        font-weight: bold;
        color: #e2e8f0;
        margin-bottom: 5px;
    }}
    
    .asset-logo {{
        font-size: 2.5rem;
        text-align: center;
        margin-bottom: 10px;
    }}
    
    /* For image logos */
    .asset-logo-img {{
        width: 50px;
        height: 50px;
        margin: 0 auto 15px auto;
        display: block;
    }}
    
    .weight-info {{
        background: rgba(30, 41, 59, 0.9);
        border-radius: 15px;
        padding: 20px;
        margin-top: 20px;
        border: 1px solid rgba(100, 116, 139, 0.3);
    }}
    
    .footer {{
        color: #94a3b8;
        text-align: center;
        margin-top: 30px;
        padding: 20px;
        font-size: 0.9rem;
    }}
    </style>
    """, unsafe_allow_html=True)

def create_asset_display(ticker, asset_data, current_price, selected_timeframe):
    """Create a fancy display for each asset"""
    asset_info = ASSETS[ticker]
    
    # Get change for selected timeframe
    change = asset_data[selected_timeframe]
    change_class = "positive-change" if change >= 0 else "negative-change"
    change_symbol = "▲" if change >= 0 else "▼"
    
    # For image logos (uncomment when you have images):
    # logo_html = f'<img src="data:image/png;base64,{get_image_base64(asset_info["logo"])}" class="asset-logo-img">'
    
    # For emoji logos (current):
    logo_html = f'<div class="asset-logo">{asset_info["logo"]}</div>'
    
    st.markdown(f"""
    <div class='asset-card'>
        {logo_html}
        <div class='asset-name' style='color: {asset_info["color"]};'>{asset_info['name']}</div>
        <div class='price-display'>${current_price:,.2f}</div>
        <div class='{change_class}' style='text-align: center;'>
            {change_symbol} {abs(change):.2f}%
        </div>
    </div>
    """, unsafe_allow_html=True)

# Helper function for image logos (uncomment when ready):
# def get_image_base64(image_path):
#     """Convert image to base64"""
#     try:
#         with open(image_path, "rb") as img_file:
#             return base64.b64encode(img_file.read()).decode()
#     except:
#         return ""

# --- MAIN APP ---
def main():
    set_page_config()
    
    # Header
    st.markdown("<h1 class='main-header'>⚡ Middle-East Tension Index Dashboard</h1>", 
                unsafe_allow_html=True)
    st.markdown("<p class='sub-header'>Real-time market-based geopolitical tension indicator</p>",
                unsafe_allow_html=True)
    
    # Small refresh button in top right
    col1, col2, col3 = st.columns([6, 1, 1])
    with col3:
        if st.button("🔄", help="Refresh data", key="refresh_btn"):
            st.rerun()
    
    # Fetch all data
    all_assets_data = {}
    with st.spinner("Fetching market data..."):
        for ticker in ASSETS.keys():
            data, current_price = get_all_asset_data(ticker)
            all_assets_data[ticker] = {
                "data": data,
                "current_price": current_price
            }
    
    # Calculate and display index
    raw_index = calculate_war_index(all_assets_data)
    war_index = normalize(raw_index)
    
    # Create gauge chart (SPEEDOMETER)
    fig = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=war_index,
        title={'text': "Tension Index", 'font': {'size': 28, 'color': 'white', 'family': 'Arial Black'}},
        delta={'reference': 50, 'increasing': {'color': "#ef4444"}, 'decreasing': {'color': "#10b981"}},
        number={'font': {'size': 50, 'color': 'white', 'family': 'Arial Black'}},
        gauge={
            'axis': {'range': [0, 100], 'tickwidth': 1, 'tickcolor': "white", 'tickfont': {'color': 'white'}},
            'bar': {'color': "#3b82f6", 'thickness': 0.25},
            'bgcolor': "rgba(0,0,0,0)",
            'borderwidth': 2,
            'bordercolor': "rgba(255,255,255,0.3)",
            'steps': [
                {'range': [0, 20], 'color': "rgba(16, 185, 129, 0.7)"},
                {'range': [20, 50], 'color': "rgba(250, 204, 21, 0.7)"},
                {'range': [50, 80], 'color': "rgba(249, 115, 22, 0.7)"},
                {'range': [80, 100], 'color': "rgba(239, 68, 68, 0.7)"}
            ],
            'threshold': {
                'line': {'color': "white", 'width': 4},
                'thickness': 0.75,
                'value': war_index
            }
        }
    ))
    
    fig.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font={'color': "white", 'family': "Arial"},
        height=400,
        margin=dict(t=80, b=80, l=50, r=50)
    )
    
    # Display gauge (SPEEDOMETER)
    st.plotly_chart(fig, use_container_width=True)
    
    # Display assets in a grid
    st.markdown("### 📊 Market Assets")
    asset_cols = st.columns(len(ASSETS))
    
    # Initialize session state for global timeframe selection
    if "selected_timeframe" not in st.session_state:
        st.session_state.selected_timeframe = "1h"
    
    selected_tf = st.session_state.selected_timeframe
    
    for idx, (ticker, asset_info) in enumerate(ASSETS.items()):
        with asset_cols[idx]:
            create_asset_display(
                ticker, 
                all_assets_data[ticker]["data"],
                all_assets_data[ticker]["current_price"],
                selected_tf
            )
    
    # Global timeframe selector (BELOW ASSETS)
    st.markdown("<div class='timeframe-selector'>", unsafe_allow_html=True)
    st.markdown("### 📈 Select Timeframe for All Assets")
    
    # Create timeframe buttons
    timeframes = {
        "1h": "1 Hour",
        "4h": "4 Hours", 
        "1d": "1 Day",
        "1wk": "1 Week"
    }
    
    cols = st.columns(4)
    for idx, (tf_key, tf_label) in enumerate(timeframes.items()):
        with cols[idx]:
            if st.button(
                tf_label, 
                key=f"tf_{tf_key}",
                type="primary" if st.session_state.selected_timeframe == tf_key else "secondary",
                width='stretch'
            ):
                st.session_state.selected_timeframe = tf_key
                st.rerun()
    
    st.markdown("</div>", unsafe_allow_html=True)
    
    # Display index values
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"""
        <div class='metric-box'>
            <h3>Raw Index</h3>
            <h2>{raw_index:.2f}</h2>
            <p>Weighted average of all assets</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class='metric-box'>
            <h3>Normalized Index</h3>
            <h2>{war_index}/100</h2>
            <p>Current tension level</p>
        </div>
        """, unsafe_allow_html=True)
    
    # Weight information (BELOW TIMEFRAME SELECTOR)
    st.markdown("<div class='weight-info'>", unsafe_allow_html=True)
    with st.expander("📊 View Weight Information", expanded=False):
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**### Asset Weights**")
            for ticker, info in ASSETS.items():
                st.markdown(f"""
                <div style='display: flex; align-items: center; margin: 10px 0;'>
                    <span style='font-size: 1.5rem; margin-right: 10px;'>{info['logo']}</span>
                    <span style='flex-grow: 1;'>{info['name']}</span>
                    <span style='font-weight: bold; color: {info["color"]};'>{info['weight']*100:.0f}%</span>
                </div>
                """, unsafe_allow_html=True)
        
        with col2:
            st.markdown("**### Timeframe Weights**")
            for tf, weight in TIMEFRAME_WEIGHTS.items():
                tf_label = {
                    "1h": "1 Hour",
                    "4h": "4 Hours",
                    "1d": "1 Day",
                    "1wk": "1 Week"
                }[tf]
                st.markdown(f"""
                <div style='display: flex; align-items: center; margin: 10px 0;'>
                    <span style='flex-grow: 1;'>{tf_label}</span>
                    <span style='font-weight: bold; color: #3b82f6;'>{weight*100:.0f}%</span>
                </div>
                """, unsafe_allow_html=True)
            
            # Show calculation formula
            st.markdown("---")
            st.markdown("**### Calculation Formula**")
            st.markdown("""
            ```
            Raw Index = Σ(Asset_Weight × Σ(Timeframe_Weight × %Change))
            Normalized = Map(Raw_Index) to 0-100 scale
            ```
            """)
    
    st.markdown("</div>", unsafe_allow_html=True)
    
    # Footer
    st.markdown("<div class='footer'>", unsafe_allow_html=True)
    st.markdown(f"""
    <div style='text-align: center;'>
        <p>🕐 Data updates every {REFRESH_INTERVAL//60} minutes • Last update: {datetime.now().strftime('%H:%M:%S')}</p>
        <p>⚡ Middle-East Tension Index v1.0 • Powered by Yahoo Finance</p>
    </div>
    """, unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

if __name__ == "__main__":
    main()
