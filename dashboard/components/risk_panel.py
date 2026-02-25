"""
Risk Panel Component.

Displays current risk state and limits.
"""

import streamlit as st
from typing import Dict, Any


def get_status_style(status: str) -> tuple:
    """Get color and emoji for status."""
    styles = {
        "normal": ("#4CAF50", "🟢"),
        "caution": ("#FFC107", "🟡"),
        "warning": ("#FF9800", "🟠"),
        "critical": ("#FF5722", "🔴"),
        "shutdown": ("#F44336", "⛔"),
    }
    return styles.get(status, ("#757575", "⚪"))


def render_risk_panel(risk_data: Dict[str, Any]) -> None:
    """
    Render the risk status panel.
    
    Args:
        risk_data: Risk state from API
    """
    st.subheader("🛡️ Risk Status")
    
    if not risk_data or risk_data.get("status") == "not_initialized":
        st.info("Risk state not initialized")
        return
    
    status = risk_data.get("status", "normal")
    can_trade = risk_data.get("can_trade", False)
    
    color, emoji = get_status_style(status)
    
    # Status banner
    if can_trade:
        st.success(f"{emoji} **Status: {status.upper()}** - Trading Allowed")
    else:
        reason = risk_data.get("reason", "Unknown")
        st.error(f"{emoji} **Status: {status.upper()}**")
        st.caption(f"Reason: {reason}")
    
    # Hard shutdown warning
    if risk_data.get("hard_shutdown"):
        st.markdown(
            """
            <div style="
                background: linear-gradient(135deg, #F44336, #D32F2F);
                padding: 15px;
                border-radius: 10px;
                text-align: center;
                margin: 10px 0;
            ">
                <h3 style="color: white; margin: 0;">⛔ HARD SHUTDOWN ACTIVE</h3>
                <p style="color: #ffcdd2; margin: 5px 0;">Trading disabled for the day</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
    
    st.markdown("---")
    
    # Trade count
    col1, col2 = st.columns(2)
    
    with col1:
        trades_taken = risk_data.get("trades_taken", 0)
        trades_remaining = risk_data.get("trades_remaining", 2)
        total_trades = trades_taken + trades_remaining
        
        st.markdown("**Trades Today**")
        st.progress(trades_taken / total_trades if total_trades > 0 else 0)
        st.metric(
            "Count",
            f"{trades_taken} / {total_trades}",
            delta=f"{trades_remaining} remaining",
            delta_color="normal" if trades_remaining > 0 else "inverse",
        )
    
    with col2:
        total_pnl = risk_data.get("total_pnl", 0)
        pnl_pct = risk_data.get("pnl_percentage", 0)
        
        st.markdown("**P&L Today**")
        pnl_color = "#4CAF50" if total_pnl >= 0 else "#F44336"
        
        st.markdown(
            f"""
            <div style="
                font-size: 1.5em;
                font-weight: bold;
                color: {pnl_color};
            ">
                ₹{total_pnl:+,.0f}
            </div>
            <div style="color: {pnl_color}; font-size: 0.9em;">
                ({pnl_pct:+.2f}%)
            </div>
            """,
            unsafe_allow_html=True,
        )
    
    st.markdown("---")
    
    # Additional metrics
    col1, col2, col3 = st.columns(3)
    
    with col1:
        consecutive = risk_data.get("consecutive_losses", 0)
        emoji = "✅" if consecutive == 0 else "⚠️" if consecutive == 1 else "🔴"
        st.metric(
            "Consecutive Losses",
            f"{emoji} {consecutive}",
            delta="Safe" if consecutive < 2 else "DANGER",
            delta_color="normal" if consecutive < 2 else "inverse",
        )
    
    with col2:
        remaining_capacity = risk_data.get("remaining_risk_capacity", 0)
        st.metric(
            "Risk Capacity",
            f"₹{remaining_capacity:,.0f}",
        )
    
    with col3:
        max_loss = remaining_capacity * -1 + risk_data.get("total_pnl", 0)
        st.metric(
            "Max Today Loss",
            f"₹{abs(max_loss):,.0f}",
        )


def render_risk_dashboard(risk_data: Dict[str, Any]) -> None:
    """
    Render comprehensive risk dashboard.
    
    Args:
        risk_data: Risk state from API
    """
    render_risk_panel(risk_data)
    
    st.markdown("---")
    st.subheader("📏 Risk Limits")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Max Trades/Day", "2")
    
    with col2:
        st.metric("Max Daily Loss", "1.5%")
    
    with col3:
        st.metric("Max Consecutive SL", "2")
    
    with col4:
        st.metric("Min Risk:Reward", "1:2")
    
    # Risk rules reminder
    with st.expander("📋 Risk Rules", expanded=False):
        st.markdown("""
        **Automatic Controls:**
        1. Maximum 2 trades per day - hard limit
        2. Maximum 1.5% daily loss - triggers shutdown
        3. After 2 consecutive stop-losses - hard shutdown
        4. Trades with R:R < 1:2 are auto-rejected
        5. SL moves to breakeven after 50% target reached
        
        **No Override Options:**
        - These rules cannot be bypassed
        - System enforces discipline automatically
        """)
