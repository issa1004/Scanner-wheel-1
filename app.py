
import streamlit as st
import pandas as pd
import numpy as np

# Configuration de la page optimisée mobile
st.set_page_config(
    page_title="Wheel Scanner Pro",
    page_icon="⚡",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Style CSS pour le rendu mobile et les badges de tendance
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
    .trend-bullish {
        color: #22c55e;
        font-weight: bold;
    }
    .trend-bearish {
        color: #ef4444;
        font-weight: bold;
    }
    </style>
""", unsafe_allow_html=True)

st.title("⚡ Wheel Scanner IBKR Pro")

# --- PROFILS DE STRATÉGIE ---
st.subheader("🎯 Profil de Stratégie")
profile = st.radio(
    "Sélectionner un profil :",
    ["🟢 Conservative", "🟡 Balanced", "🔴 Aggressive", "⚙️️ Custom / Perso"],
    horizontal=True
)

# --- REGLAGES PERSONNALISABLES ---
with st.expander("⚙️ Ajuster TOUS les filtres (Customisable)", expanded=True):
    
    st.markdown("### 🌍 1. Marchés & Capitalisation (Market Cap)")
    markets = st.multiselect(
        "Marchés :",
        ["🇺🇸 NASDAQ", "🇺🇸 NYSE", "🇨🇦 TSX", "🇪🇺 EU", "🇸🇬 SG"],
        default=["🇺🇸 NASDAQ", "🇺🇸 NYSE"]
    )
    
    col_p1, col_p2 = st.columns(2)
    min_price = col_p1.number_input("Prix Min Sous-jacent ($)", value=20.0, step=1.0)
    max_price = col_p2.number_input("Prix Max Sous-jacent ($)", value=200.0, step=1.0)
    
    # FILTRES MARKET CAP (en Milliards $)
    col_mc1, col_mc2 = st.columns(2)
    min_market_cap = col_mc1.number_input("Market Cap Min ($B)", value=10.0, step=1.0, help="En Milliards de dollars (ex: 10 = $10B)")
    max_market_cap = col_mc2.number_input("Market Cap Max ($B)", value=3000.0, step=50.0)
    
    min_volume = st.number_input("Volume Action Min", value=1000000, step=100000)

    st.markdown("### 📈 2. Analyse Technique & Tendance de Marché")
    col_e1, col_e2 = st.columns(2)
    ema_fast = col_e1.number_input("EMA Rapide (Période)", value=20, step=1)
    ema_slow = col_e2.number_input("EMA Lente (Période)", value=50, step=1)
    
    cross_days = st.slider("Fenêtre croisement EMA (jours)", 1, 30, 5)
    
    # FILTRE SUR LA TENDANCE DU MARCHÉ
    trend_filter = st.selectbox(
        "Filtrer par Tendance de Marché :",
        ["Tous les marchés", "🟢 Marché Haussier uniquement (Bullish)", "🔴 Marché Baissier uniquement (Bearish)"]
    )
    
    col_r1, col_r2 = st.columns(2)
    min_rsi = col_r1.number_input("RSI Min", value=40.0, step=1.0)
    max_rsi = col_r2.number_input("RSI Max", value=65.0, step=1.0)

    st.markdown("### 📊 3. Fondamentaux")
    col_f1, col_f2 = st.columns(2)
    max_pe = col_f1.number_input("P/E Ratio Max", value=30.0, step=1.0)
    min_roe = col_f2.number_input("ROE Min (%)", value=12.0, step=1.0)
    max_de = st.number_input("Debt/Equity Max", value=1.5, step=0.1)

    st.markdown("### 🎯 4. Options Wheel (PUT Vente)")
    col_d1, col_d2 = st.columns(2)
    min_dte = col_d1.number_input("DTE Min (Jours)", value=7, step=1)
    max_dte = col_d2.number_input("DTE Max (Jours)", value=30, step=1)
    
    col_delta1, col_delta2 = st.columns(2)
    min_delta = col_delta1.number_input("Delta Absolu Min (ex: 0.15)", value=0.15, step=0.01)
    max_delta = col_delta2.number_input("Delta Absolu Max (ex: 0.30)", value=0.30, step=0.01)
    
    col_i1, col_i2 = st.columns(2)
    min_iv_rank = col_i1.number_input("IV Rank Min", value=30.0, step=5.0)
    min_oi = col_i2.number_input("Open Interest Min", value=500, step=100)
    
    max_spread = st.number_input("Spread Bid/Ask Max (%)", value=10.0, step=1.0)


if st.button("🚀 Lancer le Scan Pro", type="primary", use_container_width=True):
    st.toast("Analyse du marché avec filtres Market Cap et Tendance...", icon="🔄")
    
    # Simulation des données incluant le Market Cap ($B) et le Signal de Tendance
    mock_results = [
        {"ticker": "AAPL", "strike": 215, "dte": 14, "delta": -0.24, "premium": 1.45, "score": 94, "market_cap": 3350, "trend": "Bullish", "rsi": 48.5, "iv_rank": 35},
        {"ticker": "MSFT", "strike": 410, "dte": 21, "delta": -0.21, "premium": 2.80, "score": 89, "market_cap": 3100, "trend": "Bullish", "rsi": 52.1, "iv_rank": 32},
        {"ticker": "NVDA", "strike": 115, "dte": 10, "delta": -0.28, "premium": 1.95, "score": 85, "market_cap": 2800, "trend": "Bullish", "rsi": 59.0, "iv_rank": 55},
        {"ticker": "TSLA", "strike": 210, "dte": 14, "delta": -0.29, "premium": 4.10, "score": 81, "market_cap": 750, "trend": "Bearish", "rsi": 38.2, "iv_rank": 62},
        {"ticker": "KO", "strike": 60, "dte": 21, "delta": -0.18, "premium": 0.65, "score": 78, "market_cap": 270, "trend": "Bullish", "rsi": 41.5, "iv_rank": 25},
    ]
    
    df = pd.DataFrame(mock_results)
    
    # Filtrage par tendance selon le choix de l'utilisateur
    if trend_filter == "🟢 Marché Haussier uniquement (Bullish)":
        df = df[df['trend'] == "Bullish"]
    elif trend_filter == "🔴 Marché Baissier uniquement (Bearish)":
        df = df[df['trend'] == "Bearish"]
        
    df = df.sort_values(by='score', ascending=False)
    
    st.subheader(f"🔥 Opportunités filtrées ({len(df)})")
    
    # Affichage des cartes avec voyants de tendance et Market Cap
    for _, item in df.iterrows():
        trend_light = "🟢 Haussier" if item['trend'] == "Bullish" else "🔴 Baissier"
        
        st.markdown(f"""
        <div class="opportunity-card">
            <span class="badge-score">Score: {item['score']}/100</span>
            <h3 style="margin:0; color:#38bdf8;">{item['ticker']} — PUT ${item['strike']}</h3>
            <p style="margin:5px 0 0 0; font-size:14px; color:#cbd5e1;">
                <b>Tendance :</b> {trend_light} &nbsp;|&nbsp; 
                <b>Cap :</b> ${item['market_cap']}B
            </p>
            <p style="margin:3px 0 0 0; font-size:13px; color:#94a3b8;">
                Prime: ${item['premium']} | DTE: {item['dte']}j | Delta: {item['delta']} | IV Rank: {item['iv_rank']}
            </p>
        </div>
        """, unsafe_allow_html=True)
        
    with st.expander("📊 Vue tableau détaillée"):
        st.dataframe(df, use_container_width=True)
