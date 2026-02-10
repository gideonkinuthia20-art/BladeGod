import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta
import time
from datetime import datetime, timedelta

# [系統設定]
st.set_page_config(page_title="Blade God V12.7 指揮官", page_icon="⚔️", layout="wide")

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
    section[data-testid="stSidebar"] { width: 420px !important; background-color: #f0f2f6; }
    
    /* CVD 視覺化圖塊 */
    .cvd-box {
        padding: 10px; border-radius: 5px; margin-bottom: 8px;
        background-color: #ffffff; border: 1px solid #ccc;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    }
    .bar-container { display: flex; align-items: flex-end; height: 40px; gap: 4px; margin-top: 5px; padding-bottom: 5px; border-bottom: 1px dashed #eee;}
    .bar { width: 12px; border-radius: 2px; }
    .bar-green { background-color: #2ea043; }
    .bar-red { background-color: #da3633; }
    .cvd-title { font-weight: bold; font-size: 1rem; color: #333; }
    .cvd-desc { font-size: 0.85rem; color: #555; margin-top: 5px; line-height: 1.4; }
    
    /* 警報框 */
    .alert-box { 
        padding: 15px; border-radius: 8px; margin-bottom: 15px; 
        text-align: center; font-size: 1.2rem; font-weight: bold;
        background-color: #e6fffa; border: 2px solid #2ea043; color: #004d1a;
        box-shadow: 0 4px 10px rgba(0,0,0,0.1);
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

# [時間週期 - H1 已移除]
TIMEFRAMES = {"⚡ M5": "5m", "⚔️ M15": "15m"}

# [輔助函數]
def get_tw_time():
    return (datetime.utcnow() + timedelta(hours=8)).strftime('%H:%M:%S')

# [核心：MTF 趨勢掃描 (背景運算用)]
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

# [側邊欄]
with st.sidebar:
    st.title("⚔️ 指揮官 V12.7")
    st.caption(f"系統時間: {get_tw_time()} | 全資產風控修正版")
    
    # --- 1. CVD 視覺圖解 ---
    with st.expander("📊 CVD 戰術圖解 (Visual Guide)", expanded=False):
        st.markdown("""
        <div class="cvd-box">
            <div class="cvd-title">📉 吸收 (Absorption) = 做多</div>
            <div class="bar-container">
                <div class="bar bar-red" style="height: 100%;"></div>
                <div class="bar bar-red" style="height: 60%;"></div>
                <div class="bar bar-red" style="height: 30%;"></div>
                <div class="bar bar-green" style="height: 15%;"></div>
            </div>
            <div class="cvd-desc"><b>現象：價格跌，但紅柱變短。</b><br>主力掛單接貨，賣壓衰竭。<br>👉 配合 🟨 黃標使用。</div>
        </div>

        <div class="cvd-box">
            <div class="cvd-title">📈 誘多 (Trap) = 做空</div>
            <div class="bar-container">
                <div class="bar bar-green" style="height: 100%;"></div>
                <div class="bar bar-green" style="height: 60%;"></div>
                <div class="bar bar-green" style="height: 30%;"></div>
                <div class="bar bar-red" style="height: 15%;"></div>
            </div>
            <div class="cvd-desc"><b>現象：價格漲，但綠柱變短。</b><br>主力偷偷出貨，買盤力竭。<br>👉 配合 🟪 紫標使用。</div>
        </div>
        
        <div class="cvd-box">
            <div class="cvd-title">🟢/🔴 強買強賣</div>
            <div class="cvd-desc">柱體與 K 棒同色且變長，代表趨勢強勁，可順勢追單。</div>
        </div>
        """, unsafe_allow_html=True)

    # --- 2. 全資產風控計算機 (修正回歸) ---
    with st.expander("💰 風控計算機 (全資產)", expanded=True):
        asset_type = st.selectbox(
            "選擇商品類別:", 
            [
                "🥇 黃金 (100oz)", 
                "🥈 白銀 (5000oz)", 
                "🇺🇸 道瓊 (每點$5)", 
                "💷 英鎊 (10萬單位)",
                "🇯🇵 日圓 (10萬單位)"
            ]
        )
        bal = st.number_input("本金 (USD):", value=1000, step=100, key="rb")
        
        # 預設參考價格 (若無實時數據時使用)
        def_prices = {
            "黃金": 2600.0, "白銀": 30.0, "道瓊": 44000.0, 
            "英鎊": 1.2500, "日圓": 150.0
        }
        ref_price = 0.0
        for k, v in def_prices.items():
            if k in asset_type: ref_price = v
            
        px = st.number_input("參考現價:", value=ref_price, format="%.4f")
        
        # 參數設定
        if "黃金" in asset_type:
            c_size = 100; safe_d = 100.0 # 扛100鎂
        elif "白銀" in asset_type:
            c_size = 5000; safe_d = 4.0  # 扛4鎂
        elif "道瓊" in asset_type:
            c_size = 5; safe_d = 1000.0  # 扛1000點
        elif "英鎊" in asset_type:
            c_size = 100000; safe_d = 0.0200 # 扛200點 (0.0200)
        elif "日圓" in asset_type:
            c_size = 100000; safe_d = 2.00 # 扛200點 (2.00日圓)
        
        # 計算邏輯
        leverage = 200
        if "日圓" in asset_type and px > 0:
            # 日圓特殊計算 (除以匯率轉回USD)
            risk_usd_per_lot = (c_size * safe_d) / px
            safe_l = (bal * 0.9) / risk_usd_per_lot
        else:
            # 一般計算 (直盤與CFD)
            safe_l = (bal * 0.9) / (c_size * safe_d)
            
        safe_l = max(0.01, safe_l)
        
        st.markdown(f"""
        **🛡️ 建議手數:** `{safe_l:.2f} 手`
        \n(設定生存波動: {safe_d})
        """)

    # --- 3. 戰術矩陣 ---
    st.subheader("🕵️ CVD 戰術輸入")
    for s_name, s_code in SYMBOLS.items():
        with st.expander(f"{s_name} 設定", expanded=False):
            s = st.radio("訊號", ["無", "黃標", "紫標"], key=f"s_{s_code}", horizontal=True)
            c = st.radio("CVD", ["一般", "強買", "強賣", "吸收(做多)", "誘多(做空)"], key=f"c_{s_code}")
            st.session_state.manual_inputs[s_code] = {"signal": s, "cvd": c}

    st.divider()
    auto = st.checkbox("自動刷新", value=False)
    rate = st.slider("秒數", 30, 300, 60)
    sound = st.checkbox("音效警報", value=True)
    
    if st.button("🚀 刷新戰場數據", type="primary"): st.rerun()

# [核心分析邏輯]
def analyze(name, ticker, df, h1_trend, user_balance, mode_pref):
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
        
        # 波動率狀態
        vol_status = "🔥 活躍"; vol_safe = True
        atr_limit = 1.0 if "黃金" in name else (0.05 if "白銀" in name else (20 if "道瓊" in name else 0.05))
        if atr < atr_limit: 
            vol_status = "🩸 死魚"; vol_safe = False
            
        mtf_bonus = 10 if "多頭" in h1_trend else (-10 if "空頭" in h1_trend else 0)

        # 自動手數 (表格內即時計算)
        contract_size = 100; survival_dist = 100.0
        
        if "白銀" in name:
            contract_size = 5000; survival_dist = 4.0 
        elif "黃金" in name:
            contract_size = 100; survival_dist = 100.0
        elif "道瓊" in name:
            contract_size = 5; survival_dist = 1000.0
        elif "英鎊" in name:
            contract_size = 100000; survival_dist = 0.0200
        elif "日圓" in name:
            contract_size = 100000; survival_dist = 2.00
            
        # 安全手數計算
        if "日圓" in name:
             risk_per_lot = (contract_size * survival_dist) / price
             safe_lots = (user_balance * 0.9) / risk_per_lot
        else:
             safe_lots = (user_balance * 0.9) / (contract_size * survival_dist)
             
        safe_lots = max(0.01, round(safe_lots, 2))
        
        u_data = st.session_state.manual_inputs.get(ticker, {"signal": "無", "cvd": "一般"})
        u_sig, u_cvd = u_data['signal'], u_data['cvd']
        
        action = "WAIT"; score = 0
        
        sl_long = price - (1.5 * atr); tp_long = price + (2.5 * atr)
        sl_short = price + (1.5 * atr); tp_short = price - (2.5 * atr)
        
        final_sl = 0.0; final_tp = 0.0

        if vol_safe == False:
            action = "🚫 波動不足"; score = 10
            final_sl = sl_long; final_tp = tp_long
        else:
            if "黃標" in u_sig:
                if "強賣" in u_cvd: action, score = "🛑 假訊號", 0
                elif "吸收" in u_cvd or "強買" in u_cvd:
                    score = 95 + mtf_bonus; action = "🚀 FIRE (做多)"
                else:
                    score = 80 + mtf_bonus; action = "⚡ 嘗試做多"
                final_sl = sl_long; final_tp = tp_long
            elif "紫標" in u_sig:
                if "強買" in u_cvd: action, score = "🛑 假訊號", 0
                elif "誘多" in u_cvd or "強賣" in u_cvd:
                    score = 95 - mtf_bonus; action = "🪓 FIRE (做空)"
                else:
                    score = 80 - mtf_bonus; action = "⚡ 嘗試做空"
                final_sl = sl_short; final_tp = tp_short
            else:
                diff = (price - ema20) / atr
                if price > ema60 and price < ema20: 
                    action = "👀 關注 (找黃標)"; score = 60 + mtf_bonus; final_sl = sl_long; final_tp = tp_long
                elif diff > 2.5: 
                    action = "⚠️ 過熱 (找紫標)"; score = 70 - mtf_bonus; final_sl = sl_short; final_tp = tp_short
                elif diff < -2.5: 
                    action = "⚠️ 超跌 (找黃標)"; score = 70 + mtf_bonus; final_sl = sl_long; final_tp = tp_long
                else: 
                    action = "💤 盤整"; score = 20; final_sl = sl_long; final_tp = tp_long

        score = max(0, min(100, score))

        return {
            "商品": name, "波動": vol_status, "現價": price, 
            "AI 建議": action, 
            "止損 (SL)": f"{final_sl:.2f}", 
            "止盈 (TP)": f"{final_tp:.2f}",
            "建議手數": f"{safe_lots} 手", "預估勝率": score,
            "history": close.tail(40).tolist()
        }
    except Exception as e: return None

# [主畫面]
st.title("🧿 Blade God V12.7 指揮官")
st.caption(f"GitHub 託管版 | 全資產風控修正")

sound_placeholder = st.empty()
tickers = list(SYMBOLS.values())
high_alert = False

for t_name, t_code in TIMEFRAMES.items():
    st.subheader(f"{t_name} 戰場")
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
                res = analyze(s_name, s_code, df, trend_ctx, st.session_state.get('rb', 1000), "保守")
                if res: 
                    tasks.append(res)
                    seen_tickers.add(s_code)
                    if res['預估勝率'] >= 85: high_alert = True
            except: continue
            
        if tasks:
            df_res = pd.DataFrame(tasks)
            st.dataframe(
                df_res[["商品", "波動", "現價", "AI 建議", "止損 (SL)", "止盈 (TP)", "建議手數", "預估勝率"]],
                use_container_width=True, hide_index=True,
                column_config={
                    "預估勝率": st.column_config.ProgressColumn("勝率 %", format="%d%%", min_value=0, max_value=100),
                    "AI 建議": st.column_config.TextColumn("戰術指令", validate="^.*$"),
                    "止損 (SL)": st.column_config.TextColumn("止損", help="ATR 1.5倍"),
                    "止盈 (TP)": st.column_config.TextColumn("止盈", help="ATR 2.5倍")
                }
            )
            
            best = df_res.sort_values(by="預估勝率", ascending=False).iloc[0]
            if best['預估勝率'] >= 70:
                with st.expander(f"🔥 {best['商品']} 趨勢圖 (勝率: {best['預估勝率']}%)", expanded=True):
                    st.line_chart(best['history'], height=150)
                    st.success(f"建議操作：{best['AI 建議']} | 手數：{best['建議手數']} | 止損：{best['止損 (SL)']}")

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
