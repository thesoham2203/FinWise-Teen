"""
Bank Nifty F&O Decision Support System
Streamlit Dashboard.

Run with: streamlit run run_dashboard.py
"""

import streamlit as st
import requests
from datetime import datetime
import time

# Page config
st.set_page_config(
    page_title="Bank Nifty DSS",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# API base URL
API_BASE = "http://localhost:8000/api/v1"

# Custom CSS
st.markdown("""
<style>
    /* Dark theme enhancements */
    .stApp {
        background: linear-gradient(180deg, #0e1117 0%, #1a1f2c 100%);
    }
    
    /* Card styling */
    .metric-card {
        background: linear-gradient(135deg, #1e2530 0%, #252d3a 100%);
        border-radius: 10px;
        padding: 15px;
        border: 1px solid #3a4556;
    }
    
    /* Header */
    .main-header {
        background: linear-gradient(90deg, #1e3a5f 0%, #2d5a87 100%);
        padding: 20px;
        border-radius: 10px;
        margin-bottom: 20px;
    }
    
    /* Status indicator */
    .status-live {
        color: #00C853;
        animation: pulse 2s infinite;
    }
    
    @keyframes pulse {
        0% { opacity: 1; }
        50% { opacity: 0.5; }
        100% { opacity: 1; }
    }
    
    /* No execution warning */
    .no-execution-banner {
        background: linear-gradient(90deg, #FF5722 0%, #FF9800 100%);
        padding: 10px 20px;
        border-radius: 5px;
        text-align: center;
        margin-bottom: 20px;
    }
</style>
""", unsafe_allow_html=True)


def fetch_api(endpoint: str) -> dict:
    """Fetch data from API endpoint."""
    try:
        response = requests.get(f"{API_BASE}{endpoint}", timeout=5)
        if response.status_code == 200:
            return response.json()
        return {"error": f"API returned {response.status_code}"}
    except requests.exceptions.ConnectionError:
        return {"error": "API not connected. Start the API server."}
    except Exception as e:
        return {"error": str(e)}


def render_header():
    """Render the main header."""
    st.markdown("""
    <div class="main-header">
        <h1 style="margin: 0; color: white;">📊 Bank Nifty Decision Support System</h1>
        <p style="margin: 5px 0 0 0; color: #90CAF9;">Human-in-the-loop F&O Trading Intelligence</p>
    </div>
    """, unsafe_allow_html=True)
    
    # No execution warning
    st.markdown("""
    <div class="no-execution-banner">
        <strong>⚠️ DECISION SUPPORT ONLY</strong> - No trade execution from this dashboard. 
        Execute manually through your broker.
    </div>
    """, unsafe_allow_html=True)


def render_market_status(data: dict):
    """Render market status section."""
    if "error" in data:
        st.error(f"Market data unavailable: {data['error']}")
        return
    
    col1, col2, col3, col4 = st.columns(4)
    
    spot = data.get("spot", {})
    futures = data.get("futures", {})
    vix = data.get("vix", {})
    options = data.get("options", {})
    
    with col1:
        ltp = spot.get("ltp", 0)
        change = spot.get("change", 0)
        change_pct = spot.get("change_pct", 0)
        delta_color = "normal" if change >= 0 else "inverse"
        st.metric(
            "Bank Nifty Spot",
            f"₹{ltp:,.2f}",
            delta=f"{change:+.0f} ({change_pct:+.2f}%)",
            delta_color=delta_color,
        )
    
    with col2:
        fut_ltp = futures.get("ltp", 0)
        basis = futures.get("basis", 0)
        st.metric(
            "Futures",
            f"₹{fut_ltp:,.2f}",
            delta=f"Basis: {basis:+.0f}",
        )
    
    with col3:
        vix_val = vix.get("value", 0)
        vix_change = vix.get("change_pct", 0)
        vix_dir = vix.get("direction", "stable")
        emoji = "📈" if vix_dir == "rising" else "📉" if vix_dir == "falling" else "➡️"
        st.metric(
            f"India VIX {emoji}",
            f"{vix_val:.2f}",
            delta=f"{vix_change:+.1f}%",
            delta_color="inverse" if vix_change > 0 else "normal",
        )
    
    with col4:
        pcr = options.get("pcr", 0)
        straddle = options.get("atm_straddle", 0)
        pcr_signal = "Bullish" if pcr > 1.2 else "Bearish" if pcr < 0.8 else "Neutral"
        st.metric(
            "PCR",
            f"{pcr:.2f}",
            delta=f"{pcr_signal} | Straddle: {straddle:.0f}",
        )


def main():
    """Main dashboard function."""
    render_header()
    
    # Sidebar
    with st.sidebar:
        st.markdown("### ⚙️ Controls")
        
        auto_refresh = st.toggle("Auto Refresh", value=True)
        refresh_interval = st.slider("Refresh (sec)", 1, 30, 5)
        
        st.markdown("---")
        
        # API Health
        health = fetch_api("/health")
        if "error" not in health:
            st.success("🟢 API Connected")
            components = health.get("components", {})
            for comp, status in components.items():
                emoji = "✅" if status else "❌"
                st.caption(f"{emoji} {comp}")
        else:
            st.error("🔴 API Disconnected")
            st.caption(health.get("error", ""))
        
        st.markdown("---")
        
        # Market status
        market = fetch_api("/market/status")
        if "error" not in market:
            status = market.get("status", "unknown")
            emoji = "🟢" if status == "open" else "🟡" if status == "opening_range" else "🔴"
            st.markdown(f"**Market:** {emoji} {status.upper()}")
            st.caption(f"Time: {market.get('current_time', '')}")
            st.caption(f"Hours: {market.get('market_open', '')} - {market.get('market_close', '')}")
        
        st.markdown("---")
        st.caption("Last update:")
        st.caption(datetime.now().strftime("%H:%M:%S"))
    
    # Main content
    st.markdown("### 📈 Market Overview")
    market_data = fetch_api("/market/data")
    render_market_status(market_data)
    
    st.markdown("---")
    
    # Two column layout
    col1, col2 = st.columns([1, 1])
    
    with col1:
        # Regime Panel
        from dashboard.components.regime_panel import render_regime_panel
        regime_data = fetch_api("/market/regime")
        if "error" not in regime_data:
            render_regime_panel(regime_data)
        else:
            st.error(f"Regime data unavailable: {regime_data.get('error', '')}")
    
    with col2:
        # Risk Panel
        from dashboard.components.risk_panel import render_risk_panel
        risk_data = fetch_api("/risk/status")
        if "error" not in risk_data:
            render_risk_panel(risk_data)
        else:
            st.error(f"Risk data unavailable: {risk_data.get('error', '')}")
    
    st.markdown("---")
    
    # Signal Panel
    from dashboard.components.signal_card import render_signal_card
    signal_data = fetch_api("/signals/current")
    render_signal_card(signal_data)
    
    st.markdown("---")
    
    # Trade Panel
    from dashboard.components.trade_panel import render_trade_panel, render_plans_list
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Current trade plan (if signal is valid)
        if signal_data.get("is_valid"):
            st.info("⚠️ Valid signal detected! Check your broker for execution.")
            # In production, you would fetch the trade plan here
        render_trade_panel(None)  # Will show placeholder
    
    with col2:
        # Today's plans
        plans = fetch_api("/trades/plans/today")
        if "error" not in plans:
            render_plans_list(plans.get("plans", []))
    
    # Auto refresh
    if auto_refresh:
        time.sleep(refresh_interval)
        st.rerun()


if __name__ == "__main__":
    main()
