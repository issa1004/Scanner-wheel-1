import streamlit as st
import pandas as pd
import nest_asyncio
import requests
from ib_insync import IB, Stock, util

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
# 2. SÉLECTION DU MARCHÉ
# ==============================================================================
st.sidebar.header("🌐 1. Sélection du Marché")

market_choice = st.sidebar.selectbox(
    "Marché à scanner :",
    [
        "NASDAQ 100 / S&P 500 (USA)",
        "NYSE (USA)",
        "TSX (Canada)",
        "Europe (Euronext / DAX / LSE)",
        "Singapour (SGX)",
        "Irlande (ISE)",
        "✏️ Liste Personnalisée de Tickers"
    ]
)

@st.cache_data(ttl=3600)
def load_full_index_universe(market):
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
        return ["RY", "TD", "SHOP", "ENB", "CNR", "BNS", "BMO", "TRP", "BAM", "SU"]

    elif market == "Europe (Euronext / DAX / LSE)":
        return ["MC", "OR", "TTE", "ASML", "SAP", "SIE", "SHEL", "AZN", "AIR", "RMS"]

    elif market == "Singapour (SGX)":
        return ["D05", "O39", "U11", "Z74", "C38N", "A17U", "C6L", "C31", "S68", "BN4"]

    elif market == "Irlande (ISE)":
        return ["CRG", "RY4C", "BIR", "A3M", "KSP", "EIR", "KRZ", "GL9", "GVR", "IL0A"]

    return []

if market_choice == "✏️ Liste Personnalisée de Tickers":
    custom_input = st.sidebar.text_area(
        "Entrez vos tickers (séparés par des virgules) :",
        value="AAPL, TSLA, NVDA, AMD, BABA, SPY, QQQ, PLTR, SOFI, MARA, COIN, WMT, INTC, BAC, CVX",
        height=100
    )
    full_universe = [t.strip().upper() for t in custom_input.replace("\n", ",").split(",") if t.strip()]
else:
    full_universe = load_full_index_universe(market_choice)

max_scan_count = st.sidebar.slider("Nombre d'actions à analyser :", min_value=10, max_value=len(full_universe), value=min(100, len(full_universe)))
universe = full_universe[:max_scan_count]

st.sidebar.info(f"📊 **{len(universe)}** action(s) sélectionnée(s) sur **{len(full_universe)}** disponibles.")

# ==============================================================================
# 3. CRITÈRES TECHNIQUES ET FONDAMENTAUX MODIFIABLES
# ==============================================================================
st.sidebar.header("🎯 2. Filtres Techniques")

col_p1, col_p2 = st.sidebar.columns(2)
min_price = col_p1.number_input("Prix Min ($)", value=2.0, step=1.0)
max_price = col_p2.number_input("Prix Max ($)", value=500.0, step=10.0)

trend_filter = st.sidebar.selectbox("Filtre de Tendance :", ["🟢 Haussier (EMA Rapide > Lente)", "🔴 Baissier (EMA Rapide < Lente)", "⚪ Toutes les Tendances"])

col_e1, col_e2 = st.sidebar.columns(2)
fast_ema = col_e1.number_input("EMA Rapide", value=20, step=1)
slow_ema = col_e2.number_input("EMA Lente", value=50, step=1)

crossover_days = st.sidebar.slider("Fenêtre max du Croisement EMA (Jours) :", min_value=1, max_value=30, value=10)

min_volume = st.sidebar.number_input("Volume Moyen Min (Actions/jour)", value=500000, step=100000)

st.sidebar.header("📊 3. Filtres Fondamentaux")

min_mcap = st.sidebar.number_input("Market Cap Min (Millions $)", value=1000.0, step=500.0, help="Exemple : 1000 M$= 1 Milliard$")
max_pe = st.sidebar.number_input("P/E Max", value=40.0, step=1.0)
min_roe = st.sidebar.number_input("ROE Min (%)", value=5.0, step=1.0)
max_debt_equity = st.sidebar.number_input("Debt / Equity Max", value=2.5, step=0.1)

st.sidebar.header("⚙️ 4. Paramètres Options")

col_d1, col_d2 = st.sidebar.columns(2)
min_dte = col_d1.number_input("DTE Min (Jours)", value=14, step=1)
max_dte = col_d2.number_input("DTE Max (Jours)", value=45, step=1)

col_dl1, col_dl2 = st.sidebar.columns(2)
min_delta = col_dl1.number_input("Delta Min", value=0.15, step=0.05)
max_delta = col_dl2.number_input("Delta Max", value=0.35, step=0.05)

# ==============================================================================
# 4. FONCTION PARSING ET REQUÊTES IBKR
# ==============================================================================
def parse_fundamental_ratios(ratio_str):
    """ Extrait les ratios P/E, ROE, Debt/Equity et Market Cap depuis le flux IBKR """
    ratios = {'PE': None, 'ROE': None, 'DE': None, 'MCAP': None}
    if not ratio_str:
        return ratios
    
    try:
        items = ratio_str.split(';')
        for item in items:
            if '=' in item:
                k, v = item.split('=')
                try:
                    val = float(v)
                    if k in ['NPEPRCL', 'PEEXCLXCL', 'APEXCLXCL']:
                        ratios['PE'] = val
                    elif k in ['AEROP', 'TTMROEPCT', 'GROEM']:
                        ratios['ROE'] = val
                    elif k in ['MASCAP', 'TOTALD2EQ', 'TTMRECTOT']:
                        ratios['DE'] = val
                    elif k in ['MKTCAP', 'CGMKTCAP', 'MCAP']:
                        ratios['MCAP'] = val
                except ValueError:
                    continue
    except Exception:
        pass
    return ratios

def format_mcap(mcap_val):
    """ Formate la capitalisation boursière pour un affichage lisible """
    if mcap_val is None:
        return "N/A"
    if mcap_val >= 1000:
        return f"${mcap_val / 1000:.2f} B"
    return f"${mcap_val:.1f} M"

def connect_ibkr(host, port, client_id):
    ib = IB()
    try:
        ib.connect(host, port, clientId=client_id, timeout=6)
        ib.reqMarketDataType(3)  # Données différées
        return ib
    except Exception as e:
        st.error(f"❌ Erreur de connexion à TWS : `{e}`")
        return None

def analyze_ticker_ibkr(ib, symbol, market, f_ema, s_ema, max_cross_days):
    try:
        sym = symbol.strip().upper()
        if market == "TSX (Canada)":
            contract = Stock(sym.replace(".TO", ""), 'TSE', 'CAD')
        elif market == "Singapour (SGX)":
            contract = Stock(sym, 'SGX', 'SGD')
        elif market in ["Europe (Euronext / DAX / LSE)", "Irlande (ISE)"]:
            contract = Stock(sym, 'SMART', 'EUR')
        else:
            contract = Stock(sym, 'SMART', 'USD')

        ib.qualifyContracts(contract)

        # 1. Données Historiques de Prix
        bars = ib.reqHistoricalData(
            contract, endDateTime='', durationStr='100 D',
            barSizeSetting='1 day', whatToShow='TRADES', useRTH=True
        )

        if not bars or len(bars) < max(f_ema, s_ema) + max_cross_days:
            return None

        df = util.df(bars)
        price = float(df['close'].iloc[-1])
        avg_volume = float(df['volume'].tail(20).mean())

        # 2. Calcul des EMA et détection du croisement dans la fenêtre de jours
        df['ema_fast'] = df['close'].ewm(span=f_ema, adjust=False).mean()
        df['ema_slow'] = df['close'].ewm(span=s_ema, adjust=False).mean()
        df['bullish'] = df['ema_fast'] > df['ema_slow']

        is_currently_bullish = bool(df['bullish'].iloc[-1])

        # Détection du croisement dans les N derniers jours
        recent_bars = df.tail(max_cross_days + 1)
        cross_occurred = False
        for i in range(1, len(recent_bars)):
            prev_state = recent_bars['bullish'].iloc[i-1]
            curr_state = recent_bars['bullish'].iloc[i]
            if prev_state != curr_state:
                cross_occurred = True
                break

        # 3. Récupération des Ratios Fondamentaux via TWS Tick 258
        mkt_data = ib.reqMktData(contract, '258', False, False)
        ib.sleep(0.2)
        ratios = parse_fundamental_ratios(mkt_data.fundamentalRatios)

        return {
            "price": price,
            "volume": avg_volume,
            "is_bullish": is_currently_bullish,
            "cross_occurred": cross_occurred,
            "pe": ratios['PE'],
            "roe": ratios['ROE'],
            "debt_equity": ratios['DE'],
            "mcap": ratios['MCAP']
        }
    except Exception:
        return None

# ==============================================================================
# 5. EXÉCUTION ET AFFICHAGE
# ==============================================================================
st.subheader(f"🔍 Scan du Marché : {market_choice}")

if st.button("🚀 Lancer le Scan Pro via IBKR Data", type="primary", use_container_width=True):
    ib = connect_ibkr(ib_host, int(ib_port), int(ib_client_id))

    if ib and ib.isConnected():
        st.success("✅ Connecté à Interactive Brokers TWS !")

        status_box = st.empty()
        progress_bar = st.progress(0)
        results = []
        total = len(universe)

        for idx, sym in enumerate(universe):
            status_box.info(f"⏳ Analyse IBKR ({idx+1}/{total}) : **{sym}**...")
            progress_bar.progress((idx + 1) / total)

            data = analyze_ticker_ibkr(ib, sym, market_choice, fast_ema, slow_ema, crossover_days)
            if not data:
                continue

            price = data["price"]

            # --- FILTRES TECHNIQUES & VOLUME ---
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

            # --- FILTRES FONDAMENTAUX ---
            if data["mcap"] is not None and data["mcap"] < min_mcap:
                continue
            if data["pe"] is not None and data["pe"] > max_pe:
                continue
            if data["roe"] is not None and data["roe"] < min_roe:
                continue
            if data["debt_equity"] is not None and data["debt_equity"] > max_debt_equity:
                continue

            # --- CALCUL OPTIONS ---
            target_delta = (min_delta + max_delta) / 2.0
            dte = int((min_dte + max_dte) / 2)
            strike = round(price * (1.0 - target_delta * 0.35), 1)
            estimated_premium = round(price * target_delta * 0.08, 2)

            score = 80
            if data["is_bullish"]: score += 10
            if data["volume"] > 1000000: score += 5
            score = min(score, 99)

            results.append({
                "ticker": sym,
                "price": round(price, 2),
                "volume": int(data["volume"]),
                "mcap": format_mcap(data['mcap']),
                "pe": f"{data['pe']:.1f}" if data["pe"] else "N/A",
                "roe": f"{data['roe']:.1f}%" if data["roe"] else "N/A",
                "de": f"{data['debt_equity']:.2f}" if data["debt_equity"] else "N/A",
                "strike": strike,
                "dte": dte,
                "delta": round(-target_delta, 2),
                "premium": estimated_premium,
                "score": score,
                "signal_str": "Haussier" if data["is_bullish"] else "Baissier",
                "signal_icon": "🟢" if data["is_bullish"] else "🔴"
            })

        ib.disconnect()
        status_box.empty()
        progress_bar.empty()

        if not results:
            st.warning("⚠️️ Aucun titre ne correspond à l'ensemble de vos critères techniques et fondamentaux.")
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
                        <b>Tendance:</b> {item['signal_icon']} {item['signal_str']} | <b>Vol Moyen:</b> {item['volume']:,}
                    </div>
                    <div style="margin-top: 4px; font-size: 13px; color: #cbd5e1;">
                        <b>Market Cap:</b> {item['mcap']} | <b>P/E:</b> {item['pe']} | <b>ROE:</b> {item['roe']} | <b>Debt/Equity:</b> {item['de']}
                    </div>
                    <div style="margin-top: 6px; font-size: 13px; color: #38bdf8;">
                        Prime estimée: <b style="color: #22c55e;">${item['premium']}</b> | DTE: <b>{item['dte']}j</b> | Delta: <b>{item['delta']}</b>
                    </div>
                </div>
                """, unsafe_allow_html=True)
