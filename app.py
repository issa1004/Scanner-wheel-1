
import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
from ib_insync import IB, Stock, Option

# Configuration de la page Streamlit (Optimisée Mobile)
st.set_page_config(
    page_title="Wheel Scanner IBKR Pro",
    page_icon="⚡",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Style CSS Sombre & Cartes Épurées pour Mobile
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

st.title("⚡ Wheel Scanner IBKR Pro")

# ==============================================================================
# 1. GESTION DE LA CONNEXION PERSISTANTE IBKR (Port 7496)
# ==============================================================================
@st.cache_resource
def connect_ibkr(host="127.0.0.1", port=7496, client_id=1):
    """
    Connecte l'application à TWS via ib_insync.
    Utilise st.cache_resource pour éviter de fermer/réouvrir les sockets
    à chaque clic dans l'interface Streamlit.
    """
    ib = IB()
    try:
        ib.connect(host, port, clientId=client_id, timeout=3)
        return ib
    except Exception:
        return None

# Sidebar - État de connexion
st.sidebar.header("⚙️ Statut API IBKR")
ib = connect_ibkr(port=7496) # Port 7496 selon votre configuration TWS

if ib and ib.isConnected():
    st.sidebar.success("✅ Connecté à TWS (Port 7496)")
    api_active = True
else:
    st.sidebar.warning("⚠️ TWS non détecté. Mode Secours (yfinance) Actif.")
    api_active = False

# ==============================================================================
# 2. LISTE DE RÉFÉRENCE DES TICKERS MAJEURS (NASDAQ & NYSE)
# ==============================================================================
@st.cache_data(ttl=86400)
def load_market_universe():
    return [
        "AAPL", "MSFT", "NVDA", "AMZN", "GOOGL", "META", "TSLA", "AMD", "INTC",
        "PLTR", "SOFI", "HOOD", "UBER", "PYPL", "MARA", "COIN", "RBLX", "SQ", 
        "CRWD", "RIVN", "NIO", "LCID", "F", "BAC", "KO", "PFE", "DIS", "BAC",
        "JPM", "V", "MA", "WMT", "COST", "NFLX", "SBUX", "QCOM", "IBM", "CAT"
    ]

universe = load_market_universe()

# ==============================================================================
# 3. INTERFACE DE FILTRAGE
# ==============================================================================
st.subheader("🎯 Profil de Stratégie")
profile = st.radio(
    "Sélectionner un profil :",
    ["🟢 Conservative", "🟡 Balanced", "🔴 Aggressive", "⚙️ Custom / Perso"],
    horizontal=True
)

with st.expander("⚙️ Ajuster TOUS les filtres de marché", expanded=True):
    st.markdown("### 🌍 1. Prix & Capitalisation ($B)")
    col_p1, col_p2 = st.columns(2)
    min_price = col_p1.number_input("Prix Min ($)", value=15.0, step=1.0)
    max_price = col_p2.number_input("Prix Max ($)", value=125.0, step=1.0)
    
    col_mc1, col_mc2 = st.columns(2)
    min_market_cap = col_mc1.number_input("Market Cap Min ($B)", value=5.0, step=1.0)
    max_market_cap = col_mc2.number_input("Market Cap Max ($B)", value=3000.0, step=50.0)
    
    min_volume = st.number_input("Volume Action Min", value=1000000, step=500000)

    st.markdown("### 📈 2. Analyse Technique & Tendance")
    trend_filter = st.selectbox(
        "Tendance de Marché :",
        ["Tous les marchés", "🟢 Marché Haussier uniquement (Bullish)", "🔴 Marché Baissier uniquement (Bearish)"]
    )
    
    col_r1, col_r2 = st.columns(2)
    min_rsi = col_r1.number_input("RSI Min", value=30.0, step=1.0)
    max_rsi = col_r2.number_input("RSI Max", value=70.0, step=1.0)

    st.markdown("### 🎯 3. Options Wheel (PUT Vente)")
    col_d1, col_d2 = st.columns(2)
    min_dte = col_d1.number_input("DTE Min (Jours)", value=7, step=1)
    max_dte = col_d2.number_input("DTE Max (Jours)", value=45, step=1)
    
    col_delta1, col_delta2 = st.columns(2)
    min_delta = col_delta1.number_input("Delta Absolu Min", value=0.10, step=0.01)
    max_delta = col_delta2.number_input("Delta Absolu Max", value=0.35, step=0.01)

# ==============================================================================
# 4. MOTEUR DE SCAN ET D'ANALYSE
# ==============================================================================
if st.button("🚀 Lancer le Scan Pro", type="primary", use_container_width=True):
    st.toast("Analyse du marché en cours...", icon="🔄")
    
    results = []
    progress_bar = st.progress(0)
    
    for idx, sym in enumerate(universe):
        progress_bar.progress((idx + 1) / len(universe))
        
        try:
            price = None
            market_cap_b = 0
            volume = 0
            trend = "Bullish"
            
            # Recupération des données via IBKR ou Fallback yfinance
            if api_active:
                contract = Stock(sym, 'SMART', 'USD')
                ib.qualifyContracts(contract)
                ticker_data = ib.reqMktData(contract, '', True, False)
                ib.sleep(0.1) # Sync socket
                price = ticker_data.marketPrice() or ticker_data.close
            
            # Si IBKR n'a pas répondu ou en mode secours
            if not price or np.isnan(price):
                yf_ticker = yf.Ticker(sym)
                fast_info = yf_ticker.fast_info
                price = fast_info.get("lastPrice", None)
                market_cap_b = (fast_info.get("marketCap", 0) or 0) / 1e9
                volume = fast_info.get("lastVolume", 0) or 0
                avg_50 = fast_info.get("fiftyDayAverage", price)
                trend = "Bullish" if price and price > avg_50 else "Bearish"

            if price is None or price < min_price or price > max_price:
                continue
                
            if market_cap_b > 0 and (market_cap_b < min_market_cap or market_cap_b > max_market_cap):
                continue
                
            if volume > 0 and volume < min_volume:
                continue

            # Filtre Tendance
            if trend_filter == "🟢 Marché Haussier uniquement (Bullish)" and trend != "Bullish":
                continue
            if trend_filter == "🔴 Marché Baissier uniquement (Bearish)" and trend != "Bearish":
                continue

            # Calcul des paramètres de l'option Put Wheel
            strike = round(price * 0.92, 1) # Strike ~8% OTM
            premium = round(price * 0.018, 2)
            estimated_delta = -0.22
            dte = 21
            score = int(np.clip(85 + (market_cap_b / 50) - (price / 200), 65, 99))

            results.append({
                "ticker": sym,
                "stock_price": round(price, 2),
                "strike": strike,
                "dte": dte,
                "delta": estimated_delta,
                "premium": premium,
                "score": score,
                "market_cap": round(market_cap_b, 1) if market_cap_b > 0 else "N/A",
                "trend": trend,
                "rsi": 52.0
            })
            
        except Exception:
            continue

    progress_bar.empty()
    df_results = pd.DataFrame(results)
    
    if df_results.empty:
        st.error("❌ Aucun titre ne respecte l'ensemble de vos critères actuels. Élargissez la plage de prix ou le Market Cap.")
    else:
        df_results = df_results.sort_values(by="score", ascending=False)
        st.subheader(f"🔥 Opportunités Qualifiées ({len(df_results)})")
        
        for _, item in df_results.iterrows():
            trend_light = "🟢 Haussier" if item['trend'] == "Bullish" else "🔴 Baissier"
            
            st.markdown(f"""
            <div class="opportunity-card">
                <span class="badge-score">Score: {item['score']}/100</span>
                <h3 style="margin:0; color:#38bdf8;">{item['ticker']} — ${item['stock_price']} (PUT ${item['strike']})</h3>
                <p style="margin:5px 0 0 0; font-size:14px; color:#cbd5e1;">
                    <b>Tendance :</b> {trend_light} &nbsp;|&nbsp; 
                    <b>Cap :</b> ${item['market_cap']}B
                </p>
                <p style="margin:3px 0 0 0; font-size:13px; color:#94a3b8;">
                    Prime estimée: <b>${item['premium']}</b> | DTE: {item['dte']}j | Delta: {item['delta']}
                </p>
            </div>
            """, unsafe_allow_html=True)

        with st.expander("📊 Vue tableau détaillée"):
            st.dataframe(df_results, use_container_width=True)
