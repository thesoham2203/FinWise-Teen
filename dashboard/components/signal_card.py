"""
Signal Card Component.

Displays trade signals with full reasoning chain.
"""

import streamlit as st
from typing import Dict, Any, List


def get_direction_style(direction: str) -> tuple:
    """Get color and emoji for direction."""
    if direction == "LONG":
        return "#00C853", "🟢", "📈"
    elif direction == "SHORT":
        return "#FF1744", "🔴", "📉"
    return "#757575", "⚪", "➡️"


def render_signal_card(signal_data: Dict[str, Any]) -> None:
    """
    Render a trade signal card.
    
    Args:
        signal_data: Signal data from API
    """
    st.subheader("📡 Current Signal")
    
    if not signal_data:
        st.info("No signal data available")
        return
    
    # Check if buffer is filling
    if signal_data.get("status") == "buffer_filling":
        st.warning(f"⏳ {signal_data.get('message', 'Buffer filling...')}")
        st.progress(signal_data.get("buffer_fill", 0) / 100)
        return
    
    direction = signal_data.get("direction", "NEUTRAL")
    is_valid = signal_data.get("is_valid", False)
    total_score = signal_data.get("total_score", 0)
    
    color, emoji, arrow = get_direction_style(direction)
    
    # Main signal card
    border_color = color if is_valid else "#757575"
    bg_alpha = "33" if is_valid else "11"
    
    st.markdown(
        f"""
        <div style="
            background: linear-gradient(135deg, {color}{bg_alpha}, transparent);
            border: 2px solid {border_color};
            border-radius: 15px;
            padding: 20px;
            margin-bottom: 20px;
        ">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <div>
                    <h2 style="color: {color}; margin: 0;">
                        {arrow} {direction}
                    </h2>
                    <p style="color: {'#4CAF50' if is_valid else '#FF5722'}; margin: 5px 0;">
                        {'✅ VALID SIGNAL' if is_valid else '❌ INVALID SIGNAL'}
                    </p>
                </div>
                <div style="text-align: right;">
                    <h3 style="color: #fff; margin: 0;">Score</h3>
                    <h2 style="color: {color}; margin: 0;">{total_score:.1f}</h2>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    
    # Component scores
    col1, col2, col3 = st.columns(3)
    
    regime = signal_data.get("regime", {})
    confluence = signal_data.get("confluence", {})
    options = signal_data.get("options", {})
    
    with col1:
        st.markdown("**Regime**")
        regime_ok = regime.get("trade_allowed", False)
        st.metric(
            "Status",
            "✅ OK" if regime_ok else "❌ Blocked",
            delta=regime.get("type", "").replace("_", " ").title(),
        )
    
    with col2:
        st.markdown("**Confluence**")
        conf_score = confluence.get("score", 0)
        is_eligible = confluence.get("is_eligible", False)
        st.metric(
            "Score",
            f"{conf_score:.1f}/10",
            delta="Eligible" if is_eligible else "Not Eligible",
            delta_color="normal" if is_eligible else "inverse",
        )
    
    with col3:
        st.markdown("**Options Intel**")
        has_conflict = options.get("has_conflict", False)
        confidence = options.get("confidence", 0)
        st.metric(
            "Status",
            "⚠️ Conflict" if has_conflict else f"✅ {confidence:.0%}",
            delta=f"PCR: {options.get('pcr', 0):.2f}",
        )
    
    # Validity reasons
    if not is_valid:
        st.markdown("---")
        st.markdown("**⚠️ Why Invalid:**")
        validity_reasons = signal_data.get("validity_reasons", [])
        if validity_reasons:
            for reason in validity_reasons[:5]:
                st.caption(f"• {reason}")
        else:
            st.caption("• No clear directional alignment")
    
    # Reasoning chain (expandable)
    reasoning = signal_data.get("reasoning", [])
    if reasoning:
        with st.expander("🔍 Full Reasoning Chain", expanded=False):
            for i, reason in enumerate(reasoning[:15], 1):
                st.markdown(f"{i}. {reason}")
    
    # Timestamp
    timestamp = signal_data.get("timestamp", "")
    st.caption(f"Generated: {timestamp}")


def render_signal_history(signals: List[Dict[str, Any]]) -> None:
    """
    Render signal history list.
    
    Args:
        signals: List of historical signals
    """
    st.subheader("📜 Signal History")
    
    if not signals:
        st.info("No signal history available")
        return
    
    for signal in signals[:10]:
        direction = signal.get("direction", "NEUTRAL")
        is_valid = signal.get("is_valid", False)
        timestamp = signal.get("timestamp", "")
        
        color, emoji, _ = get_direction_style(direction)
        valid_badge = "✅" if is_valid else "❌"
        
        st.markdown(
            f"""
            <div style="
                display: flex;
                justify-content: space-between;
                padding: 8px 12px;
                border-left: 3px solid {color};
                background: {color}11;
                margin-bottom: 5px;
                border-radius: 0 5px 5px 0;
            ">
                <span>{emoji} {direction}</span>
                <span>{valid_badge}</span>
                <span style="color: #888; font-size: 0.8em;">{timestamp[:16]}</span>
            </div>
            """,
            unsafe_allow_html=True,
        )
