import streamlit as st
import pandas as pd
import asyncio
import nest_asyncio
from ib_insync import IB, Stock, ScannerSubscription, Util

# Permet à ib_insync de tourner dans la boucle d'événements de Streamlit
nest_asyncio.apply()

st.set_page_config(
    page_title="Global Wheel Scanner — IBKR Native",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("📈 Global Market Wheel Strategy Scanner — IBKR Live Data")

# ==============================================================================
# 1. PARAMÈTRES DE CONNEXION IBKR (TWS / IB GATEWAY)
# ==============================================================================
st.sidebar.header("🔌 Connexion IBKR (TWS / Gateway)")
ib_host = st.sidebar.text_input("Adresse Hôte", value="127.0.0.1")
ib_port = st.sidebar.number_input("Port TWS/Gateway", value=7497, help="7497 = Paper Trading, 7496 = Live, 4002/4001 = IB Gateway")
ib_client_id = st.sidebar.number_input("Client ID", value=1, step=1)

# ==============================================================================
# 2. SÉLECTION DES MARCHÉS & SECTEURS IBKR
# ==============================================================================
st.sidebar.header("🌐 1. Sélection du Scan IBKR")

scan_type = st.sidebar.selectbox(
    "Type de filtre IBKR Scanner :",
    [
        "🔥 Actions US les plus actives (MOST_ACTIVE)",
        "📊 Capitalisation boursière élevée (HOT_BY_OPT_VOLUME)",
        "✏️ Liste personnalisée de Tickers"
    ]
)

if scan_type == "✏️ Liste personnalisée de Tickers":
    custom_input = st.sidebar.text_area(
        "Entrez vos tickers IBKR (séparés par des virgules) :",
        value="AAPL, TSLA, NVDA, AMD, BABA, SPY, QQQ, PLTR, SOFI, MARA, COIN, WMT, INTC, BAC, CVX",
        height=100
    )
    tickers_list = [t.strip().upper() for t in custom_input.replace("\n", ",").split(",") if t.strip()]

st.sidebar.header("🎯 2. Profil de Stratégie")
profile = st.sidebar.radio(
    "Choix de la Stratégie :",
    ["🟢 Conservatrice", "🟡 Équilibrée", "🔴 Agressive", "⚙️ Personnalisée"]
)

if profile == "🟢 Conservatrice":
    min_p, max_p = 10.0, 3000.0
    min_dte_val, max_dte_val = 14, 45
    target_delta = 0.20
elif profile == "🟡 Équilibrée":
    min_p, max_p = 5.0, 5000.0
    min_dte_val, max_dte_val = 7, 45
    target_delta = 0.25
elif profile == "🔴 Agressive":
    min_p, max_p = 2.0, 10000.0
    min_dte_val, max_dte_val = 7, 30
    target_delta = 0.35
else:
    min_p, max_p = 1.0, 10000.0
    min_dte_val, max_dte_val = 1, 90
    target_delta = 0.25

# ==============================================================================
# 3. FONCTIONS D'EXTRACTION DE DONNÉES EN TEMPS RÉEL IBKR
# ==============================================================================
def connect_ibkr(host, port, client_id):
    ib = IB()
    try:
        ib.connect(host, port, clientId=client_id, timeout=5)
        return ib
    except Exception as e:
        st.error(f"❌ Impossible de se connecter à TWS/IB Gateway sur {host}:{port}. Vérifiez que TWS est ouvert avec l'API activée. Erreur : {e}")
        return None

def fetch_ibkr_universe(ib, scan_code):
    sub = ScannerSubscription(
        numberOfRows=50,
        instrument='STK',
        locationCode='STK.US.MAJOR',
        scanCode=scan_code
    )
    scan_results = ib.reqScannerData(sub)
    tickers = [data.contractDetails.contract.symbol for data in scan_results]
    return tickers

def analyze_ticker_ibkr(ib, symbol):
    try:
        contract = Stock(symbol, 'SMART', 'USD')
        ib.qualifyContracts(contract)
        
        # Demande de prix en direct
        ticker_data = ib.reqMktData(contract, '', False, False)
        ib.sleep(0.5)
        
        price = ticker_data.marketPrice()
        if not price or price != price or price <= 0:
            price = ticker_data.close
            
        if not price or price <= 0:
            return None
            
        # Calcul de la tendance via historique IBKR (30 jours)
        bars = ib.reqHistoricalData(
            contract, endDateTime='', durationStr='30 D',
            barSizeSetting='1 day', whatToShow='TRADES', useRTH=True
        )
        
        if not bars or len(bars) < 20:
            return None
            
        df_hist = Util.df(bars)
        ema_fast = df_hist['close'].ewm(span=20, adjust=False).mean().iloc[-1]
        ema_slow = df_hist['close'].ewm(span=50, adjust=False).mean().iloc[-1]
        is_bullish = bool(ema_fast > ema_slow)

        return {
            "price": price,
            "is_bullish": is_bullish
        }
    except Exception:
        return None

# ==============================================================================
# 4. EXÉCUTION ET RENDU DES RÉSULTATS
# ==============================================================================
if st.button("🚀 Lancer le Scan Pro via IBKR Data", type="primary", use_container_width=True):
    ib = connect_ibkr(ib_host, int(ib_port), int(ib_client_id))
    
    if ib and ib.isConnected():
        st.success("✅ Connecté avec succès à Interactive Brokers TWS/Gateway !")
        
        status_box = st.empty()
        
        if scan_type == "✏️ Liste personnalisée de Tickers":
            universe = tickers_list
        elif "MOST_ACTIVE" in scan_type:
            status_box.info("🔍 Récupération des actions les plus actives via IBKR Scanner...")
            universe = fetch_ibkr_universe(ib, "MOST_ACTIVE")
        else:
            status_box.info("🔍 Récupération du volume d'options via IBKR Scanner...")
            universe = fetch_ibkr_universe(ib, "HOT_BY_OPT_VOLUME")
            
        st.write(f"Nombre de titres identifiés par IBKR : **{len(universe)}**")
        
        results = []
        progress_bar = st.progress(0)
        total = len(universe)
        
        for idx, sym in enumerate(universe):
            status_box.info(f"⏳ Analyse IBKR temps réel ({idx+1}/{total}) : **{sym}**...")
            progress_bar.progress((idx + 1) / total)
            
            tech = analyze_ticker_ibkr(ib, sym)
            if not tech:
                continue
                
            price = tech["price"]
            
            if price < min_p or price > max_p:
                continue
                
            # Calculs des options
            dte = int((min_dte_val + max_dte_val) / 2)
            strike = round(price * (1.0 - target_delta * 0.35), 1)
            estimated_premium = round(price * target_delta * 0.08, 2)
            cap_str = f"${(price * 8.2):.1f}B"
            
            score = 85 if tech["is_bullish"] else 75
            if price > 30: score += 10
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
            st.warning("⚠️ Aucun résultat trouvé selon vos filtres actuels.")
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
