# Version 0.1: The Initial Prototype

**The first working proof-of-concept, built to test the core hypothesis: Can market data serve as an early geopolitical warning signal?**

## 📋 Overview
This initial version was created to validate the project's foundational idea. It's a minimal, functional Streamlit application that fetches real-time data for four key assets, applies a simple weighted formula, and displays the calculated tension index on a basic gauge.

## 🛠️ Core Features
*   **Real-Time Data:** Fetches live price data for Crude Oil (`CL=F`), Gold (`GC=F`), Bitcoin (`BTC-USD`), and Lockheed Martin (`LMT`) via the `yfinance` API.
*   **Basic Formula:** Calculates a raw "War Index" using fixed asset weights (Oil: 38%, Gold: 28%, Bitcoin: 24%, LMT: 10%).
*   **Simple Visualization:** Displays the normalized index (0-100) on a Plotly gauge/speedometer.
*   **Auto-Refresh:** Updates data every 3 minutes to provide a near-live view.

## 🎨 UI/UX - The MVP Dashboard
![v0.1 Dashboard Screenshot](../../screenshots/v0.1_dashboard_1.png)

The interface is purposefully minimal, focusing solely on functionality:
1.  **Central Gauge:** The primary visual output. Shows the computed Middle-East Tension Index.
2.  **Asset Metrics:** A simple row displaying the percentage change for each of the four tracked assets.
3.  **Index Values:** Shows both the raw calculated value and the final normalized score.
4.  **Manual Refresh:** A button to manually trigger a data update.

## ⚙️ Technical Implementation
*   **Framework:** Built with Streamlit for rapid prototyping.
*   **Data Source:** Yahoo Finance (`yfinance`).
*   **Visualization:** Plotly for the interactive gauge.
*   **Logic:** A single timeframe (5-minute intervals) is used for percent change calculation.

## 🧪 Purpose & Learning
This version served as a critical proof-of-concept. It successfully demonstrated that a simple, automated dashboard could:
1.  Reliably pull and process real-time financial data.
2.  Translate that data into a single, interpretable metric.
3.  Form a valid foundation for a more sophisticated analytical tool.

**This is the seed from which the entire project grew.**

---

### How to Run This Version
```bash
# Navigate to this directory
cd versions/v0.1

# Install dependencies
pip install -r requirements.txt

# Launch the dashboard
streamlit run dashboard.py
