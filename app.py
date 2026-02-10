import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta
import time
from datetime import datetime, timedelta

# [系統設定]
st.set_page_config(page_title="Blade God V12.3 指揮官", page_icon="⚔️", layout="wide")

# [樣式優化]
st.markdown("""
<style>
    /* 全局字體 */
    html, body, [class*="css"], .stDataFrame { font-family: 'Microsoft JhengHei', sans-serif; color: #000000 !important; }
    .stDataFrame { font-size: 1.1rem !important; }
    
    /* 狀態顏色 */
    .vol-high { color: #007020 !important; font-weight: 900; } 
    .vol-low { color: #8B0000 !important; font-weight: 900; } 
    
    /* 側邊欄 */
    section[data-testid="stSidebar"] { width: 400px !important; background-color: #f0f2f6; }
    
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

TIMEFRAMES = {"⚡ M5": "5m", "⚔️ M15": "15m", "🌊 H1": "60m"}

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
                # 處理 yfinance 多重/單一結構
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
    st.title("⚔️ 指揮官 V12.3")
    st.caption(f"系統時間: {get_tw_time()} | 終極穩定版")
    
    # CVD 說明
    with st.expander("📖 CVD 戰術定義", expanded=False):
        st.info("📉 吸收 = 價格跌 + 紅柱縮短 (做多)\n\n📈 誘多 = 價格漲 + 綠柱縮短 (做空)")

    # 風控
    with st.expander("💰 風控計算機", expanded=True):
        mode = st.radio("資產:", ["黃金(100oz)", "白銀(5000oz)"], horizontal=True, key="rm")
        bal = st.number_input("本金 (USD):", value=1000, step=100, key="rb")
        
        size = 5000 if "白銀" in mode else 100
        safe_d = 4.0 if "白銀" in mode else 100.0
        
        # 防止除以零
        safe_l = max(0.01, (bal * 0.9) / (size * safe_d))
        
        st.markdown(f"""
        **🛡️ 保守建議:** `{safe_l:.2f} 手`
        \n(可承受 ${safe_d} 波動)
        """)

    st.subheader("🕵️ CVD 戰術輸入")
    for s_name, s_code in SYMBOLS.items():
        with st.expander(f"{s_name} 設定", expanded=False):
            s = st.radio("訊號", ["無", "黃標", "紫標"], key=f"s_{s_code}", horizontal=True)
            c = st.radio("CVD", ["一般", "強買", "強賣", "吸收(做多)", "誘多(做空)"], key=f"c_{s_code}")
            st.session_state.manual_inputs[s_code] = {"signal": s, "cvd": c}

    st.divider()
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
        
        # [關鍵修復] ATR 防呆，防止除以零導致程式變半透明卡死
        if pd.isna(atr) or atr <= 0: atr = 0.5 
        
        # 波動率狀態
        vol_status = "🔥 活躍"; vol_safe = True
        atr_limit = 1.0 if "黃金" in name else (0.05 if "白銀" in name else (20 if "道瓊" in name else 0.05))
        if atr < atr_limit: 
            vol_status = "🩸 死魚"; vol_safe = False
            
        mtf_bonus = 10 if "多頭" in h1_trend else (-10 if "空頭" in h1_trend else 0)

        # 自動手數
        contract_size = 5000 if "白銀" in name else (5 if "道瓊" in name else (100000 if "英鎊" in name or "日圓" in name else 100))
        survival_dist = 4.0 if "白銀" in name else (1000.0 if "道瓊" in name else (0.02 if "英鎊" in name else 100.0))
        safe_lots = max(0.01, round(user_balance / (contract_size * (survival_dist + price/200)), 2))
        
        u_data = st.session_state.manual_inputs.get(ticker, {"signal": "無", "cvd": "一般"})
        u_sig, u_cvd = u_data['signal'], u_data['cvd']
        
        action = "WAIT"; score = 0
        
        # 預設 SL/TP 計算 (基於 ATR)
        sl_long = price - (1.5 * atr)
        tp_long = price + (2.5 * atr)
        sl_short = price + (1.5 * atr)
        tp_short = price - (2.5 * atr)
        
        final_sl = 0.0; final_tp = 0.0

        if vol_safe == False:
            action = "🚫 波動不足"; score = 10
            final_sl = sl_long; final_tp = tp_long
        else:
            # 邏輯核心
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
                
            else: # 無訊號
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
            "建議手數": f"{safe_lots} 手", "預估勝率": score
        }
    except Exception as e:
        # 靜默處理錯誤，不讓前端當機
        return None

# [主畫面]
st.title("🧿 Blade God V12.3 指揮官")
st.caption(f"資料來源: Yahoo Finance | 穩定修復版")

# 音效播放器容器 (放在最上面，每次重新整理都清空)
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
                # 處理 yfinance 結構
                if len(tickers) > 1: df = data[s_code]
                else: df = data
                
                trend_ctx = get_h1_trend().get(s_code, "⚪ 未知")
                res = analyze(s_name, s_code, df, trend_ctx, st.session_state.get('rb', 1000), "保守")
                if res: 
                    tasks.append(res)
                    seen_tickers.add(s_code)
                    # 偵測是否觸發警報 (分數 > 85)
                    if res['預估勝率'] >= 85: high_alert = True
            except: continue
            
        if tasks:
            df_res = pd.DataFrame(tasks).sort_values(by="預估勝率", ascending=False)
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
            
            # 高分圖表展示
            best = df_res.iloc[0]
            if best['預估勝率'] >= 80:
                with st.expander(f"🔥 {best['商品']} 趨勢圖 (勝率: {best['預估勝率']}%)", expanded=True):
                    # 這裡如果需要圖表功能，需從 analyze 回傳 history，目前簡化以保穩定
                    st.success(f"建議操作：{best['AI 建議']} | 手數：{best['建議手數']}")

    except Exception as e: st.error(f"數據讀取中... ({str(e)})")

# [修復] 音效播放邏輯：強制重置容器
if high_alert:
    # 1. 先清空
    sound_placeholder.empty()
    time.sleep(0.1)
    # 2. 再寫入 HTML 音效 (加入隨機參數避免緩存)
    sound_placeholder.markdown(f"""
        <audio autoplay>
        <source src="https://assets.mixkit.co/active_storage/sfx/2869/2869-preview.mp3?t={int(time.time())}" type="audio/mp3">
        </audio>
    """, unsafe_allow_html=True)
    st.toast("🚨 偵測到高勝率訊號！", icon="🔥")

st.markdown("---")
st.caption("Blade God System V12.3 | Stability Patch")
