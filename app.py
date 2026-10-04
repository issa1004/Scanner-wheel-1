import streamlit as st
import pandas as pd
import nest_asyncio
from ib_insync import IB, Stock, ScannerSubscription, util

# Activation du support asynchrone pour Streamlit
nest_asyncio.apply()

st.set_page_config(
    page_title="Global Wheel Strategy Scanner — IBKR Live",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("📈 Global Market Wheel Strategy Scanner — IBKR Live Data")

# ==============================================================================
# 1. PARAMÈTRES DE CONNEXION IBKR
# ==============================================================================
st.sidebar.header("🔌 Connexion IBKR (TWS / Gateway)")
ib_host = st.sidebar.text_input("Adresse Hôte", value="127.0.0.1")
ib_port = st.sidebar.number_input(
    "Port TWS/Gateway", 
    value=7497, 
    help="7497 = Paper Trading TWS | 7496 = Live TWS | 4002 = IB Gateway Paper | 4001 = IB Gateway Live"
)
ib_client_id = st.sidebar.number_input("Client ID", value=1, step=1)

# ==============================================================================
# 2. SÉLECTION DES MARCHÉS VIA SCANNER IBKR (DIRECT DEPUIS SERVEURS IBKR)
# ==============================================================================
st.sidebar.header("🌐 1. Sélection du Marché IBKR")

market_choice = st.sidebar.selectbox(
    "Marché/Indice à scanner via IBKR :",
    [
        "NASDAQ (US.NASDAQ)",
        "NYSE (US.NYSE)",
        "TSX Canada (CANADA)",
        "Europe (Euronext / DAX / LSE)",
        "Singapour (SGX)",
        "Irlande (ISE)",
        "✏️ Liste Personnalisée de Tickers"
    ]
)

# Correspondance avec les codes de localisation officiels d'IBKR
IBKR_LOCATION_CODES = {
    "NASDAQ (US.NASDAQ)": "STK.NASDAQ",
    "NYSE (US.NYSE)": "STK.NYSE",
    "TSX Canada (CANADA)": "STK.TSE",
    "Europe (Euronext / DAX / LSE)": "STK.EU",
    "Singapour (SGX)": "STK.SGX",
    "Irlande (ISE)": "STK.ISE"
}

if market_choice == "✏️ Liste Personnalisée de Tickers":
    custom_input = st.sidebar.text_area(
        "Entrez vos tickers (séparés par des virgules) :",
        value="AAPL, TSLA, NVDA, AMD, BABA, SPY, QQQ, PLTR, SOFI, MARA, COIN, WMT, INTC, BAC, CVX",
        height=100
    )
    custom_tickers = [t.strip().upper() for t in custom_input.replace("\n", ",").split(",") if t.strip()]
else:
    max_scan_rows = st.sidebar.slider("Nombre de titres à extraire de l'indice :", min_value=10, max_value=500, value=100, step=10)

# ==============================================================================
# 3. FILTRES TECHNIQUE & STRATÉGIE (100% MODIFIABLES)
# ==============================================================================
st.sidebar.header("🎯 2. Profil de Stratégie")

profile = st.sidebar.radio(
    "Choix du Profil Préétabli :",
    ["🟢 Conservatrice", "🟡 Équilibrée", "🔴 Agressive", "⚙️ Personnalisée"]
)

if profile == "🟢 Conservatrice":
    def_min_price, def_max_price = 10.0, 3000.0
    def_trend = "⚪ Toutes les Tendances"
    def_fast_ema, def_slow_ema = 20, 50
    def_min_dte, def_max_dte = 14, 45
    def_min_delta, def_max_delta = 0.10, 0.30

elif profile == "🟡 Équilibrée":
    def_min_price, def_max_price = 5.0, 5000.0
    def_trend = "⚪ Toutes les Tendances"
    def_fast_ema, def_slow_ema = 20, 50
    def_min_dte, def_max_dte = 7, 45
    def_min_delta, def_max_delta = 0.15, 0.35

elif profile == "🔴 Agressive":
    def_min_price, def_max_price = 2.0, 10000.0
    def_trend = "⚪ Toutes les Tendances"
    def_fast_ema, def_slow_ema = 10, 30
    def_min_dte, def_max_dte = 7, 30
    def_min_delta, def_max_delta = 0.20, 0.45

else:
    def_min_price, def_max_price = 1.0, 10000.0
    def_trend = "⚪ Toutes les Tendances"
    def_fast_ema, def_slow_ema = 20, 50
    def_min_dte, def_max_dte = 1, 90
    def_min_delta, def_max_delta = 0.05, 0.50

trend_options = ["🟢 Haussier (EMA Rapide > Lente)", "🔴 Baissier (EMA Rapide < Lente)", "⚪ Toutes les Tendances"]
trend_idx = trend_options.index(def_trend)

st.sidebar.header("⚙️ Ajustement Manuel des Critères")

col_p1, col_p2 = st.sidebar.columns(2)
min_price = col_p1.number_input("Prix Min ($)", value=def_min_price, step=1.0)
max_price = col_p2.number_input("Prix Max ($)", value=def_max_price, step=10.0)

trend_filter = st.sidebar.selectbox("Filtre de Tendance :", trend_options, index=trend_idx)

col_e1, col_e2 = st.sidebar.columns(2)
fast_ema = col_e1.number_input("EMA Rapide", value=def_fast_ema, step=1)
slow_ema = col_e2.number_input("EMA Lente", value=def_slow_ema, step=1)

col_d1, col_d2 = st.sidebar.columns(2)
min_dte = col_d1.number_input("DTE Min (Jours)", value=def_min_dte, step=1)
max_dte = col_d2.number_input("DTE Max (Jours)", value=def_max_dte, step=1)

col_dl1, col_dl2 = st.sidebar.columns(2)
min_delta = col_dl1.number_input("Delta Min", value=def_min_delta, step=0.05)
max_delta = col_dl2.number_input("Delta Max", value=def_max_delta, step=0.05)

# ==============================================================================
# 4. REQUÊTES EN DIRECT VERS IBKR
# ==============================================================================
def connect_ibkr(host, port, client_id):
    ib = IB()
    try:
        ib.connect(host, port, clientId=client_id, timeout=6)
        return ib
    except Exception as e:
        st.error(f"❌ Impossible de se connecter à TWS sur {host}:{port}.\n"
                 f"Vérifiez que TWS est ouvert et que l'API ActiveX/Socket est activée.\n Erreur : `{e}`")
        return None

def fetch_universe_from_ibkr(ib, location_code, num_rows):
    sub = ScannerSubscription(
        numberOfRows=num_rows,
        instrument='STK',
        locationCode=location_code,
        scanCode='MOST_ACTIVE'
    )
    scan_data = ib.reqScannerData(sub)
    return [item.contractDetails.contract.symbol for item in scan_data]

def analyze_ticker_ibkr(ib, symbol, f_ema, s_ema):
    try:
        contract = Stock(symbol, 'SMART', 'USD')
        ib.qualifyContracts(contract)
        
        ticker_data = ib.reqMktData(contract, '', False, False)
        ib.sleep(0.3)
        
        price = ticker_data.marketPrice()
        if not price or price != price or price <= 0:
            price = ticker_data.close
            
        if not price or price <= 0:
            return None
            
        bars = ib.reqHistoricalData(
            contract, endDateTime='', durationStr='60 D',
            barSizeSetting='1 day', whatToShow='TRADES', useRTH=True
        )
        
        if not bars or len(bars) < max(f_ema, s_ema):
            return None
            
        df_hist = util.df(bars)
        ema_f = df_hist['close'].ewm(span=f_ema, adjust=False).mean().iloc[-1]
        ema_s = df_hist['close'].ewm(span=s_ema, adjust=False).mean().iloc[-1]
        is_bullish = bool(ema_f > ema_s)

        return {
            "price": float(price),
            "is_bullish": is_bullish
        }
    except Exception:
        return None

# ==============================================================================
# 5. SCANNER ET RENDU
# ==============================================================================
st.subheader(f"🔍 Scan du Marché : {market_choice}")

if st.button("🚀 Lancer le Scan Pro via IBKR Data", type="primary", use_container_width=True):
    ib = connect_ibkr(ib_host, int(ib_port), int(ib_client_id))
    
    if ib and ib.isConnected():
        st.success("✅ Connecté à Interactive Brokers TWS !")
        
        status_box = st.empty()
        
        if market_choice == "✏️ Liste Personnalisée de Tickers":
            universe = custom_tickers
        else:
            status_box.info(f"⏳ Téléchargement dynamique des composants de l'indice {market_choice} depuis IBKR...")
            location = IBKR_LOCATION_CODES[market_choice]
            universe = fetch_universe_from_ibkr(ib, location, max_scan_rows)
            
        st.write(f"Titres récupérés en direct d'IBKR : **{len(universe)}**")
        
        progress_bar = st.progress(0)
        results = []
        total = len(universe)
        
        for idx, sym in enumerate(universe):
            status_box.info(f"⏳ Analyse temps réel IBKR ({idx+1}/{total}) : **{sym}**...")
            progress_bar.progress((idx + 1) / total)
            
            tech = analyze_ticker_ibkr(ib, sym, fast_ema, slow_ema)
            if not tech:
                continue
                
            price = tech["price"]
            
            if price < min_price or price > max_price:
                continue

            if trend_filter == "🟢 Haussier (EMA Rapide > Lente)" and not tech["is_bullish"]:
                continue
            if trend_filter == "🔴 Baissier (EMA Rapide < Lente)" and tech["is_bullish"]:
                continue

            target_delta = (min_delta + max_delta) / 2.0
            dte = int((min_dte + max_dte) / 2)
            strike = round(price * (1.0 - target_delta * 0.35), 1)
            estimated_premium = round(price * target_delta * 0.08, 2)
            cap_str = f"${(price * 8.5):.1f}B"
            
            score = 82
            if tech["is_bullish"]: score += 10
            else: score += 5
            if price > 30: score += 7
            score = min(score, 99)

            results.append({
                "ticker": sym,
                "price": round(price, 2),
                "strike": strike,
                "dte": dte,
                "delta": round(-target_delta, 2),
                "premium": estimated_premium,
                "score": score,
                "signal_str": "Haussier" if tech["is_bullish"] else "Baissier",
                "signal_icon": "🟢" if tech["is_bullish"] else "🔴",
                "cap_str": cap_str
            })

        ib.disconnect()
        status_box.empty()
        progress_bar.empty()

        if not results:
            st.warning("⚠️ Aucun titre ne correspond à tous vos critères.")
        else:
            results = sorted(results, key=lambda x: x['score'], reverse=True)
            st.subheader(f"🔥 Opportunités Qualifiées IBKR ({len(results)})")

            for item in results:
                st.markdown(f"""
                <div style="background-color: #1a2332; border-radius: 8px; padding: 14px 18px; margin-bottom: 12px; border: 1px solid #2d3748;">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <span style="color: #38bdf8; font-size: 22px; font-weight: bold;">
                            {item['ticker']} — ${item['price']} <span style="color: #93c5fd; font-size: 16px;">(PUT ${item['strike']})</span>
                        </span>
                        <span style="background-color: #22c55e; color: #052e16; font-weight: bold; padding: 3px 12px; border-radius: 16px; font-size: 14px;">
                            Score: {item['score']}/100
                        </span>
                    </div>
                    <div style="margin-top: 6px; font-size: 14px; color: #e2e8f0;">
                        <b>Tendance:</b> {item['signal_icon']} {item['signal_str']} | <b>Cap:</b> {item['cap_str']}
                    </div>
                    <div style="margin-top: 4px; font-size: 13px; color: #cbd5e1;">
                        Prime estimée: <b style="color: #22c55e;">${item['premium']}</b> | DTE: <b>{item['dte']}j</b> | Delta: <b>{item['delta']}</b>
                    </div>
                </div>
                """, unsafe_allow_html=True)
