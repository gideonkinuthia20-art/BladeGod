import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta
import time
from datetime import datetime, timedelta

# [系統設定]
st.set_page_config(page_title="Blade God V11.9 指揮官", page_icon="⚔️", layout="wide")

# [樣式優化 - 高對比亮色主題]
st.markdown("""
<style>
    /* 全局字體優化 */
    html, body, [class*="css"] { font-family: 'Microsoft JhengHei', sans-serif; color: #000000; }
    
    /* 表格文字放大 */
    .stDataFrame { font-size: 1.15rem !important; }
    
    /* 側邊欄優化 */
    section[data-testid="stSidebar"] { width: 380px !important; background-color: #f8f9fa; }
    
    /* 摺疊選單 */
    .stExpander { 
        border: 1px solid #d1d1d1; 
        background-color: #ffffff; 
        border-radius: 8px; 
        box-shadow: 0 2px 5px rgba(0,0,0,0.05);
        margin-bottom: 10px;
    }
    .stExpander p { color: #000000 !important; font-weight: bold; }
    
    /* 輸入框優化 */
    .stNumberInput input { background-color: #ffffff; color: #000000; font-weight: bold; border: 1px solid #ccc; }
    
    /* 狀態顏色 */
    .vol-high { color: #007020; font-weight: 900; } 
    .vol-low { color: #666666; font-style: italic; } 
    
    /* 警報框 */
    .alert-box { 
        padding: 15px; 
        border-radius: 8px; 
        margin-bottom: 15px; 
        text-align: center; 
        font-size: 1.2rem;
        font-weight: bold;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    .alert-high { 
        background-color: #e6fffa; 
        border: 2px solid #2ea043; 
        color: #004d1a; 
    }
</style>
""", unsafe_allow_html=True)

# [全域變數]
if 'manual_inputs' not in st.session_state: st.session_state.manual_inputs = {}

# [標的清單]
SYMBOLS = {
    "🥇 黃金 (Gold)": "XAUUSD=X",
    "🥈 白銀 (Silver)": "XAGUSD=X",
    "🇺🇸 道瓊 (US30)": "YM=F",
    "💷 英鎊 (GBP)": "GBPUSD=X"
}

# [輔助函數]
def get_tw_time():
    # Streamlit Cloud 預設是 UTC，需加 8 小時
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
                # 處理 yfinance 下載單一 vs 多個商品的結構差異
                if len(tickers) > 1:
                    df = data[s_code]
                else:
                    df = data
                
                df = df.dropna()
                if df.empty: continue
                
                close = df['Close']
                ema20 = ta.ema(close, length=20).iloc[-1]
                price = close.iloc[-1]
                
                if price > ema20:
                    trends[s_code] = "🐂 多頭"
                else:
                    trends[s_code] = "🐻 空頭"
            except: 
                trends[s_code] = "⚪ 未知"
        return trends
    except: return {}

# [側邊欄]
with st.sidebar:
    st.title("⚔️ 指揮官 V11.9")
    st.caption(f"系統時間: {get_tw_time()} | GitHub 託管版")
    
    with st.expander("💰 風控計算機 (Risk Calc)", expanded=True):
        st.markdown("### 資產設定")
        mode = st.radio("選擇商品:", ["黃金(100oz)", "白銀(5000oz)"], horizontal=True, key="rm")
        bal = st.number_input("本金 (USD):", value=1000, step=100, key="rb")
        px = st.number_input("現價:", value=5015.0, key="rp")
        
        size = 5000 if "白銀" in mode else 100
        safe_d = 4.0 if "白銀" in mode else 100.0
        aggro_d = 2.5 if "白銀" in mode else 80.0
        
        safe_l = bal / (size * (safe_d + px/200))
        aggro_l = bal / (size * (aggro_d + px/200))
        
        # 修正後的 f-string，確保換行符號正確
        st.info(f"🛡️ 保守: **{safe_l:.2f} 手**\n\n⚔️ 激進: **{aggro_l:.2f} 手**")

    st.subheader("🕵️ 手動矩陣")
    for s_name, s_code in SYMBOLS.items():
        with st.expander(f"{s_name} 設定", expanded=False):
            s = st.radio("訊號", ["無", "黃標", "紫標"], key=f"s_{s_code}", horizontal=True)
            c = st.radio("CVD", ["一般", "強買", "強賣", "吸收", "誘多"], key=f"c_{s_code}")
            st.session_state.manual_inputs[s_code] = {"signal": s, "cvd": c}

    st.divider()
    auto = st.checkbox("自動刷新", value=False)
    # GitHub 版建議刷新頻率不要太高
    rate = st.slider("秒數", 60, 300, 60)
    sound = st.checkbox("音效警報 (Beep)", value=False) 
    
    if st.button("🚀 執行掃描", type="primary"): st.rerun()

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
        
        # ADX 計算修正
        adx_df = ta.adx(high, low, close, length=14)
        if adx_df is not None and not adx_df.empty:
            adx = adx_df['ADX_14'].iloc[-1]
        else:
            adx = 0
            
        price = close.iloc[-1]
        diff_blue = price - ema20
        diff_atr = diff_blue / atr if atr > 0 else 0
        
        u_data = st.session_state.manual_inputs.get(ticker, {"signal": "無", "cvd": "一般"})
        u_sig, u_cvd = u_data['signal'], u_data['cvd']
        
        action = "WAIT"; score = 0; sl = 0.0
        
        # 波動率狀態
        vol_status = "🔥 活躍"; vol_safe = True
        if "黃金" in name and atr < 1.5: vol_status = "💤 死魚"; vol_safe = False
        elif "白銀" in name and atr < 0.05: vol_status = "💤 死魚"; vol_safe = False
        elif "道瓊" in name and atr < 20: vol_status = "💤 死魚"; vol_safe = False
            
        mtf_bonus = 10 if "多頭" in h1_trend else (-10 if "空頭" in h1_trend else 0)

        contract_size = 5000 if "白銀" in name or "Silver" in name else (5 if "道瓊" in name else 100)
        survival_dist = 4.0 if "白銀" in name or "Silver" in name else 100.0
        if "激進" in mode_pref: survival_dist *= 0.8
        
        safe_lots = max(0.01, round(user_balance / (contract_size * (survival_dist + price/200)), 2))
        
        if vol_safe == False:
            action = "🚫 波動不足"; score = 10
        else:
            if "黃標" in u_sig:
                if "強賣" in u_cvd: action, score = "🛑 假訊號", 0
                elif "吸收" in u_cvd or "強買" in u_cvd:
                    score = 95 + mtf_bonus; action = "🚀 FIRE (做多)"; sl = price - (1.5 * atr)
                else:
                    score = 80 + mtf_bonus; action = "⚡ 嘗試做多"; sl = price - (1.0 * atr)
            elif "紫標" in u_sig:
                if "強買" in u_cvd: action, score = "🛑 假訊號", 0
                elif "誘多" in u_cvd or "強賣" in u_cvd:
                    score = 95 - mtf_bonus; action = "🪓 FIRE (做空)"; sl = price + (1.5 * atr)
                else:
                    score = 80 - mtf_bonus; action = "⚡ 嘗試做空"; sl = price + (1.0 * atr)
            else:
                if price > ema60 and price < ema20: action = "👀 關注 (找黃標)"; score = 60 + mtf_bonus
                elif diff_atr > 2.5: action = "⚠️ 過熱 (找紫標)"; score = 70 - mtf_bonus
                elif diff_atr < -2.5: action = "⚠️ 超跌 (找黃標)"; score = 70 + mtf_bonus
                elif adx > 25: action = "🌊 順勢持有"; score = 50
                else: action = "💤 盤整"; score = 20

        score = max(0, min(100, score))

        return {
            "商品": name, "波動率": vol_status, "現價": price, 
            "AI 建議": action, "止損 (SL)": f"{sl:.2f}" if sl else "-", 
            "建議手數": f"{safe_lots} 手", "預估勝率": score,
            "history": close.tail(40).tolist()
        }
    except: return None

# [主畫面]
st.title("🧿 Blade God V11.9 指揮官")
st.caption(f"資料來源: Yahoo Finance | 部署於 Streamlit Cloud")

high_alert = False
tickers = list(SYMBOLS.values())
scan_tfs = {"⚡ M5 (極速)": "5m", "⚔️ M15 (標準)": "15m"}

for t_name, t_code in scan_tfs.items():
    st.subheader(f"{t_name} 戰場")
    try:
        data = yf.download(tickers, period="5d", interval=t_code, group_by='ticker', progress=False)
        tasks = []
        for s_name, s_code in SYMBOLS.items():
            try:
                # 處理 yfinance 結構
                if len(tickers) > 1:
                    df = data[s_code]
                else:
                    df = data
                
                trend_ctx = get_h1_trend().get(s_code, "⚪ 未知")
                res = analyze(s_name, s_code, df, trend_ctx, st.session_state.get('rb', 1000), st.session_state.get('rm', "保守"))
                if res: 
                    tasks.append(res)
                    if res['預估勝率'] >= 85: high_alert = True
            except: continue
            
        if tasks:
            df_res = pd.DataFrame(tasks).sort_values(by="預估勝率", ascending=False)
            st.dataframe(
                df_res[["商品", "波動率", "現價", "AI 建議", "止損 (SL)", "建議手數", "預估勝率"]],
                use_container_width=True, hide_index=True,
                column_config={
                    "預估勝率": st.column_config.ProgressColumn("預估勝率 %", format="%d%%", min_value=0, max_value=100),
                    "建議手數": st.column_config.TextColumn("建議手數"),
                    "AI 建議": st.column_config.TextColumn("戰術指令", validate="^.*$"),
                    "波動率": st.column_config.TextColumn("波動")
                }
            )
            best = df_res.iloc[0]
            if best['預估勝率'] >= 70:
                with st.expander(f"🔥 焦點: {best['商品']} (勝率: {best['預估勝率']}%)", expanded=True):
                    st.line_chart(best['history'], height=150)
                    if best['預估勝率'] >= 90: st.markdown(f"<div class='alert-box alert-high'>🚨 完美共振：勝率 {best['預估勝率']}% | 下單 {best['建議手數']} | {best['AI 建議']}</div>", unsafe_allow_html=True)
    except Exception as e: st.error(str(e))

if high_alert and sound:
    st.markdown("""<audio autoplay><source src="https://assets.mixkit.co/active_storage/sfx/2869/2869-preview.mp3" type="audio/mp3"></audio>""", unsafe_allow_html=True)
    st.toast("🚨 偵測到高勝率訊號！", icon="🔥")

if auto:
    time.sleep(rate)
    st.rerun()
