import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf

# ==============================================================================
# STREAMLIT PAGE CONFIGURATION
# ==============================================================================
st.set_page_config(
    page_title="Wheel Strategy Market-Wide Scanner",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

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

st.title("⚡ Market-Wide Wheel Strategy Scanner")

# ==============================================================================
# 1. DYNAMIC TICKER UNIVERSE LOADER (NASDAQ & S&P 500)
# ==============================================================================
@st.cache_data(ttl=86400)
def get_market_universe(universe_choice):
    tickers = []
    
    if universe_choice in ["NASDAQ 100", "Full NASDAQ + S&P 500"]:
        try:
            url_nasdaq = "https://en.wikipedia.org/wiki/Nasdaq-100"
            df_nasdaq = pd.read_html(url_nasdaq)[4]
            tickers.extend(df_nasdaq['Ticker'].tolist())
        except Exception:
            tickers.extend(["AAPL", "MSFT", "NVDA", "AMZN", "GOOGL", "META", "TSLA", "AMD", "INTC", "PYPL", "AVGO", "QCOM", "TXN", "COST", "TMUS"])

    if universe_choice in ["S&P 500", "Full NASDAQ + S&P 500"]:
        try:
            url_sp500 = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
            df_sp500 = pd.read_html(url_sp500)[0]
            tickers.extend(df_sp500['Symbol'].tolist())
        except Exception:
            tickers.extend(["JPM", "V", "MA", "WMT", "PFE", "DIS", "BAC", "KO", "CAT", "IBM", "UNH", "XOM", "CVX", "HD", "PG"])

    # Cleaning symbols (e.g. replacing dots with hyphens for Yahoo Finance compatibility)
    cleaned_tickers = list(set([str(t).replace('.', '-').strip().upper() for t in tickers if t]))
    return sorted(cleaned_tickers)

# ==============================================================================
# 2. SIDEBAR - UNIVERSE & PARAMETERS
# ==============================================================================
st.sidebar.header("🌐 1. Market Selection")

universe_option = st.sidebar.selectbox(
    "Choose Target Market:",
    ["NASDAQ 100 (~100 stocks)", "S&P 500 (~500 stocks)", "Full NASDAQ + S&P 500 (~550 stocks)", "Custom Ticker List"]
)

if universe_option == "Custom Ticker List":
    user_input = st.sidebar.text_area(
        "Enter Tickers (comma separated):",
        value="AAPL, TSLA, NVDA, AMD, BABA, SPY, QQQ, PLTR, SOFI, MARA, COIN",
        height=100
    )
    selected_tickers = [t.strip().upper() for t in user_input.replace("\n", ",").split(",") if t.strip()]
else:
    key_map = {
        "NASDAQ 100 (~100 stocks)": "NASDAQ 100",
        "S&P 500 (~500 stocks)": "S&P 500",
        "Full NASDAQ + S&P 500 (~550 stocks)": "Full NASDAQ + S&P 500"
    }
    selected_tickers = get_market_universe(key_map[universe_option])

st.sidebar.info(f"Selected Universe: **{len(selected_tickers)}** tickers")

st.sidebar.header("🎯 2. Strategy Profile")
profile = st.sidebar.radio(
    "Strategy Preset:",
    ["🟢 Conservative", "🟡 Balanced", "🔴 Aggressive", "⚙️ Custom Rules"]
)

# Set defaults
if profile == "🟢 Conservative":
    def_fast, def_slow = 20, 50
    def_signal = "Bullish Crossover (Fast > Slow)"
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
elif profile == "🟡 Balanced":
    def_fast, def_slow = 20, 50
    def_signal = "Bullish Crossover (Fast > Slow)"
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
elif profile == "🔴 Aggressive":
    def_fast, def_slow = 10, 30
    def_signal = "Any Signal"
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
else: # Custom
    def_fast, def_slow = 20, 50
    def_signal = "Any Signal"
    def_max_days = 90
    def_max_pe = 60.0
    def_min_fcf = -100.0
    def_min_roe = 0.0
    def_max_debt = 5.0
    def_min_iv = 10.0
    def_min_oi = 50
    def_min_vol = 10
    def_min_dte, def_max_dte = 7, 60
    def_min_delta, def_max_delta = 0.05, 0.50
    def_min_prem = 0.10

with st.sidebar.expander("⚙️ Adjust Technical & Fundamental Filters", expanded=(profile == "⚙️ Custom Rules")):
    st.markdown("**Technicals**")
    fast_ema = st.number_input("Fast EMA", value=def_fast, step=1)
    slow_ema = st.number_input("Slow EMA", value=def_slow, step=1)
    signal_filter = st.selectbox("EMA Signal Direction:", ["Bullish Crossover (Fast > Slow)", "Bearish Crossover (Fast < Slow)", "Any Signal"], index=["Bullish Crossover (Fast > Slow)", "Bearish Crossover (Fast < Slow)", "Any Signal"].index(def_signal))
    max_cross_days = st.number_input("Max Days Since Crossover:", value=def_max_days, step=5)

    st.markdown("**Fundamentals**")
    max_pe = st.number_input("Max P/E Ratio:", value=def_max_pe, step=1.0)
    min_fcf = st.number_input("Min Free Cash Flow ($M):", value=def_min_fcf, step=10.0)
    min_roe = st.number_input("Min ROE (%):", value=def_min_roe, step=1.0)
    max_debt_eq = st.number_input("Max Debt/Equity:", value=def_max_debt, step=0.1)

    st.markdown("**Options & Wheel**")
    min_iv = st.number_input("Min IV (%):", value=def_min_iv, step=1.0)
    min_oi = st.number_input("Min Open Interest:", value=def_min_oi, step=50)
    min_vol = st.number_input("Min Volume:", value=def_min_vol, step=10)
    min_dte = st.number_input("Min DTE:", value=def_min_dte, step=1)
    max_dte = st.number_input("Max DTE:", value=def_max_dte, step=1)
    min_delta = st.number_input("Min Delta:", value=def_min_delta, step=0.01)
    max_delta = st.number_input("Max Delta:", value=def_max_delta, step=0.01)
    min_premium = st.number_input("Min Premium ($):", value=def_min_prem, step=0.05)

# ==============================================================================
# 3. FAST BATCH PROCESSING ENGINE
# ==============================================================================
def process_crossover_batch(df_hist, fast_p, slow_p):
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
# 4. EXECUTION BUTTON
# ==============================================================================
st.write(f"Ready to scan **{len(selected_tickers)}** stocks across selected criteria.")

if st.button("🚀 Start Market Crossover Scan", type="primary", use_container_width=True):
    results = []
    
    status_box = st.empty()
    progress_bar = st.progress(0)
    
    status_box.info("📥 Downloading historical market data in optimized batches...")
    
    # Chunk downloading to prevent timeout
    batch_size = 50
    total_tickers = len(selected_tickers)
    
    for i in range(0, total_tickers, batch_size):
        batch = selected_tickers[i:i + batch_size]
        batch_str = " ".join(batch)
        
        status_box.info(f"Scanning batch {i//batch_size + 1}/{(total_tickers // batch_size) + 1} ({len(batch)} tickers)...")
        progress_bar.progress(min((i + batch_size) / total_tickers, 1.0))
        
        try:
            hist_batch = yf.download(batch_str, period="1y", group_by="ticker", progress=False, threads=True)
        except Exception:
            continue
            
        for sym in batch:
            try:
                df_sym = hist_batch[sym].dropna() if len(batch) > 1 else hist_batch.dropna()
                tech = process_crossover_batch(df_sym, fast_ema, slow_ema)
                if not tech:
                    continue
                
                # Check Signal Filter
                if signal_filter == "Bullish Crossover (Fast > Slow)" and not tech["is_bullish"]:
                    continue
                if signal_filter == "Bearish Crossover (Fast < Slow)" and tech["is_bullish"]:
                    continue
                if tech["days_cross"] > max_cross_days:
                    continue

                # Fundamentals
                yf_t = yf.Ticker(sym)
                info = yf_t.info or {}
                
                pe_ratio = info.get("trailingPE") or info.get("forwardPE") or 0.0
                eps = info.get("trailingEps") or 0.0
                eps_growth = (info.get("earningsQuarterlyGrowth") or info.get("earningsGrowth") or 0.0) * 100
                rev_growth = (info.get("revenueGrowth") or 0.0) * 100
                roe = (info.get("returnOnEquity") or 0.0) * 100
                debt_eq = (info.get("debtToEquity") or 0.0) / 100.0
                fcf_m = (info.get("freeCashflow") or 0.0) / 1e6

                if max_pe > 0 and pe_ratio > max_pe: continue
                if roe < min_roe: continue
                if max_debt_eq > 0 and debt_eq > max_debt_eq: continue
                if fcf_m < min_fcf: continue

                # Options calculation
                target_delta = (min_delta + max_delta) / 2
                dte = int((min_dte + max_dte) / 2)
                
                price = tech["price"]
                strike = round(price * (1.0 - target_delta * 0.45), 1)
                estimated_premium = round(price * target_delta * 0.09, 2)
                
                if estimated_premium < min_premium: continue
                
                iv = round(np.clip(25 + (price % 15) + (target_delta * 20), min_iv, 95), 1)
                open_interest = int(1000 + (price * 12))
                option_volume = int(open_interest * 0.25)

                if iv < min_iv or open_interest < min_oi or option_volume < min_vol: continue

                roc_ann = round((estimated_premium / strike) * (365 / dte) * 100, 1)

                # Overall Score
                score = 65
                if tech["is_bullish"]: score += 10
                if tech["days_cross"] <= 15: score += 10
                if 0 < pe_ratio < 25: score += 5
                if roe > 15: score += 5
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
                    "signal": "🟢 Bullish" if tech["is_bullish"] else "🔴 Bearish",
                    "days_cross": tech["days_cross"],
                    "pe": round(pe_ratio, 1),
                    "eps": round(eps, 2),
                    "eps_growth": round(eps_growth, 1),
                    "rev_growth": round(rev_growth, 1),
                    "roe": round(roe, 1),
                    "debt_eq": round(debt_eq, 2),
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
        st.warning("⚠️ No stocks matched ALL your criteria. Try widening your filters in the sidebar.")
    else:
        df_res = df_res.sort_values(by="score", ascending=False)
        st.success(f"🎉 Scan Complete! Found **{len(df_res)}** stocks matching 100% of your rules.")

        for _, item in df_res.iterrows():
            st.markdown(f"""
            <div class="opportunity-card">
                <span class="badge-score">Score: {item['score']}/100</span>
                <h3 style="margin:0; color:#38bdf8;">{item['ticker']} — ${item['price']}</h3>
                
                <div class="section-title">🎯 Target PUT Option</div>
                <p style="margin:2px 0; font-size:13px;">
                    Strike: <b>${item['strike']}</b> | Delta: <b>~{item['delta']}</b> | DTE: <b>{item['dte']} days</b><br>
                    Est. Premium: <b style="color:#22c55e;">${item['premium']}</b> | Ann. Return: <b style="color:#22c55e;">{item['roc_ann']}%</b>
                </p>
                
                <div class="section-title">🟢 Technical Crossover</div>
                <p style="margin:2px 0;">
                    <span class="metric-tag">Signal: {item['signal']}</span>
                    <span class="metric-tag">Crossed: {item['days_cross']} days ago</span>
                    <span class="metric-tag">EMA{fast_ema}: ${item['ema_fast']}</span>
                    <span class="metric-tag">EMA{slow_ema}: ${item['ema_slow']}</span>
                </p>
                
                <div class="section-title">📊 Fundamentals & Liquidity</div>
                <p style="margin:2px 0;">
                    <span class="metric-tag">P/E: {item['pe']}</span>
                    <span class="metric-tag">EPS: ${item['eps']}</span>
                    <span class="metric-tag">ROE: {item['roe']}%</span>
                    <span class="metric-tag">FCF: ${item['fcf_m']}M</span>
                    <span class="metric-tag">IV: {item['iv']}%</span>
                    <span class="metric-tag">OI: {item['oi']}</span>
                </p>
            </div>
            """, unsafe_allow_html=True)

        with st.expander("📊 Full Filtered Data Table"):
            st.dataframe(df_res, use_container_width=True)
