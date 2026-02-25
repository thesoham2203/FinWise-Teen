"""
Market Regime Panel Component.

Displays current market regime with color coding and details.
"""

import streamlit as st
from typing import Dict, Any


def get_regime_color(regime: str) -> str:
    """Get color for regime type."""
    colors = {
        "trending_bullish": "#00C853",  # Green
        "trending_bearish": "#FF1744",  # Red
        "range_bound": "#FFC107",       # Amber
        "volatile": "#9C27B0",          # Purple
        "pre_breakout": "#2196F3",      # Blue
        "opening_range": "#FF9800",     # Orange
        "no_trade": "#757575",          # Grey
    }
    return colors.get(regime, "#757575")


def get_volatility_icon(volatility: str) -> str:
    """Get icon for volatility level."""
    icons = {
        "low": "🟢",
        "normal": "🟡",
        "high": "🟠",
        "extreme": "🔴",
    }
    return icons.get(volatility, "⚪")


def render_regime_panel(regime_data: Dict[str, Any]) -> None:
    """
    Render the market regime panel.
    
    Args:
        regime_data: Regime classification data from API
    """
    st.subheader("📊 Market Regime")
    
    if not regime_data:
        st.warning("No regime data available")
        return
    
    regime = regime_data.get("regime", "unknown")
    volatility = regime_data.get("volatility", "normal")
    trade_allowed = regime_data.get("trade_allowed", False)
    
    # Main regime display
    regime_color = get_regime_color(regime)
    vol_icon = get_volatility_icon(volatility)
    
    # Regime badge
    st.markdown(
        f"""
        <div style="
            background: linear-gradient(135deg, {regime_color}22, {regime_color}44);
            border: 2px solid {regime_color};
            border-radius: 10px;
            padding: 15px;
            margin-bottom: 15px;
        ">
            <h3 style="color: {regime_color}; margin: 0;">
                {regime.replace('_', ' ').upper()}
            </h3>
            <p style="margin: 5px 0 0 0; color: #ccc;">
                {vol_icon} {volatility.upper()} Volatility
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    
    # Trade allowed status
    if trade_allowed:
        st.success("✅ **Trading Allowed**")
    else:
        st.error("❌ **Trading NOT Allowed**")
        if regime_data.get("rejection_reasons"):
            for reason in regime_data["rejection_reasons"][:3]:
                st.caption(f"• {reason}")
    
    # Metrics row
    col1, col2, col3 = st.columns(3)
    
    with col1:
        atr_ratio = regime_data.get("atr_ratio", 1.0)
        st.metric(
            "ATR Ratio",
            f"{atr_ratio:.2f}x",
            delta="High" if atr_ratio > 1.3 else "Normal",
        )
    
    with col2:
        vwap_slope = regime_data.get("vwap_slope", 0)
        direction = "↗" if vwap_slope > 0 else "↘" if vwap_slope < 0 else "→"
        st.metric(
            "VWAP Slope",
            f"{direction} {abs(vwap_slope):.4f}",
        )
    
    with col3:
        price_vs_vwap = regime_data.get("price_vs_vwap", "at")
        emoji = "📈" if price_vs_vwap == "above" else "📉" if price_vs_vwap == "below" else "➡️"
        st.metric(
            "Price vs VWAP",
            f"{emoji} {price_vs_vwap.upper()}",
        )
    
    # VIX info
    st.markdown("---")
    col1, col2 = st.columns(2)
    
    with col1:
        vix_dir = regime_data.get("vix_direction", "stable")
        vix_emoji = "📈" if vix_dir == "rising" else "📉" if vix_dir == "falling" else "➡️"
        st.metric("VIX Direction", f"{vix_emoji} {vix_dir.upper()}")
    
    with col2:
        vix_level = regime_data.get("vix_level", "normal")
        st.metric("VIX Level", vix_level.upper())
    
    # Allowed setups
    allowed_setups = regime_data.get("allowed_setups", [])
    if allowed_setups:
        st.markdown("**Allowed Setups:**")
        setup_str = " • ".join([s.replace("_", " ").title() for s in allowed_setups])
        st.caption(setup_str)
    
    # Regime reasons (expandable)
    with st.expander("📝 Regime Analysis", expanded=False):
        reasons = regime_data.get("regime_reasons", [])
        for reason in reasons:
            st.markdown(f"- {reason}")
