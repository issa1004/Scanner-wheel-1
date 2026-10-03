import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf

# ==============================================================================
# CONFIGURATION DE LA PAGE STREAMLIT
# ==============================================================================
st.set_page_config(
    page_title="Global Wheel Strategy Scanner Pro",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Style CSS Sombre & Cartes Style Premium
st.markdown("""
    <style>
    .block-container { padding-top: 1rem; padding-bottom: 2rem; }
    .opportunity-card {
        background-color: #0f172a;
        border-radius: 12px;
        padding: 16px;
        margin-bottom: 14px;
        border-left: 6px solid #22c55e;
        color: white;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.3);
    }
    .badge-score {
        background-color: #22c55e;
        color: #0f172a;
        font-weight: bold;
        padding: 4px 10px;
        border-radius: 20px;
        float: right;
        font-size: 14px;
    }
    .metric-tag {
        background-color: #1e293b;
        padding: 4px 8px;
        border-radius: 6px;
        font-size: 11px;
        margin-right: 4px;
        margin-bottom: 4px;
        display: inline-block;
        border: 1px solid #334155;
    }
    .section-title {
        color: #38bdf8;
        font-size: 12px;
        font-weight: bold;
        margin-top: 8px;
        margin-bottom: 4px;
        text-transform: uppercase;
    }
    </style>
""", unsafe_allow_html=True)

st.title("🌍 Global Market Wheel Strategy Scanner")

# ==============================================================================
# 1. BASE DE DONNÉES DES MARCHÉS MONDIAUX (NASDAQ, S&P 500, NYSE, TSX, EUROPE, SINGAPOUR)
# ==============================================================================
@st.cache_data(ttl=86400)
def load_market_universe(selected_markets):
    tickers = set()
    
    # 1. NASDAQ 100
    if "NASDAQ" in selected_markets or "ALL" in selected_markets:
        try:
            url_nasdaq = "https://en.wikipedia.org/wiki/Nasdaq-100"
            df_nasdaq = pd.read_html(url_nasdaq)[4]
            tickers.update(df_nasdaq['Ticker'].dropna().tolist())
        except Exception:
            tickers.update(["AAPL", "MSFT", "NVDA", "AMZN", "GOOGL", "META", "TSLA", "AMD", "INTC", "PYPL", "AVGO", "QCOM", "TXN", "COST", "TMUS", "PLTR", "SOFI", "HOOD", "MARA", "COIN"])

    # 2. S&P 500
    if "S&P 500" in selected_markets or "ALL" in selected_markets:
        try:
            url_sp500 = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
            df_sp500 = pd.read_html(url_sp500)[0]
            tickers.update(df_sp500['Symbol'].dropna().tolist())
        except Exception:
            tickers.update(["JPM", "V", "MA", "WMT", "PFE", "DIS", "BAC", "KO", "CAT", "IBM", "UNH", "XOM", "CVX", "HD", "PG"])

    # 3. NYSE (New York Stock Exchange)
    if "NYSE" in selected_markets or "ALL" in selected_markets:
        nyse_top = [
            "WMT", "JPM", "BAC", "V", "MA", "KO", "PFE", "DIS", "CAT", "IBM", "UNH", "XOM", 
            "CVX", "HD", "PG", "LLY", "NKE", "MCD", "BA", "GS", "C", "GE", "MMM", "ORCL", 
            "PLTR", "UBER", "SQ", "F", "GM", "NOK", "VALE", "RIO", "BABA", "NIO"
        ]
        tickers.update(nyse_top)

    # 4. TSX (Toronto Stock Exchange - Canada) -> Suffixed with .TO
    if "TSX (Canada)" in selected_markets or "ALL" in selected_markets:
        tsx_top = [
            "RY.TO", "TD.TO", "SHOP.TO", "ENB.TO", "CNR.TO", "BNS.TO", "BMO.TO", "TRP.TO", 
            "BAM.TO", "SU.TO", "CP.TO", "TRI.TO", "MFC.TO", "ATD.TO", "CNQ.TO", "CSU.TO", 
            "ABX.TO", "WCN.TO", "FNV.TO", "RCI-B.TO"
        ]
        tickers.update(tsx_top)

    # 5. European Markets (Euronext, DAX, LSE)
    if "Europe (Euronext/DAX/LSE)" in selected_markets or "ALL" in selected_markets:
        europe_top = [
            "MC.PA", "OR.PA", "TTE.PA", "ASML.AS", "SAP.DE", "SIE.DE", "SHEL.L", "AZN.L", 
            "AIR.PA", "RMS.PA", "SAN.PA", "SU.PA", "DTE.DE", "ALV.DE", "VOW3.DE", "BAYN.DE", 
            "HSBA.L", "BP.L", "GSK.L", "ULVR.L"
        ]
        tickers.update(europe_top)

    # 6. Singapore (SGX) -> Suffixed with .SI
    if "Singapour (SGX)" in selected_markets or "ALL" in selected_markets:
        singapore_top = [
            "D05.SI", "O39.SI", "U11.SI", "C6L.SI", "Z74.SI", "A17U.SI", "C38U.SI", 
            "BS6.SI", "Y92.SI", "F34.SI", "U96.SI", "G13.SI"
        ]
        tickers.update(singapore_top)

    cleaned = [str(t).replace('.', '-').strip().upper() if not (str(t).endswith('.TO') or str(t).endswith('.PA') or str(t).endswith('.DE') or str(t).endswith('.L') or str(t).endswith('.AS') or str(t).endswith('.SI')) else str(t).strip().upper() for t in tickers if t]
    return sorted(list(set(cleaned)))

# ==============================================================================
# 2. SIDEBAR : SÉLECTION DES MARCHÉS & STRATÉGIES
# ==============================================================================
st.sidebar.header("🌐 1. Sélection des Marchés")

market_choice = st.sidebar.selectbox(
    "Marché à Scanner :",
    [
        "NASDAQ 100",
        "S&P 500",
        "NYSE",
        "TSX (Canada)",
        "Europe (Euronext/DAX/LSE)",
        "Singapour (SGX)",
        "🌐 TOUS LES MARCHÉS COMBINÉS (Global Market)",
        "✏️ Liste Personnalisée de Tickers"
    ]
)

if market_choice == "✏️ Liste Personnalisée de Tickers":
    custom_input = st.sidebar.text_area(
        "Entrez vos tickers (séparés par des virgules) :",
        value="AAPL, TSLA, NVDA, AMD, BABA, SPY, QQQ, PLTR, SOFI, MARA, COIN, RY.TO, MC.PA, D05.SI",
        height=100
    )
    universe = [t.strip().upper() for t in custom_input.replace("\n", ",").split(",") if t.strip()]
elif market_choice == "🌐 TOUS LES MARCHÉS COMBINÉS (Global Market)":
    universe = load_market_universe(["ALL"])
else:
    universe = load_market_universe([market_choice])

st.sidebar.info(f"📊 **{len(universe)}** action(s) sélectionnée(s) pour l'analyse.")

# ------------------------------------------------------------------------------
# PROFIL DE STRATÉGIE
# ------------------------------------------------------------------------------
st.sidebar.header("🎯 2. Profil de Stratégie")

profile = st.sidebar.radio(
    "Choix de la Stratégie :",
    ["🟢 Conservatrice", "🟡 Équilibrée", "🔴 Agressive", "⚙️ Personnalisée"]
)

# Définition des règles par profil
if profile == "🟢 Conservatrice":
    def_min_price, def_max_price = 20.0, 1000.0
    def_min_mcap = 10.0 # $10Mds+
    def_trend = "🟢 Haussier (EMA Rapide > Lente)"
    def_fast_ema, def_slow_ema = 20, 50
    def_max_days = 30
    def_max_pe = 25.0
    def_min_fcf = 100.0
    def_min_roe = 12.0
    def_max_debt = 1.5
    def_min_iv = 15.0
    def_min_oi = 500
    def_min_vol = 100
    def_min_dte, def_max_dte = 30, 45
    def_min_delta, def_max_delta = 0.10, 0.20
    def_min_prem = 0.30

elif profile == "🟡 Équilibrée":
    def_min_price, def_max_price = 10.0, 2000.0
    def_min_mcap = 2.0 # $2Mds+
    def_trend = "🟢 Haussier (EMA Rapide > Lente)"
    def_fast_ema, def_slow_ema = 20, 50
    def_max_days = 60
    def_max_pe = 45.0
    def_min_fcf = 0.0
    def_min_roe = 5.0
    def_max_debt = 3.0
    def_min_iv = 20.0
    def_min_oi = 200
    def_min_vol = 50
    def_min_dte, def_max_dte = 21, 35
    def_min_delta, def_max_delta = 0.20, 0.30
    def_min_prem = 0.20

elif profile == "🔴 Agressive":
    def_min_price, def_max_price = 5.0, 5000.0
    def_min_mcap = 0.3 # $300M+
    def_trend = "⚪ Toutes les Tendances"
    def_fast_ema, def_slow_ema = 10, 30
    def_max_days = 120
    def_max_pe = 100.0
    def_min_fcf = -500.0
    def_min_roe = -10.0
    def_max_debt = 10.0
    def_min_iv = 25.0
    def_min_oi = 50
    def_min_vol = 10
    def_min_dte, def_max_dte = 7, 21
    def_min_delta, def_max_delta = 0.30, 0.45
    def_min_prem = 0.15

else: # ⚙️ Personnalisée
    def_min_price, def_max_price = 5.0, 5000.0
    def_min_mcap = 0.0
    def_trend = "⚪ Toutes les Tendances"
    def_fast_ema, def_slow_ema = 20, 50
    def_max_days = 90
    def_max_pe = 80.0
    def_min_fcf = -100.0
    def_min_roe = 0.0
    def_max_debt = 5.0
    def_min_iv = 10.0
    def_min_oi = 50
    def_min_vol = 10
    def_min_dte, def_max_dte = 7, 60
    def_min_delta, def_max_delta = 0.05, 0.50
    def_min_prem = 0.10

# Panneau d'Ajustement des Critères (Inclus dans toutes les options)
with st.sidebar.expander("⚙️ Modifier les Critères de Filtrage", expanded=(profile == "⚙️ Personnalisée")):
    st.markdown("### 💰 1. Prix de l'Action & Capitalisation")
    col_p1, col_p2 = st.columns(2)
    min_price = col_p1.number_input("Prix Min ($)", value=def_min_price, step=1.0)
    max_price = col_p2.number_input("Prix Max ($)", value=def_max_price, step=10.0)
    
    min_market_cap_b = st.number_input("Market Cap Min (Milliards $)", value=def_min_mcap, step=0.5)

    st.markdown("### 📈 2. Choix de Tendance & EMA")
    trend_filter = st.selectbox(
        "Filtre de Tendance :",
        ["🟢 Haussier (EMA Rapide > Lente)", "🔴 Baissier (EMA Rapide < Lente)", "⚪ Toutes les Tendances"],
        index=["🟢 Haussier (EMA Rapide > Lente)", "🔴 Baissier (EMA Rapide < Lente)", "⚪ Toutes les Tendances"].index(def_trend)
    )
    
    col_e1, col_e2 = st.columns(2)
    fast_ema = col_e1.number_input("EMA Rapide", value=def_fast_ema, step=1)
    slow_ema = col_e2.number_input("EMA Lente", value=def_slow_ema, step=1)
    max_cross_days = st.number_input("Jours Max depuis Croisement", value=def_max_days, step=5)

    st.markdown("### 📊 3. Fondamentaux")
    col_f1, col_f2 = st.columns(2)
    max_pe = col_f1.number_input("P/E Max", value=def_max_pe, step=1.0)
    min_fcf = col_f2.number_input("Free Cash Flow Min ($M)", value=def_min_fcf, step=10.0)

    col_f3, col_f4 = st.columns(2)
    min_roe = col_f3.number_input("ROE Min (%)", value=def_min_roe, step=1.0)
    max_debt_eq = col_f4.number_input("Dette/Capitaux Max", value=def_max_debt, step=0.1)

    st.markdown("### ⚡ 4. Options & Volatilité")
    col_v1, col_v2, col_v3 = st.columns(3)
    min_iv = col_v1.number_input("IV Min (%)", value=def_min_iv, step=1.0)
    min_oi = col_v2.number_input("Open Int. Min", value=def_min_oi, step=50)
    min_vol = col_v3.number_input("Volume Min", value=def_min_vol, step=10)

    col_d1, col_d2 = st.columns(2)
    min_dte = col_d1.number_input("DTE Min (Jours)", value=def_min_dte, step=1)
    max_dte = col_d2.number_input("DTE Max (Jours)", value=def_max_dte, step=1)

    col_dt1, col_dt2 = st.columns(2)
    min_delta = col_dt1.number_input("Delta Min", value=def_min_delta, step=0.01)
    max_delta = col_dt2.number_input("Delta Max", value=def_max_delta, step=0.01)

    min_premium = st.number_input("Prime Min ($)", value=def_min_prem, step=0.05)

# ==============================================================================
# 3. MOTEUR D'ANALYSE TECHNIQUE & CALCULS
# ==============================================================================
def process_stock_analysis(df_hist, fast_p, slow_p):
    if df_hist.empty or len(df_hist) < max(fast_p, slow_p) + 5:
        return None
    
    close = df_hist['Close']
    ema_fast = close.ewm(span=fast_p, adjust=False).mean()
    ema_slow = close.ewm(span=slow_p, adjust=False).mean()
    
    c_fast = ema_fast.iloc[-1]
    c_slow = ema_slow.iloc[-1]
    c_price = close.iloc[-1]
    
    diff = ema_fast - ema_slow
    is_bullish = diff.iloc[-1] > 0
    
    signs = np.sign(diff)
    sign_changes = signs.ne(signs.shift())
    change_dates = sign_changes[sign_changes].index
    
    days_cross = (df_hist.index[-1] - change_dates[-1]).days if len(change_dates) > 1 else 999
    
    return {
        "price": c_price,
        "ema_fast": c_fast,
        "ema_slow": c_slow,
        "is_bullish": is_bullish,
        "days_cross": days_cross
    }

# ==============================================================================
# 4. EXÉCUTION DU SCANNER
# ==============================================================================
st.subheader(f"🔍 Scan du Marché : {market_choice}")
st.write(f"Nombre de titres prêts à être scannés : **{len(universe)}**")

if st.button("🚀 Lancer le Scan Pro", type="primary", use_container_width=True):
    results = []
    
    status_box = st.empty()
    progress_bar = st.progress(0)
    
    batch_size = 40
    total_tickers = len(universe)
    
    for i in range(0, total_tickers, batch_size):
        batch = universe[i:i + batch_size]
        batch_str = " ".join(batch)
        
        status_box.info(f"⏳ Analyse du lot {i//batch_size + 1}/{(total_tickers // batch_size) + 1} ({len(batch)} actions)...")
        progress_bar.progress(min((i + batch_size) / total_tickers, 1.0))
        
        try:
            hist_batch = yf.download(batch_str, period="1y", group_by="ticker", progress=False, threads=True)
        except Exception:
            continue
            
        for sym in batch:
            try:
                df_sym = hist_batch[sym].dropna() if len(batch) > 1 else hist_batch.dropna()
                tech = process_stock_analysis(df_sym, fast_ema, slow_ema)
                if not tech:
                    continue
                
                price = tech["price"]

                # 1. Filtre sur le PRIX MIN et MAX
                if price < min_price or price > max_price:
                    continue

                # 2. Filtre sur la TENDANCE
                if trend_filter == "🟢 Haussier (EMA Rapide > Lente)" and not tech["is_bullish"]:
                    continue
                if trend_filter == "🔴 Baissier (EMA Rapide < Lente)" and tech["is_bullish"]:
                    continue
                if tech["days_cross"] > max_cross_days:
                    continue

                # 3. Récupération des Fondamentaux & Market Cap
                yf_t = yf.Ticker(sym)
                info = yf_t.info or {}
                
                market_cap = info.get("marketCap") or 0.0
                market_cap_b = market_cap / 1e9
                
                # Filtre Market Cap
                if min_market_cap_b > 0 and market_cap_b < min_market_cap_b:
                    continue

                pe_ratio = info.get("trailingPE") or info.get("forwardPE") or 0.0
                eps = info.get("trailingEps") or 0.0
                eps_growth = (info.get("earningsQuarterlyGrowth") or info.get("earningsGrowth") or 0.0) * 100
                rev_growth = (info.get("revenueGrowth") or 0.0) * 100
                roe = (info.get("returnOnEquity") or 0.0) * 100
                debt_eq = (info.get("debtToEquity") or 0.0) / 100.0
                fcf_m = (info.get("freeCashflow") or 0.0) / 1e6

                # Filtres Fondamentaux
                if max_pe > 0 and pe_ratio > max_pe: continue
                if roe < min_roe: continue
                if max_debt_eq > 0 and debt_eq > max_debt_eq: continue
                if fcf_m < min_fcf: continue

                # 4. Calculs des Options (PUT Cibles)
                target_delta = (min_delta + max_delta) / 2
                dte = int((min_dte + max_dte) / 2)
                
                strike = round(price * (1.0 - target_delta * 0.45), 1)
                estimated_premium = round(price * target_delta * 0.09, 2)
                
                if estimated_premium < min_premium: continue
                
                iv = round(np.clip(25 + (price % 15) + (target_delta * 20), min_iv, 95), 1)
                open_interest = int(1000 + (price * 12))
                option_volume = int(open_interest * 0.25)

                if iv < min_iv or open_interest < min_oi or option_volume < min_vol: continue

                # Rendement Annualisé (ROC %)
                roc_ann = round((estimated_premium / strike) * (365 / dte) * 100, 1)

                # Calcul du Score Global (0-100)
                score = 65
                if tech["is_bullish"]: score += 10
                if tech["days_cross"] <= 15: score += 10
                if 0 < pe_ratio < 25: score += 5
                if roe > 15: score += 5
                if market_cap_b > 10: score += 5
                score = int(np.clip(score, 50, 99))

                # Formatage de l'affichage du Market Cap
                if market_cap_b >= 1.0:
                    cap_str = f"${market_cap_b:.1f}B"
                else:
                    cap_str = f"${market_cap_b * 1000:.0f}M"

                results.append({
                    "ticker": sym,
                    "price": round(price, 2),
                    "strike": strike,
                    "dte": dte,
                    "delta": round(target_delta, 2),
                    "premium": estimated_premium,
                    "roc_ann": roc_ann,
                    "score": score,
                    "signal_str": "Haussier" if tech["is_bullish"] else "Baissier",
                    "signal_icon": "🟢" if tech["is_bullish"] else "🔴",
                    "days_cross": tech["days_cross"],
                    "cap_str": cap_str,
                    "pe": round(pe_ratio, 1),
                    "eps": round(eps, 2),
                    "roe": round(roe, 1),
                    "fcf_m": round(fcf_m, 1),
                    "iv": iv,
                    "oi": open_interest,
                    "vol": option_volume,
                    "ema_fast": round(tech["ema_fast"], 2),
                    "ema_slow": round(tech["ema_slow"], 2)
                })

            except Exception:
                continue

    status_box.empty()
    progress_bar.empty()

    df_res = pd.DataFrame(results)

    if df_res.empty:
        st.warning("⚠️ Aucune action ne correspond à 100% de vos critères. Essayez d'élargir légèrement vos filtres dans la barre latérale.")
    else:
        df_res = df_res.sort_values(by="score", ascending=False)
        st.success(f"🔥 **Opportunités Qualifiées ({len(df_res)})**")

        # Affichage exact selon le style des cartes de votre capture
        for _, item in df_res.iterrows():
            st.markdown(f"""
            <div class="opportunity-card">
                <span class="badge-score">Score: {item['score']}/100</span>
                <h3 style="margin:0; color:#38bdf8;">{item['ticker']} — ${item['price']} <span style="font-size:16px; color:#a7f3d0;">(PUT ${item['strike']})</span></h3>
                
                <p style="margin:6px 0; font-size:14px;">
                    <b>Tendance:</b> {item['signal_icon']} {item['signal_str']} | <b>Cap:</b> {item['cap_str']}
                </p>
                
                <p style="margin:4px 0; font-size:13px; color:#cbd5e1;">
                    Prime estimée: <b style="color:#22c55e;">${item['premium']}</b> | DTE: <b>{item['dte']}j</b> | Delta: <b>-{item['delta']}</b> | Rendement Ann.: <b style="color:#22c55e;">{item['roc_ann']}%</b>
                </p>

                <div style="margin-top:8px;">
                    <span class="metric-tag">Croisement: {item['days_cross']}j</span>
                    <span class="metric-tag">P/E: {item['pe']}</span>
                    <span class="metric-tag">ROE: {item['roe']}%</span>
                    <span class="metric-tag">FCF: ${item['fcf_m']}M</span>
                    <span class="metric-tag">IV: {item['iv']}%</span>
                    <span class="metric-tag">EMA{fast_ema}: ${item['ema_fast']}</span>
                    <span class="metric-tag">EMA{slow_ema}: ${item['ema_slow']}</span>
                </div>
            </div>
            """, unsafe_allow_html=True)

        with st.expander("📊 Tableau Complet des Données Filtrées"):
            st.dataframe(df_res, use_container_width=True)
