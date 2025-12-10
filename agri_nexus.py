import streamlit as st
import pandas as pd

# --- 1. 物理常數與規則庫 (The Physics Layer) ---

# 作物規格書
CROPS_SPECS = {
    "水蜜桃 (Peach)": {
        "priority": "High (最高)",
        "leaf_fruit_ratio": 45,
        "spacing_rule": "長果枝留2，中果枝留1，短果枝留0",
        "note": "高耗能單位，嚴禁朝天果與貼枝果"
    },
    "甜柿 (Persimmon)": {
        "priority": "Mid (中等)",
        "leaf_fruit_ratio": 25,
        "spacing_rule": "枝條基部留1顆，極壯枝留2顆 (間距>15cm)",
        "note": "需光量大，優先保留內膛受光果"
    },
    "蜜李 (Plum)": {
        "priority": "Low (基礎)",
        "leaf_fruit_ratio": 12,
        "spacing_rule": "指距法：兩果之間需容納三指寬",
        "note": "嚴禁成串，必須拆解"
    }
}

# 營養配方庫
FORMULAS = {
    "甜蜜三角": {
        "components": [
            {"name": "海藻精", "ratio": 1000, "desc": "提升光合效率，抗逆境"},
            {"name": "高鉀液肥/糖蜜", "ratio": 500, "desc": "轉糖關鍵，搬運工"},
            {"name": "鈣硼液", "ratio": 800, "desc": "細胞壁強化，防裂果"}
        ],
        "condition": "無雨的早晨或傍晚",
        "target": "全園噴施"
    }
}

# --- 2. 運算函數 (Computational Functions) ---

def calculate_mix(water_amount):
    """計算藥桶配藥量"""
    recipe = []
    for item in FORMULAS["甜蜜三角"]["components"]:
        amount_ml = water_amount * 1000 / item["ratio"]
        recipe.append({
            "資材名稱": item["name"],
            "稀釋倍數": item["ratio"],
            "需加入量 (ml/g)": round(amount_ml, 1),
            "功能": item["desc"]
        })
    return pd.DataFrame(recipe)

# --- 3. APP 介面層 (UI Layer) ---

st.set_page_config(page_title="AgriNexus: Lishan", page_icon="🍎", layout="wide")

# [左側] 側邊欄：導航與設定
with st.sidebar:
    st.title("🧬 AgriNexus")
    st.caption("v5.2 (Sidebar)")
    st.divider()
    
    # 核心改動：將分頁變成左側的單選按鈕
    st.header("功能選單")
    page = st.radio(
        "前往功能：",
        ["📋 今日戰術", "🧪 配藥計算機", "📚 規格查詢"]
    )
    
    st.divider()
    
    # 環境參數也保留在左側下方
    st.header("📡 環境參數")
    weather = st.radio("今日天氣", ["晴朗/多雲", "陰天/起霧", "雨天"])
    workers = st.slider("今日上工人數", 1, 4, 4)
    water_tank = st.number_input("藥桶容量 (公升)", value=200, step=50)

# [右側] 主畫面：根據左側選擇顯示不同內容

# --- 頁面 1: 今日戰術 ---
if page == "📋 今日戰術":
    st.title("📋 今日戰術看板")
    st.markdown("---")
    
    st.header("優先級任務 (Priority Queue)")
    
    if "雨" in weather:
        st.error("⚠️ 警告：檢測到降雨風險。")
        st.markdown("**⛔ 停止噴施作業** (避免無效投入)。")
        st.markdown("**✅ 全力轉向：** 1. 疏果 (優先度最高) 2. 枝條加固 (防風) 3. 排水檢查")
    else:
        st.success("🌤️ 天候許可。執行標準 SOP。")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.info(f"**08:00 - 14:00 (75%)**\n\n全力疏果\n(Peach > Persimmon)")
        with col2:
            st.info(f"**14:00 - 15:00 (12%)**\n\n南瓜邊界管理\n& 枝條整理")
        with col3:
            st.info(f"**15:00 - 16:30 (13%)**\n\n噴施作業\n(甜蜜三角)")

    st.markdown("### ⚔️ 重點執行檢查")
    st.checkbox("🍑 水蜜桃：確認已移除所有「朝天果」與「貼枝果」")
    st.checkbox("🍒 蜜李：確認已拆解所有「成串」果實")
    st.checkbox("🎃 南瓜：確認藤蔓未攀爬至果樹上")

# --- 頁面 2: 配藥計算機 ---
elif page == "🧪 配藥計算機":
    st.title("🧪 甜蜜三角配方計算")
    st.markdown("---")
    
    st.info(f"當前設定藥桶容量：**{water_tank} 公升** (可於左側選單調整)")
    
    if st.button("計算投放量 (Calculate)"):
        df = calculate_mix(water_tank)
        st.table(df)
        st.warning("⚠️ 注意：請先用小桶溶解後再倒入大桶。順序：鈣硼 -> 鉀肥 -> 海藻精。")
    else:
        st.write("👈 請點擊按鈕開始計算")

# --- 頁面 3: 規格查詢 ---
elif page == "📚 規格查詢":
    st.title("📚 疏果標準規格書")
    st.markdown("---")
    
    crop_select = st.selectbox("選擇作物", list(CROPS_SPECS.keys()))
    spec = CROPS_SPECS[crop_select]
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric("🍃 葉果比 (Leaf/Fruit)", f"{spec['leaf_fruit_ratio']} : 1")
    with col2:
        st.metric("⚡ 優先級", spec['priority'])
        
    st.success(f"**✂️ 執行口訣：** {spec['spacing_rule']}")
    st.markdown(f"**📝 備註：** {spec['note']}")