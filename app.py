import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta
import time
from datetime import datetime, timedelta

# [系統設定]
st.set_page_config(page_title="Blade God V13.2 指揮官", page_icon="⚔️", layout="wide")

# [樣式優化]
st.markdown("""
<style>
    /* 全局字體 */
    html, body, [class*="css"], .stDataFrame { font-family: 'Microsoft JhengHei', sans-serif; color: #000000 !important; }
    .stDataFrame { font-size: 1.15rem !important; font-weight: 500; }
    
    /* 狀態顏色 */
    .vol-high { color: #007020 !important; font-weight: 900; } 
    .vol-low { color: #8B0000 !important; font-weight: 900; } 
    
    /* 側邊欄 */
    section[data-testid="stSidebar"] { width: 450px !important; background-color: #f0f2f6; }
    
    /* 警報框 */
    .alert-box { 
        padding: 15px; border-radius: 8px; margin-bottom: 15px; 
        text-align: center; font-size: 1.2rem; font-weight: bold;
        background-color: #e6fffa; border: 2px solid #2ea043; color: #004d1a;
        box-shadow: 0 4px 10px rgba(0,0,0,0.1);
    }
    
    /* CVD 視覺化圖塊 (橫向版優化) */
    .cvd-box {
        flex: 1; /* 平均分配寬度 */
        padding: 8px; border-radius: 6px; 
        background-color: #ffffff; border: 1px solid #ddd;
        box-shadow: 0 1px 2px rgba(0,0,0,0.05);
        min-width: 0; /* 防止破版 */
    }
    .bar-container { display: flex; align-items: flex-end; height: 35px; gap: 3px; margin-top: 5px; padding-bottom: 3px; border-bottom: 1px dashed #eee;}
    .bar { width: 100%; border-radius: 2px; } /* 寬度自動填滿 */
    .bar-green { background-color: #2ea043; }
    .bar-red { background-color: #da3633; }
    
    .cvd-title { font-weight: bold; font-size: 0.85rem; color: #333; text-align: center; white-space: nowrap; }
    .cvd-desc { font-size: 0.75rem; color: #666; margin-top: 4px; line-height: 1.2; text-align: center; }

    /* 分隔線優化 */
    hr { margin: 0.5em 0; }
    
    /* 輸入區塊緊湊化 */
    .stSelectbox { margin-bottom: 0px !important; }
    div[data-testid="stExpander"] div[data-testid="stVerticalBlock"] { gap: 0.5rem; }
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

# [側邊欄：風控與輸入]
with st.sidebar:
    st.title("⚙️ 戰術設定")
    
    # 風控計算機 (維持 V13.0 自動抓價功能)
    with st.expander("💰 風控計算機 (Auto-Price)", expanded=True):
        risk_asset = st.selectbox("計算目標:", list(SYMBOLS.keys()))
        ticker = SYMBOLS[risk_asset]
        
        try:
            ticker_df = yf.download(ticker, period="1d", interval="5m", progress=False)
            if not ticker_df.empty:
                if len(ticker_df.columns.levels) > 1:
                    cur_price = ticker_df.xs(ticker, axis=1, level=0)['Close'].iloc[-1]
                else:
                    cur_price = ticker_df['Close'].iloc[-1]
            else: cur_price = 0.0
        except: cur_price = 0.0
            
        px = st.number_input(f"目前現價 (M5):", value=float(cur_price), format="%.3f", key=f"price_{risk_asset}")
        bal = st.number_input("帳戶本金 (USD):", value=1000, step=100, key="rb")

        if "黃金" in risk_asset: 
            c_size = 100; safe_d = 100.0; label_d = "$100 美金"
        elif "白銀" in risk_asset: 
            c_size = 5000; safe_d = 4.0; label_d = "$4 美金"
        elif "道瓊" in risk_asset: 
            c_size = 5; safe_d = 1000.0; label_d = "1000 點"
        elif "英鎊" in risk_asset: 
            c_size = 100000; safe_d = 0.0200; label_d = "0.0200 (200點)"
        elif "日圓" in risk_asset: 
            c_size = 100000; safe_d = 2.00; label_d = "2.00 (200點)"
        
        if "日圓" in risk_asset and px > 0:
             safe_l = (bal * 0.9 * px) / (c_size * safe_d)
        else:
             safe_l = (bal * 0.9) / (c_size * safe_d)
             
        safe_l = max(0.01, safe_l)
        
        st.markdown(f"**🛡️ 建議手數:** `{safe_l:.2f} 手` (可扛: {label_d})")

    st.subheader("🕵️ 戰術矩陣輸入 (分流)")
    for s_name, s_code in SYMBOLS.items():
        # [優化] 使用兩欄佈局，將 M5/M15 並排，並使用 Selectbox 節省空間
        with st.expander(f"{s_name} 設定", expanded=False):
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
                "M5": {"signal": s5, "cvd": c5},
                "M15": {"signal": s15, "cvd": c15}
            }

    st.divider()
    auto = st.checkbox("自動刷新", value=False)
    rate = st.slider("秒數", 30, 300, 60)
    sound = st.checkbox("音效警報", value=True)
    
    if st.button("🚀 刷新戰場數據", type="primary"): st.rerun()

# [核心分析邏輯]
def analyze(name, ticker, df, h1_trend, user_balance, tf_key):
    try:
        df = df.dropna()
        if len(df) < 50: return None
        
        close = df['Close']; high = df['High']; low = df['Low']
        ema20 = ta.ema(close, length=20).iloc[-1]
        ema60 = ta.ema(close, length=60).iloc[-1]
        ema240 = ta.ema(close, length=240).iloc[-1]
        atr = ta.atr(high, low, close, length=14).iloc[-1]
        price = close.iloc[-1]
        
        if pd.isna(atr) or atr <= 0: atr = 0.5 
        
        # 波動率
        vol_status = "🔥 活躍"; vol_safe = True
        atr_limit = 1.0 if "黃金" in name else (0.05 if "白銀" in name else (20 if "道瓊" in name else 0.05))
        if atr < atr_limit: 
            vol_status = "🩸 死魚"; vol_safe = False
            
        mtf_bonus = 10 if "多頭" in h1_trend else (-10 if "空頭" in h1_trend else 0)

        # 手數
        contract_size = 5000 if "白銀" in name else (5 if "道瓊" in name else (100000 if "英鎊" in name or "日圓" in name else 100))
        survival_dist = 4.0 if "白銀" in name else (1000.0 if "道瓊" in name else (0.02 if "英鎊" in name else 100.0))
        safe_lots = max(0.01, round(user_balance / (contract_size * (survival_dist + price/200)), 2))
        
        # 讀取輸入
        all_inputs = st.session_state.manual_inputs.get(ticker, {})
        tf_inputs = all_inputs.get(tf_key, {"signal": "無", "cvd": "一般"})
        u_sig, u_cvd = tf_inputs['signal'], tf_inputs['cvd']
        
        manual_display = "-"
        if u_sig != "無" or u_cvd != "一般":
            manual_display = f"{u_sig} | {u_cvd}"
        
        action = "WAIT"; score = 0
        sl = 0.0; tp = 0.0
        
        sl_long = price - (1.5 * atr); tp_long = price + (2.5 * atr)
        sl_short = price + (1.5 * atr); tp_short = price - (2.5 * atr)

        if vol_safe == False:
            action = "🚫 波動不足"; score = 10
            sl = sl_long; tp = tp_long
        else:
            if "黃標" in u_sig:
                if "強賣" in u_cvd or "誘多" in u_cvd: 
                    action, score = "🛑 假訊號 (CVD賣壓)", 0 
                elif "吸收" in u_cvd or "強買" in u_cvd:
                    score = 95 + mtf_bonus; action = "🚀 FIRE (做多)" 
                else:
                    score = 75 + mtf_bonus; action = "⚡ 嘗試做多"
                sl = sl_long; tp = tp_long
                
            elif "紫標" in u_sig:
                if "強買" in u_cvd or "吸收" in u_cvd: 
                    action, score = "🛑 假訊號 (CVD軋空)", 0 
                elif "誘多" in u_cvd or "強賣" in u_cvd:
                    score = 95 - mtf_bonus; action = "🪓 FIRE (做空)" 
                else:
                    score = 75 - mtf_bonus; action = "⚡ 嘗試做空"
                sl = sl_short; tp = tp_short
                
            else: # 無訊號
                diff = (price - ema20) / atr
                if price > ema60 and price < ema20: 
                    action = "👀 關注 (找黃標)"; score = 60 + mtf_bonus; sl = sl_long; tp = tp_long
                elif diff > 2.5: 
                    action = "⚠️ 過熱 (找紫標)"; score = 70 - mtf_bonus; sl = sl_short; tp = tp_short
                elif diff < -2.5: 
                    action = "⚠️ 超跌 (找黃標)"; score = 70 + mtf_bonus; sl = sl_long; tp = tp_long
                else: 
                    action = "💤 盤整"; score = 20; sl = sl_long; tp = tp_long

        score = max(0, min(100, score))

        return {
            "商品": name, "波動": vol_status, "現價": price, 
            "手動訊號": manual_display,
            "AI 建議": action, 
            "止損 (SL)": f"{sl:.2f}", 
            "止盈 (TP)": f"{tp:.2f}",
            "建議手數": f"{safe_lots} 手", "預估勝率": score,
            "history": close.tail(40).tolist()
        }
    except Exception as e: return None

# [主畫面佈局：左右分欄]
col_main, col_info = st.columns([0.65, 0.35])

with col_main:
    st.title("🧿 Blade God V13.2 指揮官")
    st.caption(f"GitHub 託管版 | M5/M15 分流 + CVD 橫向展開")

with col_info:
    # [修正] CVD 戰術圖解：無 Expander，直接橫向排列
    st.markdown("""
    <div style="display: flex; gap: 5px; margin-top: 10px;">
        <div class="cvd-box">
            <div class="cvd-title">📉 吸收 (做多)</div>
            <div class="bar-container">
                <div class="bar bar-red" style="height: 100%;"></div>
                <div class="bar bar-red" style="height: 60%;"></div>
                <div class="bar bar-green" style="height: 15%;"></div>
            </div>
            <div class="cvd-desc">跌+紅縮<br>主力接貨</div>
        </div>

        <div class="cvd-box">
            <div class="cvd-title">📈 誘多 (做空)</div>
            <div class="bar-container">
                <div class="bar bar-green" style="height: 100%;"></div>
                <div class="bar bar-green" style="height: 60%;"></div>
                <div class="bar bar-red" style="height: 15%;"></div>
            </div>
            <div class="cvd-desc">漲+綠縮<br>主力出貨</div>
        </div>
        
        <div class="cvd-box">
            <div class="cvd-title">🚀 強勢順勢</div>
            <div class="bar-container">
                <div class="bar bar-green" style="height: 40%;"></div>
                <div class="bar bar-green" style="height: 70%;"></div>
                <div class="bar bar-green" style="height: 100%;"></div>
            </div>
            <div class="cvd-desc">量價齊揚<br>順勢追單</div>
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
                df_res[["商品", "波動", "現價", "手動訊號", "AI 建議", "止損 (SL)", "止盈 (TP)", "建議手數", "預估勝率"]],
                use_container_width=True, hide_index=True,
                column_config={
                    "預估勝率": st.column_config.ProgressColumn("勝率 %", format="%d%%", min_value=0, max_value=100),
                    "手動訊號": st.column_config.TextColumn("戰術回饋", width="medium"),
                    "AI 建議": st.column_config.TextColumn("戰術指令", validate="^.*$"),
                    "止損 (SL)": st.column_config.TextColumn("止損", help="ATR 1.5倍"),
                    "止盈 (TP)": st.column_config.TextColumn("止盈", help="ATR 2.5倍")
                }
            )
            
            # [修正] 移除圖表，改為純文字重點提示 (因為Yahoo圖表數據不穩)
            high_conf_items = df_res[df_res['預估勝率'] >= 70].sort_values(by="預估勝率", ascending=False)
            if not high_conf_items.empty:
                st.markdown(f"#### 🔥 {t_name} 焦點戰場")
                for idx, row in high_conf_items.iterrows():
                    st.success(f"**{row['商品']}** | 勝率: **{row['預估勝率']}%** | 👉 操作: **{row['AI 建議']}** | 手數: **{row['建議手數']}** | 止損: **{row['止損 (SL)']}**")

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
