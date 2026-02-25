"""
Trade Panel Component.

Displays trade plans and history.
NO execution buttons - display only!
"""

import streamlit as st
from typing import Dict, Any, List


def get_direction_style(direction: str) -> tuple:
    """Get color and emoji for direction."""
    if direction in ["LONG", "long"]:
        return "#00C853", "🟢", "📈"
    elif direction in ["SHORT", "short"]:
        return "#FF1744", "🔴", "📉"
    return "#757575", "⚪", "➡️"


def get_status_badge(status: str) -> str:
    """Get badge for plan status."""
    badges = {
        "pending": "🟡 Pending",
        "active": "🟢 Active",
        "executed": "✅ Executed",
        "cancelled": "⚫ Cancelled",
        "expired": "⏰ Expired",
        "rejected": "❌ Rejected",
    }
    return badges.get(status, status)


def render_trade_panel(plan_data: Dict[str, Any] = None) -> None:
    """
    Render trade plan display panel.
    
    Args:
        plan_data: Trade plan data (optional)
    """
    st.subheader("📋 Trade Plan")
    
    if not plan_data:
        st.info("No active trade plan. Wait for a valid signal.")
        st.caption("Trade plans appear here when signals meet all criteria.")
        return
    
    direction = plan_data.get("direction", "UNKNOWN")
    instrument = plan_data.get("instrument", "")
    is_valid = plan_data.get("is_valid", False)
    status = plan_data.get("status", "pending")
    
    color, emoji, arrow = get_direction_style(direction)
    
    # Plan header
    st.markdown(
        f"""
        <div style="
            background: linear-gradient(135deg, {color}22, transparent);
            border: 2px solid {color};
            border-radius: 10px;
            padding: 15px;
            margin-bottom: 15px;
        ">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <div>
                    <h3 style="color: {color}; margin: 0;">
                        {arrow} {direction} {instrument}
                    </h3>
                    <span style="
                        background: {color}44;
                        padding: 2px 8px;
                        border-radius: 4px;
                        font-size: 0.8em;
                    ">
                        {get_status_badge(status)}
                    </span>
                </div>
                <div style="text-align: right;">
                    <span style="color: {'#4CAF50' if is_valid else '#FF5722'};">
                        {'✅ Valid' if is_valid else '❌ Invalid'}
                    </span>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    
    # Entry zone
    entry_zone = plan_data.get("entry_zone", {})
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Entry Zone", f"{entry_zone.get('lower', 0):.2f} - {entry_zone.get('upper', 0):.2f}")
    
    with col2:
        st.metric("Optimal Entry", f"{entry_zone.get('optimal', 0):.2f}")
    
    with col3:
        st.metric("Stop Loss", f"{plan_data.get('stop_loss', 0):.2f}")
    
    # Targets
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Target 1", f"{plan_data.get('target_1', 0):.2f}")
    
    with col2:
        st.metric("Target 2", f"{plan_data.get('target_2', 0):.2f}")
    
    with col3:
        rr = plan_data.get("risk_reward", 0)
        rr_color = "normal" if rr >= 2 else "inverse"
        st.metric("Risk:Reward", f"1:{rr:.1f}", delta="Good" if rr >= 2 else "Low", delta_color=rr_color)
    
    # Position sizing
    st.markdown("---")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Position Size", f"{plan_data.get('position_size', 0)} lots")
    
    with col2:
        st.metric("Risk Amount", f"₹{plan_data.get('risk_amount', 0):,.0f}")
    
    with col3:
        confidence = plan_data.get("confidence", 0)
        st.metric("Confidence", f"{confidence:.0%}")
    
    # Rejection reasons if invalid
    if not is_valid:
        rejection_reasons = plan_data.get("rejection_reasons", [])
        if rejection_reasons:
            st.markdown("**⚠️ Rejection Reasons:**")
            for reason in rejection_reasons:
                st.caption(f"• {reason}")
    
    # Reasoning (expandable)
    reasoning = plan_data.get("reasoning", [])
    if reasoning:
        with st.expander("🔍 Trade Reasoning", expanded=False):
            for reason in reasoning:
                st.markdown(f"- {reason}")
    
    # Important notice
    st.markdown("---")
    st.info(
        "👤 **Human-in-the-loop**: Review this plan carefully. "
        "Execute manually through your broker if you agree with the analysis. "
        "**No trade execution from this dashboard.**"
    )


def render_trades_history(trades: List[Dict[str, Any]]) -> None:
    """
    Render trade history.
    
    Args:
        trades: List of executed trades
    """
    st.subheader("📊 Trade History")
    
    if not trades:
        st.info("No trade history available")
        return
    
    # Summary stats
    total_trades = len(trades)
    winners = sum(1 for t in trades if t.get("is_winner"))
    total_pnl = sum(t.get("pnl_amount", 0) for t in trades)
    win_rate = winners / total_trades * 100 if total_trades > 0 else 0
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Trades", total_trades)
    
    with col2:
        st.metric("Win Rate", f"{win_rate:.0f}%")
    
    with col3:
        st.metric("Winners", winners)
    
    with col4:
        pnl_color = "#4CAF50" if total_pnl >= 0 else "#F44336"
        st.metric("Total P&L", f"₹{total_pnl:+,.0f}")
    
    st.markdown("---")
    
    # Trade list
    for trade in trades[:20]:
        direction = trade.get("direction", "")
        color, emoji, _ = get_direction_style(direction)
        is_winner = trade.get("is_winner")
        pnl = trade.get("pnl_amount", 0)
        
        result_emoji = "✅" if is_winner else "❌" if is_winner is False else "⏳"
        pnl_text = f"₹{pnl:+,.0f}" if pnl != 0 else "Open"
        
        st.markdown(
            f"""
            <div style="
                display: flex;
                justify-content: space-between;
                align-items: center;
                padding: 10px 15px;
                border-left: 3px solid {color};
                background: {color}11;
                margin-bottom: 8px;
                border-radius: 0 8px 8px 0;
            ">
                <div>
                    <strong>{emoji} {trade.get('instrument', '')}</strong>
                    <br>
                    <span style="color: #888; font-size: 0.8em;">
                        Entry: {trade.get('entry_price', 0):.2f}
                    </span>
                </div>
                <div style="text-align: right;">
                    <span style="color: {'#4CAF50' if pnl > 0 else '#F44336' if pnl < 0 else '#888'};">
                        {pnl_text}
                    </span>
                    <br>
                    <span>{result_emoji}</span>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )


def render_plans_list(plans: List[Dict[str, Any]]) -> None:
    """
    Render list of today's trade plans.
    
    Args:
        plans: List of trade plans
    """
    st.subheader("📋 Today's Plans")
    
    if not plans:
        st.info("No trade plans generated today")
        return
    
    for plan in plans[:10]:
        direction = plan.get("direction", "")
        color, emoji, _ = get_direction_style(direction)
        status = plan.get("status", "pending")
        is_valid = plan.get("is_valid", False)
        
        st.markdown(
            f"""
            <div style="
                display: flex;
                justify-content: space-between;
                align-items: center;
                padding: 10px 15px;
                border-left: 3px solid {color};
                background: {color}11;
                margin-bottom: 8px;
                border-radius: 0 8px 8px 0;
            ">
                <div>
                    <strong>{emoji} {plan.get('instrument', '')}</strong>
                    <span style="
                        background: {'#4CAF5044' if is_valid else '#FF572244'};
                        padding: 2px 6px;
                        border-radius: 3px;
                        font-size: 0.7em;
                        margin-left: 5px;
                    ">{'✅ Valid' if is_valid else '❌ Invalid'}</span>
                </div>
                <div>
                    <span style="background: #ffffff22; padding: 2px 8px; border-radius: 4px; font-size: 0.8em;">
                        {get_status_badge(status)}
                    </span>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
