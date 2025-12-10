import streamlit as st
import pandas as pd

# ==========================================
# 1. 農業邏輯層 (The Logic Layer)
# ==========================================

# --- A. 作物規格書 ---
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

# --- B. 農事戰術庫 (整合營養與農藥) ---
# mix_order 物理原則: 
# 1. 粉劑/粒劑 (WP/WG) - 最難溶，先泡
# 2. 懸浮劑/水劑 (SC/SL) - 次之
# 3. 乳劑/油劑 (EC) - 最後，避免包覆其他藥劑
# 4. 展著劑 - 輔助

FARMING_SCENARIOS = {
    "1. 休眠期/清園 (Dormant)": {
        "type": "🛡️ 病蟲害防治 (Pest Control)",
        "programs": {
            "封園清洗 (全園噴灑)": {
                "desc": "清除越冬病菌與蟲卵，降低來年基數",
                "interval": "冬季修剪後執行 1 次",
                "phi": "無 (非產期)",
                "components": [
                    {"name": "石灰硫磺合劑", "ratio": 100, "mix_order": 1, "desc": "強鹼殺菌殺蟲 (單獨使用)"},
                ]
            },
            "基肥補充 (根部)": {
                "desc": "改良土壤，儲存春季萌芽能量",
                "interval": "一次性",
                "phi": "無",
                "components": [
                    {"name": "有機質肥料", "ratio": 50, "mix_order": 1, "desc": "改善土壤團粒"},
                    {"name": "苦土石灰", "ratio": 100, "mix_order": 2, "desc": "調整酸鹼值"}
                ]
            }
        }
    },
    "2. 謝花幼果期 (Young Fruit)": {
        "type": "⚔️ 混合戰術 (Mix)",
        "programs": {
            "病蟲害防護 (殺菌+殺蟲)": {
                "desc": "防治蚜蟲、薊馬、縮葉病、穿孔病",
                "interval": "每 7-10 天",
                "phi": "安全採收期：21天",
                "components": [
                    {"name": "待克利 (粉劑)", "ratio": 3000, "mix_order": 1, "desc": "殺菌：防治黑星病/炭疽"},
                    {"name": "益達胺 (水劑)", "ratio": 1500, "mix_order": 2, "desc": "殺蟲：針對蚜蟲/薊馬"},
                    {"name": "展著劑", "ratio": 3000, "mix_order": 4, "desc": "增加藥效"}
                ]
            },
            "細胞分裂營養 (葉面)": {
                "desc": "促進幼果細胞分裂，決定果實大小關鍵",
                "interval": "每 10 天",
                "phi": "無",
                "components": [
                    {"name": "海藻精", "ratio": 1000, "mix_order": 2, "desc": "天然激素刺激分裂"},
                    {"name": "速效鈣硼", "ratio": 800, "mix_order": 2, "desc": "細胞壁建構"}
                ]
            }
        }
    },
    "3. 果實膨大期 (Expansion)": {
        "type": "⚔️ 混合戰術 (Mix)",
        "programs": {
            "果實蠅與夜蛾防治": {
                "desc": "重點防治東方果實蠅與夜蛾類",
                "interval": "每 7 天 (密度高時)",
                "phi": "安全採收期：15天",
                "components": [
                    {"name": "賜諾殺 (SC)", "ratio": 2500, "mix_order": 2, "desc": "殺蟲：針對薊馬/果實蠅"},
                    {"name": "蘇力菌 (WP)", "ratio": 1000, "mix_order": 1, "desc": "生物防治：針對鱗翅目幼蟲"},
                    {"name": "甲殼素", "ratio": 800, "mix_order": 2, "desc": "防病兼抗菌"}
                ]
            },
            "轉色增甜配方 (葉面)": {
                "desc": "退氮增鉀，促進轉色與糖度積累",
                "interval": "每 7-10 天",
                "phi": "無",
                "components": [
                    {"name": "高鉀液肥", "ratio": 500, "mix_order": 2, "desc": "鉀離子運糖"},
                    {"name": "磷酸一鉀", "ratio": 800, "mix_order": 1, "desc": "控制氮素吸收 (粉劑先溶)"},
                    {"name": "微量元素", "ratio": 1500, "mix_order": 1, "desc": "光合作用輔酶"}
                ]
            }
        }
    }
}

# ==========================================
# 2. 核心運算函數
# ==========================================

def calculate_mix(water_amount, stage, program_name):
    """
    計算藥桶配藥量，並自動排序投料順序 (WP -> SC -> EC)
    """
    try:
        plan = FARMING_SCENARIOS[stage]["programs"][program_name]
        components = plan["components"]
        info = {
            "desc": plan["desc"],
            "interval": plan["interval"],
            "phi": plan["phi"]
        }
    except KeyError:
        return pd.DataFrame(), {}

    recipe = []
    # 核心排序邏輯：依照 mix_order (1.粉 -> 2.水 -> 3.油/乳 -> 4.展著)
    sorted_components = sorted(components, key=lambda x: x["mix_order"])

    step_counter = 1
    for item in sorted_components:
        amount_ml = water_amount * 1000 / item["ratio"]
        
        # 產生操作提示
        action_tip = ""
        if item["mix_order"] == 1:
            action_tip = "🔴 優先：用小桶水完全溶解粉劑"
        elif item["mix_order"] == 3:
            action_tip = "🟡 後放：乳劑/油劑 (避免乳化破壞)"
        elif item["mix_order"] == 4:
            action_tip = "🟢 最後：加入展著劑，輕攪拌"
        else:
            action_tip = "🔵 中間：液劑直接倒入"

        recipe.append({
            "投料順序": step_counter,
            "資材/農藥名稱": item["name"],
            "劑型操作": action_tip,
            "稀釋倍數": item["ratio"],
            "需加入量 (ml/g)": round(amount_ml, 1),
            "功能": item["desc"]
        })
        step_counter += 1
        
    return pd.DataFrame(recipe), info

# ==========================================
# 3. APP 介面層
# ==========================================

st.set_page_config(page_title="AgriNexus: Smart Spray", page_icon="🚜", layout="wide")

with st.sidebar:
    st.title("🚜 AgriNexus Pro")
    st.caption("v7.2 (UI Enhanced)")
    st.divider()
    
    st.header("功能導航")
    page = st.radio("選擇模式：", ["📋 今日戰術看板", "⚗️ 藥劑/營養計算", "📖 規格查詢"])
    
    st.divider()
    st.header("⚙️ 作業參數")
    water_tank = st.number_input("藥桶容量 (公升)", value=200, step=50)
    weather = st.radio("天氣狀況", ["☀️ 晴朗 (適合噴藥)", "☁️ 陰天/起霧", "🌧️ 雨天 (禁止作業)"])

# --- 頁面 1: 看板 ---
if page == "📋 今日戰術看板":
    st.title("📋 今日農事戰術看板")
    st.markdown("---")
    
    if "雨" in weather:
        st.error("⛔ **氣候警報：** 檢測到降雨。**嚴禁噴施農藥** (避免藥害與流失)。")
        st.info("✅ **建議替代工作：** 1. 疏通排水溝 2. 資材庫存盤點 3. 農機具保養")
    else:
        st.success("✅ **氣候適宜：** 可執行噴施作業。")
        st.warning("⚠️ **安全提醒：** 噴施農藥請務必穿著防護衣、戴口罩，並注意風向。")
        
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("### 🕒 最佳作業時間")
            st.write("- **殺菌/殺蟲劑：** 下午 3:00 後 (避免高溫藥害，且害蟲多在傍晚活動)")
            st.write("- **營養劑：** 上午 8:00 - 10:00 (氣孔張開，吸收最好)")
        with col2:
            st.markdown("### 🚫 禁忌事項")
            st.write("- 銅劑不可與強酸強鹼混用。")
            st.write("- 開花期盡量避免使用殺蟲劑 (保護授粉昆蟲)。")

# --- 頁面 2: 計算機 (核心) ---
elif page == "⚗️ 藥劑/營養計算":
    st.title("⚗️ 智慧配藥計算機")
    
    # --- [修改處] 這裡使用了 ## 標題語法，讓字體變大 ---
    st.markdown("## 📢 包含 **農藥投料順序** 與 **營養劑** 計算")
    st.markdown("---")

    c1, c2 = st.columns(2)
    with c1:
        selected_stage = st.selectbox("1️⃣ 目前生長階段", list(FARMING_SCENARIOS.keys()))
    with c2:
        # 根據階段抓取底下的 programs
        available_programs = list(FARMING_SCENARIOS[selected_stage]["programs"].keys())
        selected_program = st.selectbox("2️⃣ 選擇作業方案", available_programs)

    st.divider()

    if st.button("🚀 計算配方與順序"):
        df, info = calculate_mix(water_tank, selected_stage, selected_program)
        
        if not df.empty:
            # 顯示摘要資訊
            st.subheader(f"方案：{selected_program}")
            
            m1, m2, m3 = st.columns(3)
            with m1:
                st.metric("💧 總水量", f"{water_tank} L")
            with m2:
                st.metric("📅 施用頻率", info['interval'])
            with m3:
                # 如果有 PHI 顯示 PHI，否則顯示無
                st.metric("🛑 安全採收期 (PHI)", info['phi'], delta_color="inverse")

            st.info(f"💡 **功能說明：** {info['desc']}")

            st.markdown("### 📝 投料順序表 (Mixing Order)")
            st.caption("請嚴格遵守以下順序，防止藥劑沉澱或失效：")
            
            # 使用 Styler 讓表格更好看 (選用)
            st.table(df.set_index("投料順序"))
            
            st.markdown("""
            > **⚠️ 專業混合原則 (Tank Mix Rules):**
            > 1. **水**：藥桶先裝 1/3 ~ 1/2 的水。
            > 2. **粉 (WP/SP)**：先用小桶水溶解後倒入。
            > 3. **水 (SC/SL)**：懸浮劑或水劑。
            > 4. **乳 (EC)**：乳劑最後放 (避免油包水)。
            > 5. **展**：展著劑最後加入，輕輕攪拌。
            """)
            
        else:
            st.error("查無配方資料。")

# --- 頁面 3: 規格 ---
elif page == "📖 規格查詢":
    st.title("📖 作物管理規格書")
    st.markdown("---")
    crop_select = st.selectbox("選擇作物", list(CROPS_SPECS.keys()))
    spec = CROPS_SPECS[crop_select]
    
    c1, c2 = st.columns(2)
    with c1:
        st.metric("🍃 葉果比標準", f"{spec['leaf_fruit_ratio']} : 1")
    with c2:
        st.metric("⚡ 管理優先級", spec['priority'])
    
    st.success(f"**✂️ 疏果口訣：** {spec['spacing_rule']}")
    st.info(f"**📝 栽培備註：** {spec['note']}")
