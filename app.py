import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta
import time
from datetime import datetime, timedelta
import pytz

# [系統設定]
st.set_page_config(page_title="Blade God V14.7 指揮官", page_icon="⚔️", layout="wide")

# [UI 極致美化 - V14.7 旗艦戰術風格]
st.markdown("""
<style>
    /* 引入 Google Fonts: JetBrains Mono (數據用) & Roboto (介面用) */
    @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;700&family=Roboto:wght@300;400;700;900&display=swap');
    
    /* 全局變數 */
    :root {
        --primary-color: #007AFF;
        --success-color: #34C759;
        --danger-color: #FF3B30;
        --bg-color: #F5F7FA;
        --card-bg: #FFFFFF;
        --text-color: #1D1D1F;
    }

    /* 基礎設定 */
    .stApp {
        background-color: var(--bg-color);
        font-family: 'Roboto', sans-serif;
        color: var(--text-color);
    }
    
    h1, h2, h3 {
        font-family: 'Roboto', sans-serif;
        font-weight: 900;
        letter-spacing: -0.5px;
    }

    /* 側邊欄美化 */
    section[data-testid="stSidebar"] {
        background-color: #FFFFFF;
        border-right: 1px solid rgba(0,0,0,0.05);
        box-shadow: 4px 0 24px rgba(0,0,0,0.02);
    }
    
    /* 卡片容器樣式 */
    .stExpander {
        border: none !important;
        background: transparent !important;
        box-shadow: none !important;
    }
    
    div[data-testid="stExpander"] details {
        border-radius: 16px;
        background-color: #FFFFFF;
        border: 1px solid rgba(0,0,0,0.06);
        box-shadow: 0 4px 12px rgba(0,0,0,0.03);
        margin-bottom: 12px;
        overflow: hidden;
        transition: all 0.3s ease;
    }
    div[data-testid="stExpander"] details:hover {
        box-shadow: 0 8px 24px rgba(0,0,0,0.06);
        transform: translateY(-2px);
    }
    
    /* 風控儀表板 (HUD Style) */
    .risk-hud {
        background: linear-gradient(135deg, #2B32B2 0%, #1488CC 100%);
        color: white;
        padding: 20px;
        border-radius: 16px;
        box-shadow: 0 10px 20px rgba(20, 136, 204, 0.3);
        margin-bottom: 20px;
        position: relative;
        overflow: hidden;
    }
    .risk-hud::before {
        content: '';
        position: absolute;
        top: -50%;
        left: -50%;
        width: 200%;
        height: 200%;
        background: radial-gradient(circle, rgba(255,255,255,0.1) 0%, transparent 60%);
        pointer-events: none;
    }
    .hud-title {
        font-size: 0.8rem;
        text-transform: uppercase;
        letter-spacing: 1px;
        opacity: 0.9;
        margin-bottom: 5px;
    }
    .hud-value {
        font-family: 'JetBrains Mono', monospace;
        font-size: 2.2rem;
        font-weight: 700;
        margin-bottom: 5px;
        text-shadow: 0 2px 4px rgba(0,0,0,0.2);
    }
    .hud-sub {
        font-size: 0.85rem;
        background: rgba(255,255,255,0.2);
        padding: 4px 10px;
        border-radius: 20px;
        display: inline-block;
    }
    
    /* 警報框 - 呼吸燈效 */
    .alert-box { 
        padding: 16px; 
        border-radius: 12px; 
        margin-bottom: 20px; 
        text-align: center; 
        background: linear-gradient(to right, #e8f5e9, #f1f8e9);
        border-left: 5px solid var(--success-color);
        box-shadow: 0 4px 15px rgba(52, 199, 89, 0.15);
        animation: pulse-green 2s infinite;
    }
    .alert-title {
        color: var(--success-color);
        font-weight: 900;
        font-size: 1.1rem;
        margin-bottom: 4px;
        text-transform: uppercase;
    }
    .alert-content {
        color: #1c4f23;
        font-size: 1rem;
        font-weight: 500;
        font-family: 'JetBrains Mono', monospace;
    }
    
    @keyframes pulse-green {
        0% { box-shadow: 0 0 0 0 rgba(52, 199, 89, 0.4); }
        70% { box-shadow: 0 0 0 10px rgba(52, 199, 89, 0); }
        100% { box-shadow: 0 0 0 0 rgba(52, 199, 89, 0); }
    }

    /* CVD 視覺化區塊 - 現代化 */
    .cvd-wrapper {
        display: grid; 
        grid-template-columns: 1fr 1fr; 
        gap: 12px; 
        margin-top: 10px;
    }
    .cvd-box {
        padding: 12px; 
        border-radius: 12px; 
        background-color: #FFFFFF; 
        border: 1px solid #EAEAEA;
        box-shadow: 0 2px 8px rgba(0,0,0,0.04);
        text-align: center;
        transition: transform 0.2s;
    }
    .cvd-box:hover {
        transform: translateY(-3px);
        box-shadow: 0 6px 16px rgba(0,0,0,0.08);
        border-color: var(--primary-color);
    }
    
    .bar-container { 
        display: flex; align-items: flex-end; justify-content: center;
        height: 40px; gap: 4px; margin-top: 10px; padding-bottom: 5px; 
        border-bottom: 2px solid #F5F5F5;
    }
    .bar { width: 10px; border-radius: 4px 4px 0 0; } 
    .bar-green { background: linear-gradient(to top, #34C759, #81F59B); }
    .bar-red { background: linear-gradient(to top, #FF3B30, #FF8580); }
    
    .cvd-title { font-weight: 800; font-size: 0.85rem; color: #333; margin-bottom: 4px; }
    .cvd-desc { font-size: 0.75rem; color: #888; font-weight: 500; }

    /* 按鈕 - 戰術風格 */
    div.stButton > button {
        width: 100%;
        background: #1D1D1F;
        color: white;
        border: none;
        padding: 12px 24px;
        font-size: 1rem;
        font-weight: 700;
        border-radius: 12px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.2);
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    div.stButton > button:hover {
        background: #333336;
        box-shadow: 0 8px 20px rgba(0,0,0,0.3);
        transform: translateY(-1px);
    }
    div.stButton > button:active {
        transform: translateY(1px);
    }
    
    /* 輸入框美化 */
    .stNumberInput input { 
        background-color: #F5F7FA; 
        color: #1D1D1F; 
        font-weight: 700; 
        border: 1px solid transparent; 
        border-radius: 8px;
    }
    .stNumberInput input:focus {
        border-color: var(--primary-color);
        background-color: #FFFFFF;
    }

</style>
""", unsafe_allow_html=True)

# [全域變數]
if 'manual_inputs' not in st.session_state: st.session_state.manual_inputs = {}

# [標的清單]
SYMBOLS = {
    "🥇 黃金 (Gold)": "GC=F",
    "🥈 白銀 (Silver)": "SI=F",
    "🇺🇸 道瓊 (US30)": "YM=F",
    "💷 英鎊 (GBP)": "GBPUSD=X",
    "🇯🇵 日圓 (JPY)": "JPY=X" 
}

# [即時報價對映]
REALTIME_MAPPING = {
    "GC=F": "XAUUSD=X",
    "SI=F": "XAGUSD=X"
}

# [備援價格]
FALLBACK_PRICES = {
    "GC=F": 2600.0, "SI=F": 30.0, "YM=F": 44000.0, "GBPUSD=X": 1.2500, "JPY=X": 150.0
}

TIMEFRAMES = {"⚡ M5": "5m", "⚔️ M15": "15m"}

# [輔助函數]
def get_tw_time():
    return (datetime.utcnow() + timedelta(hours=8)).strftime('%H:%M:%S')

# [核心：MTF 趨勢掃描]
@st.cache_data(ttl=60)
def get_h1_trend():
    tickers = list(SYMBOLS.values())
    try:
        data = yf.download(tickers, period="5d", interval="60m", group_by='ticker', progress=False)
        trends = {}
        for s_code in tickers:
            try:
                if len(tickers) > 1: df = data[s_code]
                else: df = data
                df = df.dropna()
                if df.empty: continue
                close = df['Close']; ema20 = ta.ema(close, length=20).iloc[-1]
                price = close.iloc[-1]
                trends[s_code] = "🐂 多頭" if price > ema20 else "🐻 空頭"
            except: trends[s_code] = "⚪ 未知"
        return trends
    except: return {}

# [V14.2 核心] 智能數據獲取
def get_realtime_quote(ticker):
    target_ticker = REALTIME_MAPPING.get(ticker, ticker)
    current_time = datetime.now(pytz.timezone('Asia/Taipei'))
    
    def fetch_and_check(t_symbol):
        try:
            df = yf.download(t_symbol, period="1d", interval="1m", progress=False)
            if df.empty: return None
            
            if isinstance(df.columns, pd.MultiIndex):
                try: close_val = df.xs(t_symbol, axis=1, level=0)['Close'].iloc[-1]
                except: close_val = df['Close'].iloc[-1]
            else: close_val = df['Close'].iloc[-1]
            
            price = float(close_val)
            last_dt = df.index[-1]
            if last_dt.tzinfo is None: last_dt = last_dt.replace(tzinfo=pytz.utc)
            last_dt_tw = last_dt.astimezone(pytz.timezone('Asia/Taipei'))
            diff_mins = (current_time - last_dt_tw).total_seconds() / 60
            time_str = last_dt_tw.strftime('%H:%M:%S')
            return price, time_str, diff_mins
        except: return None

    res = fetch_and_check(target_ticker)
    if res: return res
    if target_ticker != ticker:
        res = fetch_and_check(ticker)
        if res: return res
    return None, None, 9999

# [輔助函數：統一風控計算邏輯]
def calculate_safe_lots(balance, price, symbol_name):
    leverage = 200 
    if "黃金" in symbol_name: 
        c_size = 100; survival_dist = 100.0; label_d = "$100 美金"
    elif "白銀" in symbol_name: 
        c_size = 5000; survival_dist = 4.0; label_d = "$4 美金"
    elif "道瓊" in symbol_name: 
        c_size = 5; survival_dist = 1000.0; label_d = "1000 點"
    elif "英鎊" in symbol_name: 
        c_size = 100000; survival_dist = 0.0200; label_d = "200 點 (0.02)"
    elif "日圓" in symbol_name: 
        c_size = 100000; survival_dist = 2.00; label_d = "200 點 (2.00)"
    else:
        c_size = 100; survival_dist = 100.0; label_d = "N/A"
        
    if "日圓" in symbol_name:
        safe_l = (balance * 0.9 * price) / (c_size * survival_dist * 1.5) 
    else:
        safe_l = (balance * 0.9) / (c_size * survival_dist)
    
    return max(0.01, round(safe_l, 2)), label_d

# [側邊欄：風控與輸入]
with st.sidebar:
    st.title("⚙️ 指揮官設定")
    st.caption("TACTICAL SETTINGS")
    
    # 風控計算機 (使用 V14.7 HUD 樣式)
    with st.expander("💰 風控儀表板 (Risk HUD)", expanded=True):
        risk_asset = st.selectbox("計算目標:", list(SYMBOLS.keys()))
        ticker = SYMBOLS[risk_asset]
        rt_price, rt_time, rt_lag = get_realtime_quote(ticker)
        
        if rt_price is None: rt_price = FALLBACK_PRICES.get(ticker, 0.0)
            
        bal = st.number_input("本金 (USD):", value=1000, step=100, key="rb")
        # 隱藏現價輸入，但保留邏輯
        if rt_price > 0:
            cal_lots, cal_dist = calculate_safe_lots(bal, rt_price, risk_asset)
            # HUD 顯示
            st.markdown(f"""
            <div class="risk-hud">
                <div class="hud-title">建議手數 (SAFE LOTS)</div>
                <div class="hud-value">{cal_lots:.2f}</div>
                <div class="hud-sub">生存距離: {cal_dist}</div>
                <div style="font-size: 0.7rem; margin-top: 8px; opacity: 0.7;">Ref Price: {rt_price:.2f}</div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.error("⚠️ 數據連線中斷")

    st.subheader("🕵️ 戰術矩陣 (分流)")
    for s_name, s_code in SYMBOLS.items():
        with st.expander(f"{s_name}", expanded=False):
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("**⚡ M5**")
                s5 = st.selectbox("訊號", ["無", "黃標", "紫標"], key=f"s5_{s_code}")
                c5 = st.selectbox("CVD", ["一般", "強買", "強賣", "吸收", "誘多"], key=f"c5_{s_code}")
            with col2:
                st.markdown("**⚔️ M15**")
                s15 = st.selectbox("訊號", ["無", "黃標", "紫標"], key=f"s15_{s_code}")
                c15 = st.selectbox("CVD", ["一般", "強買", "強賣", "吸收", "誘多"], key=f"c15_{s_code}")
            st.session_state.manual_inputs[s_code] = {
                "M5": {"signal": s5, "cvd": c5}, "M15": {"signal": s15, "cvd": c15}
            }

    st.divider()
    auto = st.checkbox("自動刷新", value=False)
    rate = st.slider("秒數", 10, 300, 30)
    sound = st.checkbox("音效警報", value=True)
    if st.button("🚀 刷新戰場數據", type="primary"): st.rerun()

# [核心分析邏輯]
def analyze(name, ticker, df, h1_trend, user_balance, tf_key):
    try:
        df = df.dropna()
        if len(df) < 10: return None 
        
        close = df['Close']; high = df['High']; low = df['Low']
        ema20 = ta.ema(close, length=20).iloc[-1]
        ema60 = ta.ema(close, length=60).iloc[-1]
        ema240 = ta.ema(close, length=240).iloc[-1]
        atr = ta.atr(high, low, close, length=14).iloc[-1]
        
        rt_price, rt_time, rt_lag = get_realtime_quote(ticker)
        price = rt_price if rt_price else close.iloc[-1]
        time_display = rt_time if rt_time else "延遲"
        
        if rt_time:
            if rt_lag < 2: time_display = f"🟢 {rt_time}"
            elif rt_lag < 15: time_display = f"🟡 {rt_time}"
            else: time_display = f"🔴 {rt_time}"
        
        if pd.isna(atr) or atr <= 0: atr = 0.5 
        
        vol_status = "🔥 活躍"; vol_safe = True
        atr_limit = 1.0 if "黃金" in name else (0.05 if "白銀" in name else (20 if "道瓊" in name else 0.05))
        if atr < atr_limit: 
            vol_status = "<span class='vol-low'>🩸 死魚</span>"; vol_safe = False
        else:
            vol_status = "<span class='vol-high'>🔥 活躍</span>"
            
        mtf_bonus = 10 if "多頭" in h1_trend else (-10 if "空頭" in h1_trend else 0)

        loc_score = 0
        if price > ema20: loc_score = 5 
        elif price > ema60: loc_score = 10 
        elif price > ema240: loc_score = 5 
        else: loc_score = -10 

        safe_lots, _ = calculate_safe_lots(user_balance, price, name)
        
        all_inputs = st.session_state.manual_inputs.get(ticker, {})
        tf_inputs = all_inputs.get(tf_key, {"signal": "無", "cvd": "一般"})
        u_sig, u_cvd = tf_inputs['signal'], tf_inputs['cvd']
        
        manual_display = "-"
        if u_sig != "無" or u_cvd != "一般":
            # 簡化顯示以配合版面
            sig_icon = {"無": "", "黃標": "🟨", "紫標": "🟪"}
            cvd_icon = {"一般": "", "強買": "🟢", "強賣": "🔴", "吸收": "📉", "誘多": "📈"}
            manual_display = f"{sig_icon.get(u_sig, '')}{cvd_icon.get(u_cvd, '')}"
        
        action = "WAIT"; score = 0
        sl = 0.0; tp = 0.0
        
        sl_long = price - (1.5 * atr); tp_long = price + (2.5 * atr)
        sl_short = price + (1.5 * atr); tp_short = price - (2.5 * atr)

        has_manual_signal = (u_sig != "無")
        
        if vol_safe == False and not has_manual_signal:
            action = "🚫 波動不足"; score = 10
            sl = sl_long; tp = tp_long
        else:
            if "黃標" in u_sig:
                if "強賣" in u_cvd or "誘多" in u_cvd: 
                    action, score = "🛑 假訊號", 0 
                elif "吸收" in u_cvd or "強買" in u_cvd:
                    score = 95 + mtf_bonus + loc_score 
                    action = "🚀 FIRE (做多)" 
                else:
                    score = 75 + mtf_bonus + loc_score
                    action = "⚡ 嘗試做多"
                sl = sl_long; tp = tp_long
                
            elif "紫標" in u_sig:
                short_loc_score = -loc_score 
                if "強買" in u_cvd or "吸收" in u_cvd: 
                    action, score = "🛑 假訊號", 0 
                elif "誘多" in u_cvd or "強賣" in u_cvd:
                    score = 95 - mtf_bonus + short_loc_score
                    action = "🪓 FIRE (做空)" 
                else:
                    score = 75 - mtf_bonus + short_loc_score
                    action = "⚡ 嘗試做空"
                sl = sl_short; tp = tp_short
                
            else: # 無訊號
                diff = (price - ema20) / atr
                if price > ema60 and price < ema20: 
                    action = "👀 關注"; score = 60 + mtf_bonus; sl = sl_long; tp = tp_long
                elif price < ema60 and price > ema240:
                    action = "🛡️ 防守"; score = 55 + mtf_bonus; sl = sl_long; tp = tp_long
                elif diff > 2.5: 
                    action = "⚠️ 過熱 (找空)"; score = 70 - mtf_bonus; sl = sl_short; tp = tp_short
                elif diff < -2.5: 
                    action = "⚠️ 超跌 (找多)"; score = 70 + mtf_bonus; sl = sl_long; tp = tp_long
                else: 
                    action = "💤 盤整"; score = 20; sl = sl_long; tp = tp_long

        score = max(0, min(100, score))

        return {
            "商品": name, "數據時間": time_display, "波動": vol_status, "現價": price, 
            "手動": manual_display,
            "AI 建議": action, 
            "止損": f"{sl:.2f}", 
            "止盈": f"{tp:.2f}",
            "手數": f"{safe_lots}", "預估勝率": score
        }
    except Exception as e: return None

# [主畫面佈局]
col_main, col_info = st.columns([0.6, 0.4])

with col_main:
    st.title("🧿 Blade God V14.7 指揮官")
    st.caption(f"GitHub 託管版 | 極致美學 | V14.7")

with col_info:
    st.markdown("""
<div class="cvd-wrapper">
    <div class="cvd-box">
        <div class="cvd-title">📉 吸收 (做多)</div>
        <div class="bar-container">
            <div class="bar bar-red" style="height: 100%;"></div>
            <div class="bar bar-red" style="height: 60%;"></div>
            <div class="bar bar-green" style="height: 20%;"></div>
        </div>
        <div class="cvd-desc">跌+紅縮</div>
    </div>
    <div class="cvd-box">
        <div class="cvd-title">📈 誘多 (做空)</div>
        <div class="bar-container">
            <div class="bar bar-green" style="height: 100%;"></div>
            <div class="bar bar-green" style="height: 60%;"></div>
            <div class="bar bar-red" style="height: 20%;"></div>
        </div>
        <div class="cvd-desc">漲+綠縮</div>
    </div>
    <div class="cvd-box">
        <div class="cvd-title">🟢 強勢買進</div>
        <div class="bar-container">
            <div class="bar bar-green" style="height: 40%;"></div>
            <div class="bar bar-green" style="height: 70%;"></div>
            <div class="bar bar-green" style="height: 100%;"></div>
        </div>
        <div class="cvd-desc">綠柱長</div>
    </div>
    <div class="cvd-box">
        <div class="cvd-title">🔴 強勢賣出</div>
        <div class="bar-container">
            <div class="bar bar-red" style="height: 40%;"></div>
            <div class="bar bar-red" style="height: 70%;"></div>
            <div class="bar bar-red" style="height: 100%;"></div>
        </div>
        <div class="cvd-desc">紅柱長</div>
    </div>
</div>
""", unsafe_allow_html=True)

sound_placeholder = st.empty()
tickers = list(SYMBOLS.values())
high_alert = False

for t_name, t_code in TIMEFRAMES.items():
    st.subheader(f"{t_name} 戰場")
    tf_key = "M5" if "M5" in t_name else "M15"
    
    try:
        data = yf.download(tickers, period="5d", interval=t_code, group_by='ticker', progress=False)
        tasks = []
        seen_tickers = set()
        
        for s_name, s_code in SYMBOLS.items():
            if s_code in seen_tickers: continue
            try:
                if len(tickers) > 1: df = data[s_code]
                else: df = data
                
                trend_ctx = get_h1_trend().get(s_code, "⚪ 未知")
                res = analyze(s_name, s_code, df, trend_ctx, st.session_state.get('rb', 1000), tf_key)
                if res: 
                    tasks.append(res)
                    seen_tickers.add(s_code)
                    if res['預估勝率'] >= 85: high_alert = True
            except: continue
            
        if tasks:
            df_res = pd.DataFrame(tasks) 
            st.dataframe(
                df_res[["商品", "數據時間", "波動", "現價", "手動", "AI 建議", "止損", "止盈", "手數", "預估勝率"]],
                use_container_width=True, hide_index=True,
                column_config={
                    "預估勝率": st.column_config.ProgressColumn("勝率", format="%d%%", min_value=0, max_value=100),
                    "手動": st.column_config.TextColumn("戰術", width="small"),
                    "AI 建議": st.column_config.TextColumn("指令", validate="^.*$"),
                    "止損": st.column_config.TextColumn("止損", help="ATR 1.5"),
                    "止盈": st.column_config.TextColumn("止盈", help="ATR 2.5")
                }
            )
            
            high_conf_items = df_res[df_res['預估勝率'] >= 70].sort_values(by="預估勝率", ascending=False)
            if not high_conf_items.empty:
                for idx, row in high_conf_items.iterrows():
                    st.markdown(f"""
                    <div class="alert-box">
                        <div class="alert-title">{row['商品']} | 勝率 {row['預估勝率']}%</div>
                        <div class="alert-content">
                            👉 {row['AI 建議']} | 手數: {row['手數']} | 止損: {row['止損']}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

    except Exception as e: st.error(f"數據讀取中... ({str(e)})")

if high_alert and sound:
    sound_placeholder.empty()
    time.sleep(0.1)
    sound_placeholder.markdown(f"""
        <audio autoplay>
        <source src="https://assets.mixkit.co/active_storage/sfx/2869/2869-preview.mp3?t={int(time.time())}" type="audio/mp3">
        </audio>
    """, unsafe_allow_html=True)
    st.toast("🚨 偵測到高勝率訊號！", icon="🔥")

if auto:
    time.sleep(rate)
    st.rerun()
