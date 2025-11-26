import streamlit as st
from loader import DocumentLoader
from comparator import TextComparator # อย่าลืมแก้ import ให้ตรงกับโครงสร้างไฟล์จริงของคุณนะ
import streamlit.components.v1 as components

# --- 1. CONFIG & STYLES (ส่วนตั้งค่า UI เก็บไว้ที่เดิมได้ หรือจะแยกไฟล์ก็ได้ถ้าเยอะ) ---
st.set_page_config(layout="wide", page_title="Pro Document Comparator", page_icon="⚖️")

st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Kanit:wght@300;400;600&display=swap');
        html, body, [class*="css"], font, button, input, textarea, div { font-family: 'Kanit', sans-serif !important; }
        
        /* Navbar & Spacing */
        header[data-testid="stHeader"] { background-color: transparent !important; z-index: 999999 !important; }
        div[data-testid="stDecoration"] { display: none; }
        .block-container { padding-top: 75px !important; padding-bottom: 1rem !important; }
        
        .top-navbar {
            position: fixed; top: 0; left: 0; right: 0; height: 60px;
            background-color: #ffffff; border-bottom: 1px solid #e0e0e0;
            z-index: 99999; display: flex; align-items: center; padding-left: 80px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        }
        .navbar-logo { font-size: 22px; font-weight: 600; color: #2b5876; display: flex; align-items: center; gap: 10px; }

        /* UI Elements */
        div[data-baseweb="base-input"] { border: 1px solid #ced4da !important; border-radius: 8px !important; background-color: #ffffff !important; }
        .css-card { background-color: white; padding: 1rem 1.5rem; border-radius: 10px; box-shadow: 0 2px 8px rgba(0,0,0,0.05); border: 1px solid #eef0f2; margin-top: -15px; }
        
        /* Badge */
        .match-badge { background-color: #2b5876; color: white; padding: 5px 12px; border-radius: 20px; font-size: 0.9rem; }
        section[data-testid="stSidebar"] { top: 60px !important; background-color: #f8f9fa; }
    </style>
    <div class="top-navbar"><div class="navbar-logo"><span>⚖️</span> DocCompare <span style="font-size: 14px; color: #adb5bd; margin-left: 10px; font-weight: 300;">| ระบบเปรียบเทียบเอกสาร</span></div></div>
""", unsafe_allow_html=True)

# --- 2. SIDEBAR ---
with st.sidebar:
    st.markdown("### 📂 Upload Files")
    file1 = st.file_uploader("ต้นฉบับ (Original)", type=["docx", "pdf"])
    file2 = st.file_uploader("ฉบับแก้ไข (Modified)", type=["docx", "pdf"])
    st.markdown("---")
    view_mode = st.radio("มุมมอง", ["แสดงทั้งหมด", "เฉพาะจุดต่าง"], index=1)
    mode_key = "diff_only" if view_mode == "เฉพาะจุดต่าง" else "all"

# --- 3. MAIN LOGIC (Controller) ---
if file1 and file2:
    with st.spinner('⏳ กำลังประมวลผล...'):
        try:
            # A. Prepare Data (Model)
            type1, type2 = file1.name.split('.')[-1].lower(), file2.name.split('.')[-1].lower()
            text1 = DocumentLoader.extract_text(file1, type1)
            text2 = DocumentLoader.extract_text(file2, type2)
            
            # B. UI Controls (View Logic)
            col_search, col_count = st.columns([4, 1])
            with col_search:
                search_query = st.text_input("", placeholder="🔍 พิมพ์คำค้นหา...")
            
            # C. Business Logic (Filtering & Counting)
            match_count = 0
            if search_query:
                # C1. Filter
                text1 = [line for line in text1 if search_query in line]
                text2 = [line for line in text2 if search_query in line]
                # C2. Count
                match_count = sum(line.count(search_query) for line in text1) + sum(line.count(search_query) for line in text2)
                
            # D. Display Status
            with col_count:
                if search_query:
                    badge_color = "#2b5876" if match_count > 0 else "#dc3545"
                    msg = f"เจอ {match_count} จุด" if match_count > 0 else "ไม่พบข้อมูล"
                    st.markdown(f"<div style='text-align:right; padding-top: 8px;'><span class='match-badge' style='background-color:{badge_color};'>{msg}</span></div>", unsafe_allow_html=True)

            # E. Process & Render (เรียกใช้ Module ที่ Clean แล้ว)
            comparator = TextComparator()
            
            # 1. สร้าง HTML ตารางเปล่าๆ
            raw_html = comparator.generate_diff_html(text1, text2, mode=mode_key)
            
            # 2. เอาตารางไปชุบแป้งทอด (ใส่ CSS/JS) ผ่านฟังก์ชันที่เราเพิ่งแยกออกไป
            final_html = comparator.get_final_display_html(raw_html, search_query)

            # F. Output
            st.markdown('<div class="css-card">', unsafe_allow_html=True)
            components.html(final_html, height=800, scrolling=True)
            st.markdown('</div>', unsafe_allow_html=True)

        except Exception as e:
            st.error(f"เกิดข้อผิดพลาด: {e}")
else:
    st.info("👈 กรุณาอัปโหลดไฟล์ที่เมนูด้านซ้ายเพื่อเริ่มเปรียบเทียบ")
