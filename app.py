import streamlit as st
import pandas as pd
import yfinance as yf
import requests
import datetime

st.set_page_config(
    page_title="Global Wheel Strategy Scanner",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("📈 Global Market Wheel Strategy Scanner")

# ==============================================================================
# 1. SÉLECTION DU MARCHÉ
# ==============================================================================
st.sidebar.header("🌐 1. Sélection du Marché")

market_choice = st.sidebar.selectbox(
    "Marché à scanner :",
    [
        "NASDAQ 100 / S&P 500 (USA)",
        "NYSE (USA)",
        "TSX (Canada)",
        "Europe (Euronext / DAX)",
        "✏️ Liste Personnalisée de Tickers"
    ]
)

@st.cache_data(ttl=3600)
def load_universe(market):
    if market == "NASDAQ 100 / S&P 500 (USA)":
        try:
            headers = {'User-Agent': 'Mozilla/5.0'}
            r = requests.get("https://en.wikipedia.org/wiki/List_of_S%26P_500_companies", headers=headers, timeout=5)
            df = pd.read_html(r.text)[0]
            return [s.replace('.', '-') for s in df['Symbol'].tolist()]
        except Exception:
            return ["AAPL", "MSFT", "NVDA", "AMZN", "GOOGL", "META", "TSLA", "AVGO", "AMD", "NFLX",
                    "COST", "TMUS", "CSCO", "AMAT", "PEP", "INTU", "QCOM", "TXN", "AMGN", "HON"]

    elif market == "NYSE (USA)":
        return ["BRK-B", "JPM", "WMT", "UNH", "V", "XOM", "MA", "PG", "JNJ", "HD",
                "ORCL", "ABBV", "BAC", "CVX", "MRK", "TMO", "LIN", "WFC", "ACN", "MCD"]

    elif market == "TSX (Canada)":
        tickers = ["RY", "TD", "SHOP", "ENB", "CNR", "BNS", "BMO", "TRP", "BAM", "SU"]
        return [f"{t}.TO" for t in tickers]

    elif market == "Europe (Euronext / DAX)":
        return ["MC.PA", "OR.PA", "TTE.PA", "ASML.AS", "SAP.DE", "SIE.DE", "AIR.PA", "RMS.PA"]

    return []

if market_choice == "✏️ Liste Personnalisée de Tickers":
    custom_input = st.sidebar.text_area(
        "Entrez vos tickers (ex: AAPL, TSLA, SHOP.TO) :",
        value="AAPL, TSLA, NVDA, AMD, BABA, SPY, QQQ, PLTR, SOFI, MARA, COIN, WMT, INTC, BAC, CVX",
        height=100
    )
    full_universe = [t.strip().upper() for t in custom_input.replace("\n", ",").split(",") if t.strip()]
else:
    full_universe = load_universe(market_choice)

max_scan_count = st.sidebar.slider("Nombre d'actions à analyser :", min_value=5, max_value=len(full_universe), value=min(50, len(full_universe)))
universe = full_universe[:max_scan_count]

st.sidebar.info(f"📊 **{len(universe)}** action(s) sélectionnée(s).")

# ==============================================================================
# 2. FILTRES TECHNIQUES ET FONDAMENTAUX
# ==============================================================================
st.sidebar.header("🎯 2. Filtres Techniques")

col_p1, col_p2 = st.sidebar.columns(2)
min_price = col_p1.number_input("Prix Min ($)", value=2.0, step=1.0)
max_price = col_p2.number_input("Prix Max ($)", value=500.0, step=10.0)

trend_filter = st.sidebar.selectbox("Tendance :", ["🟢 Haussier (EMA Rapide > Lente)", "🔴 Baissier (EMA Rapide < Lente)", "⚪ Toutes les Tendances"])

col_e1, col_e2 = st.sidebar.columns(2)
fast_ema = col_e1.number_input("EMA Rapide", value=20, step=1)
slow_ema = col_e2.number_input("EMA Lente", value=50, step=1)

crossover_days = st.sidebar.slider("Croisement EMA (Jours max) :", min_value=1, max_value=30, value=10)
min_volume = st.sidebar.number_input("Volume Moyen Min (Actions/jour)", value=500000, step=100000)

st.sidebar.header("📊 3. Filtres Fondamentaux")

min_mcap = st.sidebar.number_input("Market Cap Min (M$)", value=1000.0, step=500.0, help="1000 M$ = 1 Milliard $")
max_pe = st.sidebar.number_input("P/E Max", value=50.0, step=1.0)
min_roe = st.sidebar.number_input("ROE Min (%)", value=0.0, step=1.0)
max_debt_equity = st.sidebar.number_input("Debt / Equity Max", value=3.0, step=0.1)

st.sidebar.header("⚙️ 4. Paramètres Options")

col_d1, col_d2 = st.sidebar.columns(2)
min_dte = col_d1.number_input("DTE Min (Jours)", value=14, step=1)
max_dte = col_d2.number_input("DTE Max (Jours)", value=45, step=1)

col_dl1, col_dl2 = st.sidebar.columns(2)
min_delta = col_dl1.number_input("Delta Min", value=0.15, step=0.05)
max_delta = col_dl2.number_input("Delta Max", value=0.35, step=0.05)

# ==============================================================================
# 3. MOTEUR D'ANALYSE
# ==============================================================================
def analyze_stock(ticker_symbol):
    try:
        stock = yf.Ticker(ticker_symbol)
        
        # 1. Données Historiques (120 jours pour calcul EMA)
        hist = stock.history(period="120d")
        if hist.empty or len(hist) < max(fast_ema, slow_ema) + crossover_days:
            return None

        latest_price = float(hist['Close'].iloc[-1])
        avg_volume = float(hist['Volume'].tail(20).mean())

        # 2. Calcul des EMA et Croisement
        hist['EMA_Fast'] = hist['Close'].ewm(span=fast_ema, adjust=False).mean()
        hist['EMA_Slow'] = hist['Close'].ewm(span=slow_ema, adjust=False).mean()
        hist['Bullish'] = hist['EMA_Fast'] > hist['EMA_Slow']

        is_bullish = bool(hist['Bullish'].iloc[-1])

        # Vérification du croisement dans les N derniers jours
        recent = hist.tail(crossover_days + 1)
        cross_occurred = False
        for i in range(1, len(recent)):
            if recent['Bullish'].iloc[i-1] != recent['Bullish'].iloc[i]:
                cross_occurred = True
                break

        # 3. Données Fondamentales
        info = stock.info
        mcap_m = (info.get('marketCap', 0) or 0) / 1e6
        pe_ratio = info.get('trailingPE', None) or info.get('forwardPE', None)
        roe_val = (info.get('returnOnEquity', 0) or 0) * 100
        debt_eq = (info.get('debtToEquity', 0) or 0) / 100.0

        return {
            "symbol": ticker_symbol,
            "price": latest_price,
            "volume": avg_volume,
            "is_bullish": is_bullish,
            "cross_occurred": cross_occurred,
            "mcap_m": mcap_m,
            "pe": pe_ratio,
            "roe": roe_val,
            "debt_equity": debt_eq
        }
    except Exception:
        return None

# ==============================================================================
# 4. EXECUTION DU SCAN
# ==============================================================================
st.subheader(f"🔍 Scan du Marché : {market_choice}")

if st.button("🚀 Lancer le Scan Ultra-Rapide", type="primary", use_container_width=True):
    status_box = st.empty()
    progress_bar = st.progress(0)
    results = []
    total = len(universe)

    for idx, sym in enumerate(universe):
        status_box.info(f"⏳ Analyse ({idx+1}/{total}) : **{sym}**...")
        progress_bar.progress((idx + 1) / total)

        data = analyze_stock(sym)
        if not data:
            continue

        price = data["price"]

        # Filtres Techniques
        if price < min_price or price > max_price:
            continue
        if data["volume"] < min_volume:
            continue
        if not data["cross_occurred"]:
            continue
        if trend_filter == "🟢 Haussier (EMA Rapide > Lente)" and not data["is_bullish"]:
            continue
        if trend_filter == "🔴 Baissier (EMA Rapide < Lente)" and data["is_bullish"]:
            continue

        # Filtres Fondamentaux
        if min_mcap > 0 and data["mcap_m"] < min_mcap:
            continue
        if data["pe"] is not None and data["pe"] > max_pe:
            continue
        if data["roe"] < min_roe:
            continue
        if data["debt_equity"] > max_debt_equity:
            continue

        # Calculs Options
        target_delta = (min_delta + max_delta) / 2.0
        dte = int((min_dte + max_dte) / 2)
        strike = round(price * (1.0 - target_delta * 0.35), 2)
        estimated_premium = round(price * target_delta * 0.08, 2)

        mcap_str = f"${data['mcap_m']/1000:.2f} B" if data['mcap_m'] >= 1000 else f"${data['mcap_m']:.1f} M"

        results.append({
            "ticker": sym,
            "price": round(price, 2),
            "volume": int(data["volume"]),
            "mcap": mcap_str,
            "pe": f"{data['pe']:.1f}" if data["pe"] else "N/A",
            "roe": f"{data['roe']:.1f}%",
            "de": f"{data['debt_equity']:.2f}",
            "strike": strike,
            "dte": dte,
            "delta": round(-target_delta, 2),
            "premium": estimated_premium,
            "signal_str": "Haussier" if data["is_bullish"] else "Baissier",
            "signal_icon": "🟢" if data["is_bullish"] else "🔴"
        })

    status_box.empty()
    progress_bar.empty()

    if not results:
        st.warning("⚠️ Aucun titre ne correspond à l'ensemble de vos critères de filtrage.")
    else:
        st.subheader(f"🔥 Opportunités Qualifiées ({len(results)})")

        for item in results:
            st.markdown(f"""
            <div style="background-color: #1a2332; border-radius: 8px; padding: 14px 18px; margin-bottom: 12px; border: 1px solid #2d3748;">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <span style="color: #38bdf8; font-size: 22px; font-weight: bold;">
                        {item['ticker']} — ${item['price']} <span style="color: #93c5fd; font-size: 16px;">(PUT Recommended: ${item['strike']})</span>
                    </span>
                </div>
                <div style="margin-top: 6px; font-size: 14px; color: #e2e8f0;">
                    <b>Tendance:</b> {item['signal_icon']} {item['signal_str']} | <b>Vol Moyen:</b> {item['volume']:,}
                </div>
                <div style="margin-top: 4px; font-size: 13px; color: #cbd5e1;">
                    <b>Market Cap:</b> {item['mcap']} | <b>P/E:</b> {item['pe']} | <b>ROE:</b> {item['roe']} | <b>Debt/Equity:</b> {item['de']}
                </div>
                <div style="margin-top: 6px; font-size: 13px; color: #38bdf8;">
                    Prime estimée: <b style="color: #22c55e;">${item['premium']}</b> | DTE: <b>{item['dte']}j</b> | Delta cible: <b>{item['delta']}</b>
                </div>
            </div>
            """, unsafe_allow_html=True)
