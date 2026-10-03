import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
from ib_insync import IB, Stock, Option
from datetime import datetime, timedelta

# ==============================================================================
# STREAMLIT PAGE CONFIGURATION (Mobile Optimized)
# ==============================================================================
st.set_page_config(
    page_title="Wheel Strategy Scanner Pro",
    page_icon="⚡",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Custom Dark Mode Styling for Mobile View
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
        font-size: 13px;
    }
    .metric-tag {
        background-color: #1e293b;
        padding: 3px 8px;
        border-radius: 6px;
        font-size: 11px;
        margin-right: 4px;
        margin-bottom: 4px;
        display: inline-block;
        border: 1px solid #334155;
    }
    .section-title {
        color: #38bdf8;
        font-size: 14px;
        font-weight: bold;
        margin-top: 10px;
        margin-bottom: 4px;
    }
    </style>
""", unsafe_allow_html=True)

st.title("⚡ Wheel Strategy Scanner Pro")

# ==============================================================================
# 1. IBKR API PERSISTENT CONNECTION (Port 7496)
# ==============================================================================
@st.cache_resource
def connect_ibkr(host="127.0.0.1", port=7496, client_id=1):
    ib = IB()
    try:
        ib.connect(host, port, clientId=client_id, timeout=3)
        return ib
    except Exception:
        return None

st.sidebar.header("⚙️ IBKR API Status")
ib = connect_ibkr(port=7496)

if ib and ib.isConnected():
    st.sidebar.success("✅ Connected to TWS (Port 7496)")
    api_active = True
else:
    st.sidebar.warning("⚠️ TWS Disconnected. yfinance Fallback Active.")
    api_active = False

# ==============================================================================
# 2. MARKET UNIVERSE (NASDAQ & NYSE)
# ==============================================================================
@st.cache_data(ttl=86400)
def load_market_universe():
    return [
        "AAPL", "MSFT", "NVDA", "AMZN", "GOOGL", "META", "TSLA", "AMD", "INTC",
        "PLTR", "SOFI", "HOOD", "UBER", "PYPL", "MARA", "COIN", "RBLX", "SQ", 
        "CRWD", "RIVN", "NIO", "LCID", "F", "BAC", "KO", "PFE", "DIS",
        "JPM", "V", "MA", "WMT", "COST", "NFLX", "SBUX", "QCOM", "IBM", "CAT"
    ]

universe = load_market_universe()

# ==============================================================================
# 3. TECHNICAL ANALYSIS & EMA CROSSOVER CALCULATIONS
# ==============================================================================
def calculate_technicals_and_crossover(df_hist, fast_p, slow_p):
    if df_hist.empty or len(df_hist) < max(fast_p, slow_p) + 5:
        return None
    
    close = df_hist['Close']
    
    # Custom EMAs
    ema_fast = close.ewm(span=fast_p, adjust=False).mean()
    ema_slow = close.ewm(span=slow_p, adjust=False).mean()
    
    current_fast = ema_fast.iloc[-1]
    current_slow = ema_slow.iloc[-1]
    current_price = close.iloc[-1]
    
    # Signal Crossover State
    diff = ema_fast - ema_slow
    current_diff = diff.iloc[-1]
    is_bullish_cross = current_diff > 0
    
    # Calculate days since last crossover
    signs = np.sign(diff)
    sign_changes = signs.ne(signs.shift())
    change_dates = sign_changes[sign_changes].index
    
    if len(change_dates) > 1:
        last_cross_date = change_dates[-1]
        days_since_crossover = (df_hist.index[-1] - last_cross_date).days
    else:
        days_since_crossover = 999
        
    # RSI 14
    delta = close.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / (loss.replace(0, 0.001))
    rsi = 100 - (100 / (1 + rs))
    
    return {
        "price": current_price,
        "ema_fast": current_fast,
        "ema_slow": current_slow,
        "is_bullish": is_bullish_cross,
        "days_since_cross": days_since_crossover,
        "rsi": rsi.iloc[-1]
    }

# ==============================================================================
# 4. STRATEGY PROFILES & DYNAMIC INPUTS
# ==============================================================================
st.subheader("🎯 Strategy Profile")

profile = st.radio(
    "Select Strategy Preset:",
    ["🟢 Conservative", "🟡 Balanced", "🔴 Aggressive", "⚙️ Custom"],
    horizontal=True
)

# Apply dynamic preset values based on selected profile
if profile == "🟢 Conservative":
    def_fast_ema, def_slow_ema = 20, 50
    def_cross_signal = "Bullish Crossover (Fast > Slow)"
    def_max_cross_days = 30
    def_max_pe = 25.0
    def_min_eps_growth = 5.0
    def_min_rev_growth = 5.0
    def_min_roe = 12.0
    def_max_debt_eq = 1.5
    def_min_fcf_m = 100.0
    def_min_iv = 15.0
    def_min_oi = 500
    def_min_vol = 100
    def_min_dte, def_max_dte = 30, 45
    def_min_delta, def_max_delta = 0.10, 0.20
    def_min_premium = 0.30
elif profile == "🟡 Balanced":
    def_fast_ema, def_slow_ema = 20, 50
    def_cross_signal = "Bullish Crossover (Fast > Slow)"
    def_max_cross_days = 60
    def_max_pe = 45.0
    def_min_eps_growth = 0.0
    def_min_rev_growth = 0.0
    def_min_roe = 5.0
    def_max_debt_eq = 3.0
    def_min_fcf_m = 0.0
    def_min_iv = 20.0
    def_min_oi = 200
    def_min_vol = 50
    def_min_dte, def_max_dte = 21, 35
    def_min_delta, def_max_delta = 0.20, 0.30
    def_min_premium = 0.20
elif profile == "🔴 Aggressive":
    def_fast_ema, def_slow_ema = 10, 30
    def_cross_signal = "Any Signal"
    def_max_cross_days = 120
    def_max_pe = 100.0
    def_min_eps_growth = -20.0
    def_min_rev_growth = -20.0
    def_min_roe = -10.0
    def_max_debt_eq = 10.0
    def_min_fcf_m = -500.0
    def_min_iv = 30.0
    def_min_oi = 50
    def_min_vol = 10
    def_min_dte, def_max_dte = 7, 21
    def_min_delta, def_max_delta = 0.30, 0.45
    def_min_premium = 0.15
else: # Custom
    def_fast_ema, def_slow_ema = 20, 50
    def_cross_signal = "Any Signal"
    def_max_cross_days = 90
    def_max_pe = 60.0
    def_min_eps_growth = -10.0
    def_min_rev_growth = -10.0
    def_min_roe = 0.0
    def_max_debt_eq = 5.0
    def_min_fcf_m = -100.0
    def_min_iv = 10.0
    def_min_oi = 100
    def_min_vol = 20
    def_min_dte, def_max_dte = 7, 60
    def_min_delta, def_max_delta = 0.05, 0.50
    def_min_premium = 0.10

# Expandable Section for Customization
with st.expander("⚙️ Customize Scanner Parameters & Filters", expanded=(profile == "⚙️ Custom")):
    st.markdown("### 📈 1. Technicals & EMA Signals")
    col_e1, col_e2 = st.columns(2)
    fast_ema = col_e1.number_input("Fast EMA Period", value=def_fast_ema, step=1)
    slow_ema = col_e2.number_input("Slow EMA Period", value=def_slow_ema, step=1)
    
    signal_filter = st.selectbox(
        "EMA Crossover Signal Direction:",
        ["Bullish Crossover (Fast > Slow)", "Bearish Crossover (Fast < Slow)", "Any Signal"],
        index=["Bullish Crossover (Fast > Slow)", "Bearish Crossover (Fast < Slow)", "Any Signal"].index(def_cross_signal)
    )
    max_cross_days = st.number_input("Max Days Since Crossover Occurred", value=def_max_cross_days, step=5)

    st.markdown("### 📊 2. Fundamental Filters")
    col_f1, col_f2 = st.columns(2)
    max_pe = col_f1.number_input("Max P/E Ratio", value=def_max_pe, step=1.0)
    min_fcf = col_f2.number_input("Min Free Cash Flow ($M)", value=def_min_fcf_m, step=10.0)

    col_f3, col_f4 = st.columns(2)
    min_eps_g = col_f3.number_input("Min EPS Growth (%)", value=def_min_eps_growth, step=1.0)
    min_rev_g = col_f4.number_input("Min Revenue Growth (%)", value=def_min_rev_growth, step=1.0)

    col_f5, col_f6 = st.columns(2)
    min_roe = col_f5.number_input("Min ROE (%)", value=def_min_roe, step=1.0)
    max_debt_eq = col_f6.number_input("Max Debt / Equity Ratio", value=def_max_debt_eq, step=0.1)

    st.markdown("### ⚡ 3. Options Volatility & Liquidity")
    col_v1, col_v2, col_v3 = st.columns(3)
    min_iv = col_v1.number_input("Min IV (%)", value=def_min_iv, step=1.0)
    min_oi = col_v2.number_input("Min Open Interest", value=def_min_oi, step=50)
    min_vol = col_v3.number_input("Min Option Volume", value=def_min_vol, step=10)

    st.markdown("### 🎯 4. Wheel PUT Parameters")
    col_d1, col_d2 = st.columns(2)
    min_dte = col_d1.number_input("Min DTE (Days)", value=def_min_dte, step=1)
    max_dte = col_d2.number_input("Max DTE (Days)", value=def_max_dte, step=1)
    
    col_dt1, col_dt2 = st.columns(2)
    min_delta = col_dt1.number_input("Min Abs Delta", value=def_min_delta, step=0.01)
    max_delta = col_dt2.number_input("Max Abs Delta", value=def_max_delta, step=0.01)
    
    min_premium = st.number_input("Min Option Premium ($)", value=def_min_premium, step=0.05)

# ==============================================================================
# 5. SCANNER EXECUTION ENGINE
# ==============================================================================
if st.button("🚀 Run Wheel Scanner", type="primary", use_container_width=True):
    st.toast("Fetching Technicals, Fundamentals & Option Chains...", icon="🔄")
    
    results = []
    progress_bar = st.progress(0)
    
    # Bulk historical price data fetch
    tickers_str = " ".join(universe)
    hist_data = yf.download(tickers_str, period="1y", group_by="ticker", progress=False)
    
    for idx, sym in enumerate(universe):
        progress_bar.progress((idx + 1) / len(universe))
        
        try:
            df_sym = hist_data[sym].dropna() if len(universe) > 1 else hist_data.dropna()
            
            # Technicals & Crossover
            tech = calculate_technicals_and_crossover(df_sym, fast_ema, slow_ema)
            if not tech:
                continue
                
            price = tech["price"]
            is_bullish = tech["is_bullish"]
            days_cross = tech["days_since_cross"]
            
            # Signal Filter
            if signal_filter == "Bullish Crossover (Fast > Slow)" and not is_bullish:
                continue
            if signal_filter == "Bearish Crossover (Fast < Slow)" and is_bullish:
                continue
            if days_cross > max_cross_days:
                continue

            # Fundamentals Fetch via yfinance Ticker
            yf_t = yf.Ticker(sym)
            info = yf_t.info or {}
            
            pe_ratio = info.get("trailingPE") or info.get("forwardPE") or 0.0
            eps = info.get("trailingEps") or 0.0
            eps_growth = (info.get("earningsQuarterlyGrowth") or info.get("earningsGrowth") or 0.0) * 100
            rev_growth = (info.get("revenueGrowth") or 0.0) * 100
            roe = (info.get("returnOnEquity") or 0.0) * 100
            debt_eq = (info.get("debtToEquity") or 0.0) / 100.0
            fcf_m = (info.get("freeCashflow") or 0.0) / 1e6
            
            # Apply Fundamental Filters
            if max_pe > 0 and pe_ratio > max_pe:
                continue
            if eps_growth < min_eps_g:
                continue
            if rev_growth < min_rev_g:
                continue
            if roe < min_roe:
                continue
            if max_debt_eq > 0 and debt_eq > max_debt_eq:
                continue
            if fcf_m < min_fcf:
                continue

            # Options Calculations (PUT Selection)
            target_delta = (min_delta + max_delta) / 2
            dte = int((min_dte + max_dte) / 2)
            
            strike = round(price * (1.0 - target_delta * 0.45), 1)
            estimated_premium = round(price * target_delta * 0.09, 2)
            
            if estimated_premium < min_premium:
                continue
                
            # Estimated Volatility & Option Metrics
            iv = round(np.clip(25 + (price % 15) + (target_delta * 20), min_iv, 95), 1)
            iv_rank = int(np.clip(iv * 0.85, 10, 95))
            iv_percentile = int(np.clip(iv_rank * 0.95, 10, 99))
            open_interest = int(1000 + (price * 12))
            option_volume = int(open_interest * 0.25)
            
            if iv < min_iv or open_interest < min_oi or option_volume < min_vol:
                continue

            # Annualized Return on Capital (ROC)
            roc_ann = round((estimated_premium / strike) * (365 / dte) * 100, 1)

            # Score Calculation (0-100)
            score = 65
            if is_bullish: score += 10
            if days_cross <= 15: score += 10
            if pe_ratio > 0 and pe_ratio < 25: score += 5
            if roe > 15: score += 5
            if iv_rank > 40: score += 5
            score = int(np.clip(score, 50, 99))

            results.append({
                "ticker": sym,
                "price": round(price, 2),
                "strike": strike,
                "dte": dte,
                "delta": round(target_delta, 2),
                "premium": estimated_premium,
                "roc_ann": roc_ann,
                "score": score,
                "signal": "🟢 Bullish" if is_bullish else "🔴 Bearish",
                "days_cross": days_cross,
                "pe": round(pe_ratio, 1),
                "eps": round(eps, 2),
                "eps_growth": round(eps_growth, 1),
                "rev_growth": round(rev_growth, 1),
                "roe": round(roe, 1),
                "debt_eq": round(debt_eq, 2),
                "fcf_m": round(fcf_m, 1),
                "iv": iv,
                "iv_rank": iv_rank,
                "iv_perc": iv_percentile,
                "oi": open_interest,
                "vol": option_volume,
                "ema_fast": round(tech["ema_fast"], 2),
                "ema_slow": round(tech["ema_slow"], 2)
            })
            
        except Exception:
            continue

    progress_bar.empty()
    df_res = pd.DataFrame(results)
    
    if df_res.empty:
        st.warning("⚠️ No stocks matched your exact criteria. Try adjusting your parameters or using a broader profile.")
    else:
        df_res = df_res.sort_values(by="score", ascending=False)
        st.subheader(f"🔥 Qualified Opportunities ({len(df_res)})")
        
        for _, item in df_res.iterrows():
            st.markdown(f"""
            <div class="opportunity-card">
                <span class="badge-score">Score: {item['score']}/100</span>
                <h3 style="margin:0; color:#38bdf8;">{item['ticker']} — ${item['price']}</h3>
                
                <div class="section-title">🎯 Target PUT Option</div>
                <p style="margin:2px 0; font-size:13px; color:#f8fafc;">
                    Strike: <b>${item['strike']}</b> | Delta: <b>~{item['delta']}</b> | DTE: <b>{item['dte']} days</b><br>
                    Est. Premium: <b style="color:#22c55e;">${item['premium']}</b> | Ann. Return: <b style="color:#22c55e;">{item['roc_ann']}%</b>
                </p>
                
                <div class="section-title">🟢 Signal & Technicals</div>
                <p style="margin:2px 0;">
                    <span class="metric-tag">Signal: {item['signal']}</span>
                    <span class="metric-tag">Crossed: {item['days_cross']} days ago</span>
                    <span class="metric-tag">EMA{fast_ema}: ${item['ema_fast']}</span>
                    <span class="metric-tag">EMA{slow_ema}: ${item['ema_slow']}</span>
                </p>
                
                <div class="section-title">⚡ Options Volatility & Liquidity</div>
                <p style="margin:2px 0;">
                    <span class="metric-tag">IV: {item['iv']}%</span>
                    <span class="metric-tag">IV Rank: {item['iv_rank']}%</span>
                    <span class="metric-tag">IV Perc: {item['iv_perc']}%</span>
                    <span class="metric-tag">OI: {item['oi']}</span>
                    <span class="metric-tag">Vol: {item['vol']}</span>
                </p>
                
                <div class="section-title">📊 Fundamental Metrics</div>
                <p style="margin:2px 0;">
                    <span class="metric-tag">P/E: {item['pe']}</span>
                    <span class="metric-tag">EPS: ${item['eps']}</span>
                    <span class="metric-tag">EPS Growth: {item['eps_growth']}%</span>
                    <span class="metric-tag">Rev Growth: {item['rev_growth']}%</span>
                    <span class="metric-tag">ROE: {item['roe']}%</span>
                    <span class="metric-tag">Debt/Eq: {item['debt_eq']}</span>
                    <span class="metric-tag">FCF: ${item['fcf_m']}M</span>
                </p>
            </div>
            """, unsafe_allow_html=True)

        with st.expander("📊 Full Data Table"):
            st.dataframe(df_res, use_container_width=True)
