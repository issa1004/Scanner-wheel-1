import streamlit as st
import pandas as pd
import yfinance as yf
import math
import time

st.set_page_config(
    page_title="Global Wheel Strategy Scanner - Version Illimitée",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("📈 Global Market Wheel Strategy Scanner (Version Illimitée)")

# ==============================================================================
# UNIVERS COMPLETS INTÉGRÉS EN DUR
# ==============================================================================
SP500_FULL = [
    "MMM","AOS","ABT","ABBV","ACN","ADBE","AMD","AAP","AES","AFL","A","APD","ABNB","AKAM","ALB","ARE","ALGN","ALLE",
    "LNT","ALL","GOOGL","GOOG","MO","AMZN","AMCR","AEE","AAL","AEP","AXP","AIG","AMT","AWK","AMP","AME","AMGN","APH",
    "ADI","ANSS","AON","APA","AAPL","AMAT","APTV","ACGL","ADM","ANET","AJG","AIZ","T","ATO","ADSK","ADP","AZO","AVB",
    "AVY","AXON","BKR","BALL","BAC","BK","BBWI","BAX","BDX","BRK-B","BBY","BIO","TECH","BIIB","BLK","BX","BKNG","BWA",
    "BSX","BMY","AVGO","BR","BRO","BF-B","BLDR","BG","CDNS","CZR","CPT","CPB","COF","CAH","KMX","CCL","CARR","CTLT",
    "CAT","CBOE","CBRE","CDW","CE","COR","CNC","CNP","CF","CHRW","CRL","SCHW","CHTR","CVX","CMG","CB","CHD","CI",
    "CINF","CTAS","CSCO","C","CFG","CLX","CME","CMS","KO","CTSH","CL","CMCSA","CAG","COP","ED","STZ","CEG","COO",
    "CPRT","GLW","CPAY","CTVA","CSGP","COST","CTRA","CCI","CSX","CMI","CVS","DHR","DRI","DVA","DAY","DE","DAL","XRAY",
    "DVN","DXCM","FANG","DLR","DFS","DG","DLTR","D","DPZ","DOV","DOW","DHI","DTE","DUK","DD","EMN","ETN","EBAY",
    "ECL","EIX","EW","EA","ELV","EMR","ENPH","ETR","EOG","EPAM","EQT","EFX","EQR","EQIX","ERIE","ESS","EL","ETSY",
    "EG","EVRG","ES","EXC","EXPE","EXPD","EXR","XOM","FFIV","FSLR","FAST","FRT","FDX","FIS","FITB","FE","FI","FLT",
    "FMC","F","FTNT","FTV","FOXA","FOX","BEN","FCX","GRMN","IT","GE","GEHC","GEV","GEN","GNRC","GD","GIS","GM",
    "GPC","GILD","GPN","GL","GDDY","GS","HAL","HIG","HAS","HCA","DOC","HSIC","HSY","HES","HPE","HLT","HOLX","HD",
    "HON","HRL","HST","HWM","HPQ","HUBB","HUM","HBAN","HII","IBM","IEX","IDXX","ITW","INCY","IR","PODD","INTC","ICE",
    "IFF","IP","IPG","INTU","ISRG","IVZ","INVH","IQV","IRM","JBHT","JBL","JKHY","J","JNJ","JCI","JPM","JNPR","K",
    "KVUE","KMB","KIM","KMI","KLAC","KHC","KR","LHX","LH","LRCX","LW","LVS","LDOS","LEN","LIN","LYV","LKQ","LMT",
    "L","LOW","LULU","LYB","MTB","MRO","MPC","MKTX","MAR","MMC","MLM","MAS","MA","MTCH","MKC","MCD","MCK","MDT","MRK",
    "META","MET","MTD","MGM","MCHP","MU","MSFT","MAA","MRNA","MOH","TAP","MDLZ","MPWR","MNST","MCO","MS","MOS","MSI",
    "MSCI","NDAQ","NTAP","NFLX","NEM","NWSA","NWS","NEE","NKE","NI","NDSN","NSC","NTRS","NOC","NCLH","NRG","NUE",
    "NVDA","NVR","NXPI","ORLY","OXY","ODFL","OMC","ON","OKE","ORCL","OTIS","PCAR","PKG","PLTR","PANW","PH","PAYX",
    "PAYC","PYPL","PNR","PEP","PFE","PCG","PM","PSX","PNC","POOL","PPG","PPL","PFG","PG","PGR","PLD","PRU","PEG",
    "PTC","PSA","PHM","QRVO","PWR","QCOM","DGX","RL","RJF","RTX","O","REG","REGN","RF","RSG","RMD","RVTY","ROK",
    "ROL","ROP","ROST","RCL","SPGI","CRM","SBAC","SLB","STX","SRE","NOW","SHW","SPG","SWKS","SJM","SNA","SOLV",
    "SO","LUV","SWK","SBUX","STT","STLD","STE","SYK","SMCI","SNPS","SYF","SYY","TMUS","TROW","TTWO","TPR","TRGP",
    "TGT","TEL","TDY","TFX","TER","TSLA","TXN","TXT","TMO","TJX","TSCO","TT","TDG","TRV","TRMB","TFC","TYL","TSN",
    "USB","UBER","UDR","ULTA","UNP","UAL","UPS","URI","UNH","UHS","VLO","VTR","VRSN","VRSK","VZ","VRTX","VBG","VMC",
    "WRB","WAB","WMT","DIS","WBD","WM","WAT","WEC","WFC","WELL","WST","WDC","WY","WHR","WMB","WTW","GWW","WYNN",
    "XEL","XYL","YUM","ZBRA","ZBH","ZTS"
]

NASDAQ_FULL = [
    "AAPL","MSFT","NVDA","AMZN","GOOGL","GOOG","META","TSLA","AVGO","AMD","NFLX","COST","TMUS","CSCO","AMAT","PEP",
    "INTU","QCOM","TXN","AMGN","HON","SBUX","INTC","PYPL","ADI","ADP","KLAC","GILD","MDLZ","REGN","LRCX",
    "PANW","SNPS","CDNS","ASML","CRWD","MELI","MAR","CTAS","ORLY","ABNB","WDAY","MNST","ROST","DXCM","FTNT",
    "KDP","PAYX","MCHP","AEP","IDXX","PDD","AZN","BKR","EA","EXC","LULU","XEL","GEHC","BIIB","WBD",
    "DLTR","ODFL","PCAR","ROKU","ZM","DDOG","TEAM","ZS","ENPH","ILMN","MDB","WBA","FAST","VRSK","SIRI",
    "PLTR","SOFI","MARA","COIN","HOOD","RIOT","SNAP","NIO","LCID","BABA","JD","BIDU","NTES","TSM","ARM"
]

TSX_FULL = [f"{t}.TO" for t in [
    "RY","TD","SHOP","ENB","CNR","BNS","BMO","TRP","BAM","SU","CP","CNQ","TRI","MFC","AEM","ATD","WCN","BCE",
    "RCI-B","POW","IMO","FM","TECK-B","DOL","QSR","GIB-A","NTR","GWO","PPL","SLF","IFC","WPM","CVE","PKEY",
    "TOU","EMA","FTS","CAR-UN","H","OTEX","K","GIL","WCP","ARX","CCL-B","CCO","NPI","L","TIH","EFN","ALA","X",
    "KEY","MEG","BTE","CPG","FEI","FFH","STN","IVN","EDV","LUN","HBM","PAAS","ELD","CMMC","IMG","EQX","SSRM"
]]

NYSE_FULL = [
    "BRK-B","JPM","WMT","UNH","V","XOM","MA","PG","JNJ","HD","ORCL","ABBV","BAC","CVX","MRK","TMO","LIN",
    "WFC","ACN","MCD","DIS","ABT","GE","PM","CAT","IBM","VZ","RTX","UBER","LOW","SPGI","UNP","PFE","COP",
    "HON","BA","T","BMY","GS","MS","AXP","BLK","SCHW","C","DE","LMT","EOG","SLB","FI","PLD","CI","SYK","TJX",
    "MMC","AMT","CB","MO","BKNG","NKE","ISRG","EL","VLO","PNC","USB","BDX","MCK","CL","TGT","FCX","FDX"
]

EUROPE_FULL = [
    "MC.PA","OR.PA","TTE.PA","ASML.AS","SAP.DE","SIE.DE","AIR.PA","RMS.PA","SAN.PA","BNP.PA","SU.PA","DG.PA",
    "EL.PA","GLE.PA","CS.PA","CAP.PA","KER.PA","RI.PA","VIE.PA","EN.PA","BAYN.DE","ALV.DE","BMW.DE","MBG.DE",
    "DTE.DE","BAS.DE","MUV2.DE","DHL.DE","VOW3.DE","ADS.DE","INGA.AS","PRX.AS","REN.AS","HEIA.AS","ABN.AS"
]

# ==============================================================================
# 1. PROFILS DE STRATÉGIE
# ==============================================================================
st.sidebar.header("🎯 Profil de Stratégie")

strategy_profile = st.sidebar.radio(
    "Choisissez votre profil :",
    ["🛡️ Conservatrice", "⚖️ Modérée", "🔥 Agressive", "⚙️ Personnalisée"]
)

if strategy_profile == "🛡️ Conservatrice":
    def_min_price, def_max_price = 15.0, 300.0
    def_fast_ema, def_slow_ema = 20, 50
    def_cross_days = 10
    def_min_vol = 1000000
    def_min_mcap = 10000.0
    def_max_pe = 25.0
    def_min_roe = 10.0
    def_max_de = 1.5
    def_min_dte, def_max_dte = 30, 45
    def_min_delta, def_max_delta = 0.10, 0.20

elif strategy_profile == "⚖️ Modérée":
    def_min_price, def_max_price = 10.0, 400.0
    def_fast_ema, def_slow_ema = 20, 50
    def_cross_days = 10
    def_min_vol = 500000
    def_min_mcap = 2000.0
    def_max_pe = 40.0
    def_min_roe = 5.0
    def_max_de = 2.5
    def_min_dte, def_max_dte = 20, 45
    def_min_delta, def_max_delta = 0.15, 0.30

elif strategy_profile == "🔥 Agressive":
    def_min_price, def_max_price = 5.0, 500.0
    def_fast_ema, def_slow_ema = 9, 21
    def_cross_days = 15
    def_min_vol = 300000
    def_min_mcap = 500.0
    def_max_pe = 75.0
    def_min_roe = 0.0
    def_max_de = 4.0
    def_min_dte, def_max_dte = 14, 30
    def_min_delta, def_max_delta = 0.25, 0.40

else:
    def_min_price, def_max_price = 1.0, 1000.0
    def_fast_ema, def_slow_ema = 20, 50
    def_cross_days = 10
    def_min_vol = 100000
    def_min_mcap = 100.0
    def_max_pe = 100.0
    def_min_roe = -20.0
    def_max_de = 10.0
    def_min_dte, def_max_dte = 7, 60
    def_min_delta, def_max_delta = 0.10, 0.45

# ==============================================================================
# 2. GESTION DES 10 LISTES PERSONNALISÉES
# ==============================================================================
if "custom_lists" not in st.session_state:
    st.session_state.custom_lists = {
        "Liste 1 (Technologie)": "AAPL, MSFT, NVDA, AMD, GOOGL, META, AMZN, PLTR, TSLA, INTC, ORCL, CSCO, QCOM, AMAT, IBM",
        "Liste 2 (Canada TSX)": "RY.TO, TD.TO, SHOP.TO, ENB.TO, CNR.TO, BNS.TO, BMO.TO, TRP.TO, BAM.TO, SU.TO, CP.TO, CNQ.TO, MFC.TO, ATD.TO, BCE.TO",
        "Liste 3 (Options High Vol / Meme)": "TSLA, PLTR, SOFI, MARA, COIN, RIOT, SNAP, NIO, HOOD, BABA, UBER, AMD, BAC, F, LCID",
        "Liste 4 (Dividendes / Value)": "JPM, WMT, UNH, V, XOM, MA, PG, JNJ, HD, ABBV, BAC, CVX, MRK, TMO, KO, PEP, MCD",
        "Liste 5 (Énergie / Matériaux)": "XOM, CVX, COP, SLB, EOG, MPC, VLO, OXY, SU.TO, CNQ.TO, TECK-B.TO, NTR.TO, AEM.TO",
        "Liste 6 (Finance & Banques)": "JPM, BAC, WFC, C, GS, MS, RY.TO, TD.TO, BNS.TO, BMO.TO, NA.TO, CM.TO",
        "Liste 7 (Personnalisée 7)": "AAPL, SPY, QQQ, IWM",
        "Liste 8 (Personnalisée 8)": "TSLA, NVDA, AMZN",
        "Liste 9 (Personnalisée 9)": "SHOP.TO, RY.TO, TD.TO",
        "Liste 10 (Personnalisée 10)": "MSFT, GOOGL, META"
    }

# ==============================================================================
# 3. SÉLECTION DU MARCHÉ & UNIVERS DE TITRES
# ==============================================================================
st.sidebar.header("🌐 1. Sélection du Marché")

market_options = [
    f"🏛️ S&P 500 (USA - {len(SP500_FULL)} Actions)",
    f"💻 NASDAQ (USA - {len(NASDAQ_FULL)} Actions)",
    f"🍁 TSX Composite (Canada - {len(TSX_FULL)} Actions)",
    f"🏢 NYSE Large Caps (USA - {len(NYSE_FULL)} Actions)",
    f"🌍 Europe Large Caps (Euronext/DAX - {len(EUROPE_FULL)} Actions)",
    "📂 Utiliser une de mes 10 Listes Personnalisées"
]

market_choice = st.sidebar.selectbox("Choisissez le marché :", market_options)

if "S&P 500" in market_choice:
    full_universe = SP500_FULL
elif "NASDAQ" in market_choice:
    full_universe = NASDAQ_FULL
elif "TSX" in market_choice:
    full_universe = TSX_FULL
elif "NYSE" in market_choice:
    full_universe = NYSE_FULL
elif "Europe" in market_choice:
    full_universe = EUROPE_FULL
else:
    selected_list_name = st.sidebar.selectbox("Choisissez votre liste :", list(st.session_state.custom_lists.keys()))
    
    edited_text = st.sidebar.text_area(
        f"Contenu de {selected_list_name} (séparés par des virgules) :",
        value=st.session_state.custom_lists[selected_list_name],
        height=120
    )
    st.session_state.custom_lists[selected_list_name] = edited_text
    full_universe = [t.strip().upper() for t in edited_text.replace("\n", ",").split(",") if t.strip()]

with st.sidebar.expander("✏️ Éditer mes 10 Listes Personnalisées"):
    for key in st.session_state.custom_lists.keys():
        st.session_state.custom_lists[key] = st.text_area(key, st.session_state.custom_lists[key], height=65)

# --- CONFIGURATION DU MODE SANS LIMITES ---
st.sidebar.markdown("---")
scan_all = st.sidebar.checkbox("🚀 SCANNER TOUTE LA LISTE SANS LIMITE", value=True)

if scan_all:
    universe = full_universe
    st.sidebar.success(f" Mode Illimité Activé : **{len(universe)}** actions vont être analysées.")
else:
    max_scan_count = st.sidebar.slider("Limiter le nombre d'actions à :", min_value=5, max_value=len(full_universe), value=min(50, len(full_universe)))
    universe = full_universe[:max_scan_count]
    st.sidebar.info(f" Analyse limitée aux **{len(universe)}** premiers titres.")

# Estimer la durée du scan
est_seconds = len(universe) * 0.4
est_minutes = math.ceil(est_seconds / 60)
st.sidebar.caption(f"⏱️ Temps estimé pour {len(universe)} titres : environ **{est_minutes} min**.")

# ==============================================================================
# 4. FILTRES
# ==============================================================================
st.sidebar.header("🎯 2. Filtres Techniques")
col_p1, col_p2 = st.sidebar.columns(2)
min_price = col_p1.number_input("Prix Min ($)", value=def_min_price, step=1.0)
max_price = col_p2.number_input("Prix Max ($)", value=def_max_price, step=10.0)

trend_filter = st.sidebar.selectbox("Filtre de Tendance :", ["🟢 Haussier (EMA Rapide > Lente)", "🔴 Baissier (EMA Rapide < Lente)", "⚪ Toutes les Tendances"])

col_e1, col_e2 = st.sidebar.columns(2)
fast_ema = col_e1.number_input("EMA Rapide", value=def_fast_ema, step=1)
slow_ema = col_e2.number_input("EMA Lente", value=def_slow_ema, step=1)

crossover_days = st.sidebar.slider("Fenêtre Croisement (Jours) :", min_value=1, max_value=30, value=def_cross_days)
min_volume = st.sidebar.number_input("Volume Moyen Min", value=def_min_vol, step=100000)

st.sidebar.header("📊 3. Filtres Fondamentaux")
min_mcap = st.sidebar.number_input("Market Cap Min (Millions $)", value=def_min_mcap, step=100.0)
max_pe = st.sidebar.number_input("P/E Max", value=def_max_pe, step=1.0)
min_roe = st.sidebar.number_input("ROE Min (%)", value=def_min_roe, step=1.0)
max_debt_equity = st.sidebar.number_input("Debt / Equity Max", value=def_max_de, step=0.1)

st.sidebar.header("⚙️ 4. Paramètres Options")
col_d1, col_d2 = st.sidebar.columns(2)
min_dte = col_d1.number_input("DTE Min", value=def_min_dte, step=1)
max_dte = col_d2.number_input("DTE Max", value=def_max_dte, step=1)

col_dl1, col_dl2 = st.sidebar.columns(2)
min_delta = col_dl1.number_input("Delta Min", value=def_min_delta, step=0.05)
max_delta = col_dl2.number_input("Delta Max", value=def_max_delta, step=0.05)

# ==============================================================================
# 5. MOTEUR D'ANALYSE
# ==============================================================================
def analyze_stock(ticker_symbol):
    try:
        stock = yf.Ticker(ticker_symbol)
        hist = stock.history(period="120d")
        
        if hist.empty or len(hist) < max(fast_ema, slow_ema) + crossover_days:
            return None

        price = float(hist['Close'].iloc[-1])
        if math.isnan(price) or price <= 0:
            return None

        avg_volume = float(hist['Volume'].tail(20).mean())

        hist['EMA_Fast'] = hist['Close'].ewm(span=fast_ema, adjust=False).mean()
        hist['EMA_Slow'] = hist['Close'].ewm(span=slow_ema, adjust=False).mean()
        hist['Bullish'] = hist['EMA_Fast'] > hist['EMA_Slow']

        is_bullish = bool(hist['Bullish'].iloc[-1])

        recent = hist.tail(crossover_days + 1)
        cross_occurred = False
        for i in range(1, len(recent)):
            if recent['Bullish'].iloc[i-1] != recent['Bullish'].iloc[i]:
                cross_occurred = True
                break

        info = stock.info
        mcap_m = (info.get('marketCap', 0) or 0) / 1e6
        pe_ratio = info.get('trailingPE', None) or info.get('forwardPE', None)
        roe_val = (info.get('returnOnEquity', 0) or 0) * 100.0
        debt_eq = (info.get('debtToEquity', 0) or 0) / 100.0

        return {
            "symbol": ticker_symbol,
            "price": price,
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
# 6. EXÉCUTION DU SCANNER
# ==============================================================================
st.subheader(f"🔍 Analyse de : {market_choice}")
st.write(f"Nombre total de titres à analyser : **{len(universe)}** | Profil : **{strategy_profile}**")

if st.button("🚀 LANCER LE SCAN COMPLET (SANS LIMITE)", type="primary", use_container_width=True):
    status_box = st.empty()
    progress_bar = st.progress(0)
    results = []
    total = len(universe)
    start_time = time.time()

    for idx, sym in enumerate(universe):
        elapsed = round(time.time() - start_time, 1)
        status_box.info(f"⏳ Analyse ({idx+1}/{total}) : **{sym}** | Temps écoulé : {elapsed}s | Opportunités trouvées : {len(results)}")
        progress_bar.progress((idx + 1) / total)

        data = analyze_stock(sym)
        if not data:
            continue

        price = data["price"]

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

        if min_mcap > 0 and data["mcap_m"] < min_mcap:
            continue
        if data["pe"] is not None and data["pe"] > max_pe:
            continue
        if data["roe"] < min_roe:
            continue
        if data["debt_equity"] > max_debt_equity:
            continue

        target_delta = (min_delta + max_delta) / 2.0
        dte = int((min_dte + max_dte) / 2)
        strike = round(price * (1.0 - target_delta * 0.35), 2)
        estimated_premium = round(price * target_delta * 0.08, 2)

        mcap_str = f"${data['mcap_m']/1000:.2f} B" if data['mcap_m'] >= 1000 else f"${data['mcap_m']:.1f} M"

        score = 80
        if data["is_bullish"]: score += 10
        if data["volume"] > 1000000: score += 5
        score = min(score, 99)

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
            "score": score,
            "signal_str": "Haussier" if data["is_bullish"] else "Baissier",
            "signal_icon": "🟢" if data["is_bullish"] else "🔴"
        })

    status_box.empty()
    progress_bar.empty()
    total_time = round(time.time() - start_time, 1)

    if not results:
        st.warning(f"⚠️ Scan terminé en {total_time}s. Aucun titre ne correspond à l'ensemble de vos critères.")
    else:
        results = sorted(results, key=lambda x: x['score'], reverse=True)
        st.success(f"✅ Scan complet terminé en **{total_time}s** ! **{len(results)} opportunités** qualifiées sur {total} titres analysés.")
        
        # Affichage des résultats
        for item in results:
            st.markdown(f"""
            <div style="background-color: #1a2332; border-radius: 8px; padding: 14px 18px; margin-bottom: 12px; border: 1px solid #2d3748;">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <span style="color: #38bdf8; font-size: 22px; font-weight: bold;">
                        {item['ticker']} — ${item['price']} <span style="color: #93c5fd; font-size: 16px;">(PUT conseillé: ${item['strike']})</span>
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
                    Prime estimée: <b style="color: #22c55e;">${item['premium']}</b> | DTE: <b>{item['dte']}j</b> | Delta cible: <b>{item['delta']}</b>
                </div>
            </div>
            """, unsafe_allow_html=True)
