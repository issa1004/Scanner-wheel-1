import streamlit as st
import pandas as pd

st.set_page_config(page_title="Wheel Scanner Mobile", page_icon="⚡", layout="centered")

st.markdown("""
    <style>
    .block-container { padding-top: 1rem; padding-bottom: 2rem; }
    .opportunity-card {
        background-color: #1e293b;
        border-radius: 12px;
        padding: 16px;
        margin-bottom: 12px;
        border-left: 6px solid #22c55e;
        color: white;
    }
    .badge-score {
        background-color: #22c55e;
        color: black;
        font-weight: bold;
        padding: 4px 8px;
        border-radius: 20px;
        float: right;
    }
    </style>
""", unsafe_allow_html=True)

st.title("⚡ Wheel Scanner IBKR")

profile = st.radio(
    "Profil de stratégie :",
    ["🟢 Conservative", "🟡 Balanced", "🔴 Aggressive"],
    horizontal=True
)

with st.expander("⚙️ Ajuster tous les filtres"):
    markets = st.multiselect("Marchés :", ["🇺🇸 NASDAQ", "🇺🇸 NYSE", "🇨🇦 TSX", "🇪🇺 EU", "🇸🇬 SG"], default=["🇺🇸 NASDAQ", "🇺🇸 NYSE"])
    col1, col2 = st.columns(2)
    ema_fast = col1.selectbox("EMA Rapide", [9, 12, 20], index=2)
    ema_slow = col2.selectbox("EMA Lente", [21, 26, 50], index=2)
    cross_days = st.slider("Fenêtre croisement (jours)", 1, 30, 5)
    min_price = col1.number_input("Prix Min ($)", value=20.0)
    max_price = col2.number_input("Prix Max ($)", value=150.0)
    min_volume = st.number_input("Volume Min", value=1000000)

if st.button("🚀 Lancer le Scan Mobile", type="primary", use_container_width=True):
    st.toast("Analyse des chaînes d'options en cours...", icon="🔄")
    
    mock_results = [
        {"ticker": "AAPL", "strike": 215, "dte": 14, "delta": -0.24, "premium": 1.45, "score": 94, "rsi": 48.5},
        {"ticker": "MSFT", "strike": 410, "dte": 21, "delta": -0.21, "premium": 2.80, "score": 89, "rsi": 52.1},
        {"ticker": "NVDA", "strike": 115, "dte": 10, "delta": -0.28, "premium": 1.95, "score": 85, "rsi": 59.0},
    ]
    
    st.subheader("🔥 Top opportunités Wheel")
    for item in mock_results:
        st.markdown(f"""
        <div class="opportunity-card">
            <span class="badge-score">Score: {item['score']}/100</span>
            <h3 style="margin:0; color:#38bdf8;">{item['ticker']} — PUT ${item['strike']}</h3>
            <p style="margin:5px 0 0 0; font-size:14px; color:#cbd5e1;">
                <b>Prime:</b> ${item['premium']} &nbsp;|&nbsp; 
                <b>DTE:</b> {item['dte']}j &nbsp;|&nbsp; 
                <b>Delta:</b> {item['delta']} &nbsp;|&nbsp; 
                <b>RSI:</b> {item['rsi']}
            </p>
        </div>
        """, unsafe_allow_html=True)
