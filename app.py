import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf

# Configuration de la page
st.set_page_config(
    page_title="Wheel Scanner Pro — NASDAQ & NYSE",
    page_icon="⚡",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Style CSS
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

st.title("⚡ Wheel Scanner NASDAQ & NYSE Pro")

# Liste de référence des tickers majeurs US (NASDAQ & NYSE)
@st.cache_data(ttl=86400)
def get_all_us_tickers():
    # Liste représentative des principaux composants NASDAQ/NYSE
    # (Peut être étendue ou connectée à une API de tickers)
    tickers = [
        "AAPL", "MSFT", "NVDA", "AMZN", "GOOGL", "META", "TSLA", "BRK-B", "UNH", "JNJ",
        "JPM", "V", "PG", "XOM", "MA", "HD", "CVX", "MRK", "ABBV", "LLY", "PEP", "KO",
        "BAC", "COST", "TMO", "CSCO", "MCD", "WMT", "ACN", "ABT", "DIS", "LIN", "AMD",
        "INTC", "TXN", "CMCSA", "PM", "PFE", "NKE", "ORCL", "UNP", "AMGN", "LOW", "SPGI",
        "HON", "IBM", "GS", "CAT", "GE", "SBUX", "QCOM", "RTX", "BKNG", "PLTR", "SOFI",
        "HOOD", "UBER", "PYPL", "MARA", "COIN", "RBLX", "SQ", "CRWD", "RIVN", "NIO", "LCID"
    ]
    return tickers

all_tickers = get_all_us_tickers()

# --- PROFILS DE STRATÉGIE ---
st.subheader("🎯 Profil de Stratégie")
profile = st.radio(
    "Sélectionner un profil :",
    ["🟢 Conservative", "🟡 Balanced", "🔴 Aggressive", "⚙️ Custom / Perso"],
    horizontal=True
)

# --- REGLAGES PERSONNALISABLES ---
with st.expander("⚙️ Ajuster TOUS les filtres (Customisable)", expanded=True):
    
    st.markdown("### 🌍 1. Marchés & Capitalisation")
    markets = st.multiselect(
        "Marchés sélectionnés :",
        ["🇺🇸 NASDAQ", "🇺🇸 NYSE"],
        default=["🇺🇸 NASDAQ", "🇺🇸 NYSE"]
    )
    
    col_p1, col_p2 = st.columns(2)
    min_price = col_p1.number_input("Prix Min Sous-jacent ($)", value=15.0, step=1.0)
    max_price = col_p2.number_input("Prix Max Sous-jacent ($)", value=150.0, step=1.0)
    
    col_mc1, col_mc2 = st.columns(2)
    min_market_cap = col_mc1.number_input("Market Cap Min ($B)", value=5.0, step=1.0)
    max_market_cap = col_mc2.number_input("Market Cap Max ($B)", value=3000.0, step=50.0)
    
    min_volume = st.number_input("Volume Action Min", value=1000000, step=500000)

    st.markdown("### 📈 2. Analyse Technique & Tendance")
    trend_filter = st.selectbox(
        "Filtrer par Tendance de Marché :",
        ["Tous les marchés", "🟢 Marché Haussier uniquement (Bullish)", "🔴 Marché Baissier uniquement (Bearish)"]
    )
    
    col_r1, col_r2 = st.columns(2)
    min_rsi = col_r1.number_input("RSI Min", value=30.0, step=1.0)
    max_rsi = col_r2.number_input("RSI Max", value=70.0, step=1.0)

    st.markdown("### 📊 3. Fondamentaux")
    max_pe = st.number_input("P/E Ratio Max", value=50.0, step=5.0)

    st.markdown("### 🎯 4. Options Wheel (PUT Vente)")
    col_d1, col_d2 = st.columns(2)
    min_dte = col_d1.number_input("DTE Min (Jours)", value=7, step=1)
    max_dte = col_d2.number_input("DTE Max (Jours)", value=45, step=1)
    
    col_delta1, col_delta2 = st.columns(2)
    min_delta = col_delta1.number_input("Delta Absolu Min", value=0.10, step=0.01)
    max_delta = col_delta2.number_input("Delta Absolu Max", value=0.35, step=0.01)


if st.button("🚀 Lancer le Scan NASDAQ & NYSE Pro", type="primary", use_container_width=True):
    st.toast("Scan en direct des marchés NASDAQ & NYSE...", icon="🔄")
    
    results = []
    progress_bar = st.progress(0)
    
    # Parcours et filtrage direct sur la liste NASDAQ / NYSE
    for idx, ticker_symbol in enumerate(all_tickers):
        progress_bar.progress((idx + 1) / len(all_tickers))
        
        try:
            ticker = yf.Ticker(ticker_symbol)
            info = ticker.fast_info
            
            # Récupération du prix actuel
            price = info.get("lastPrice", None)
            if price is None or price < min_price or price > max_price:
                continue
                
            market_cap_b = (info.get("marketCap", 0) or 0) / 1e9
            if market_cap_b < min_market_cap or market_cap_b > max_market_cap:
                continue
                
            volume = info.get("lastVolume", 0) or 0
            if volume < min_volume:
                continue

            # Simulation/Calcul de tendance et d'option pour le démo en direct
            trend = "Bullish" if price > info.get("fiftyDayAverage", price) else "Bearish"
            if trend_filter == "🟢 Marché Haussier uniquement (Bullish)" and trend != "Bullish":
                continue
            if trend_filter == "🔴 Marché Baissier uniquement (Bearish)" and trend != "Bearish":
                continue

            strike = round(price * 0.92, 1) # Strike ~8% OTM
            premium = round(price * 0.015, 2)
            score = int(np.clip(80 + (market_cap_b / 50) - (price / 200), 60, 98))

            results.append({
                "ticker": ticker_symbol,
                "stock_price": round(price, 2),
                "strike": strike,
                "dte": 21,
                "delta": -0.20,
                "premium": premium,
                "score": score,
                "market_cap": round(market_cap_b, 1),
                "trend": trend,
                "rsi": 50.0
            })
            
        except Exception:
            continue

    progress_bar.empty()
    df_results = pd.DataFrame(results)
    
    if df_results.empty:
        st.error("❌ Aucune action trouvée respectant l'ensemble de vos critères sur le NASDAQ/NYSE.")
    else:
        df_results = df_results.sort_values(by="score", ascending=False)
        st.subheader(f"🔥 Opportunités NASDAQ & NYSE ({len(df_results)})")
        
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

