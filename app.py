import streamlit as st
from streamlit_option_menu import option_menu
from modules.loader import DocumentLoader
from modules.comparator import TextComparator 
from modules.code_view import render_code_compare_mode
from modules.spell_check_view import render_spell_check_mode
from modules.ocr_view import render_ocr_mode
import streamlit.components.v1 as components

# --- 1. CONFIG & STYLES ---
st.set_page_config(layout="wide", page_title="Smart Document - Intelligent Platform", page_icon="📑")

st.markdown("""
    <style>
        /* Import Font: Kanit & JetBrains Mono */
        @import url('https://fonts.googleapis.com/css2?family=Kanit:wght@300;400;500;600&display=swap');
        @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;700&display=swap');

        /* Global Font Settings */
        html, body, [class*="css"], font, button, input, textarea, div { 
            font-family: 'Kanit', sans-serif !important; 
        }
        
        /* Navbar Adjustment */
        header[data-testid="stHeader"] { background-color: transparent !important; z-index: 999999 !important; }
        div[data-testid="stDecoration"] { display: none; }
        .block-container { padding-top: 50px !important; padding-bottom: 1rem !important; }
        
        /* Fixed Navbar */
        .top-navbar {
            position: fixed; top: 0; left: 0; right: 0; height: 50px;
            background-color: #ffffff; border-bottom: 1px solid #e0e0e0;
            z-index: 99999; display: flex; align-items: center; padding-left: 80px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        }
        
        .navbar-logo { 
            font-size: 20px; font-weight: 600; color: #0d6efd;
            display: flex; align-items: center; gap: 10px; letter-spacing: 0.5px;
        }
        .navbar-tagline {
            font-size: 13px; color: #6c757d; margin-left: 15px; font-weight: 300;
            border-left: 1px solid #dee2e6; padding-left: 15px;
        }

        /* Sidebar Styling */
        section[data-testid="stSidebar"] { top: 50px !important; background-color: #f8f9fa; }
        
        /* Custom styling for Option Menu (Sidebar) */
        .nav-link {
            font-family: 'Kanit', sans-serif !important;
            font-size: 15px !important;
            font-weight: 400 !important;
            margin: 5px !important;
        }
        .nav-link-selected {
            font-weight: 500 !important;
            background-color: #0d6efd !important;
        }
        .menu-title {
            font-family: 'Kanit', sans-serif !important;
            font-weight: 600 !important;
            color: #495057 !important;
            font-size: 18px !important;
            padding-bottom: 10px !important;
        }

        /* General UI Elements */
        div[data-baseweb="base-input"], div[data-baseweb="textarea"] { 
            border: 1px solid #ced4da !important; border-radius: 8px !important; background-color: #ffffff !important; 
        }
        .css-card { background-color: white; padding: 1rem 1.5rem; border-radius: 10px; box-shadow: 0 2px 8px rgba(0,0,0,0.05); border: 1px solid #eef0f2; margin-top: -15px; }
        .match-badge { background-color: #0d6efd; color: white; padding: 5px 12px; border-radius: 20px; font-size: 0.9rem; }
        textarea { font-family: 'JetBrains Mono', monospace !important; font-size: 14px !important; }
    </style>
    
    <div class="top-navbar">
        <div class="navbar-logo">
            <span>📑</span> Smart Document
            <span class="navbar-tagline">ระบบจัดการเอกสารอัจฉริยะ (Compare / Proofread / OCR)</span>
        </div>
    </div>
""", unsafe_allow_html=True)

# --- 2. SIDEBAR (MENU ปรับปรุงใหม่) ---
with st.sidebar:
    
    # เรียงลำดับเมนูใหม่ตามที่ขอ
    app_mode = option_menu(
        menu_title="รายการระบบ", 
        options=[
            "แปลง PDF เป็นข้อความ (AI OCR)", # 1. OCR (ย้ายมาบนสุด)
            "เปรียบเทียบเอกสาร",             # 2. Compare Docs
            "ตรวจการสะกดคำ",                 # 3. Spell Check
            "เปรียบเทียบโค้ด"                # 4. Compare Code
        ],
        icons=['qr-code-scan', 'file-earmark-diff', 'spellcheck', 'code-slash'], 
        menu_icon="grid-fill", 
        default_index=0,
        styles={
            "container": {"padding": "5px", "background-color": "#f8f9fa"},
            "icon": {"color": "#0d6efd", "font-size": "18px"}, 
            "nav-link": {"font-size": "15px", "text-align": "left", "margin":"5px", "--hover-color": "#eef0f2"},
            "nav-link-selected": {"background-color": "#0d6efd", "color": "white"},
        }
    )
    
    st.markdown("---")
    
    # --- Contextual Info (ปรับข้อความตามเมนู) ---
    if app_mode == "แปลง PDF เป็นข้อความ (AI OCR)":
        st.info("💡 **Tips:** ใช้ AI แปลงภาพเอกสาร PDF ให้เป็นข้อความ Text/Word (รองรับภาษาไทย 100%)")

    elif app_mode == "เปรียบเทียบเอกสาร":
        st.markdown("### 📂 Upload Files")
        file1 = st.file_uploader("ต้นฉบับ (Original)", type=["docx", "pdf"])
        file2 = st.file_uploader("ฉบับแก้ไข (Modified)", type=["docx", "pdf"])
        st.markdown("---")
        st.markdown("### 👁️ Options")
        view_mode = st.radio("มุมมอง", ["แสดงทั้งหมด", "เฉพาะจุดต่าง"], index=0)
        mode_key = "diff_only" if view_mode == "เฉพาะจุดต่าง" else "all"
        
    elif app_mode == "ตรวจการสะกดคำ":
        st.info("💡 **Tips:** ใช้ AI ตรวจทานไวยากรณ์ คำผิด และจัดรูปประโยคให้สละสลวย")
        
    elif app_mode == "เปรียบเทียบโค้ด":
        st.info("💡 **Tips:** เครื่องมือสำหรับ Developer เทียบ Code Change หรือ Config")
        mode_key = "all"

# --- 3. MAIN LOGIC (Controller) ---

# 1. OCR (ขึ้นก่อน)
if app_mode == "แปลง PDF เป็นข้อความ (AI OCR)":
    render_ocr_mode()

# 2. Compare Docs
elif app_mode == "เปรียบเทียบเอกสาร":
    if file1 and file2:
        with st.spinner('⏳ กำลังประมวลผลไฟล์...'):
            try:
                type1, type2 = file1.name.split('.')[-1].lower(), file2.name.split('.')[-1].lower()
                text1 = DocumentLoader.extract_text(file1, type1)
                text2 = DocumentLoader.extract_text(file2, type2)
                
                col_search, col_count = st.columns([4, 1])
                with col_search:
                    search_query = st.text_input("", placeholder="🔍 พิมพ์คำค้นหา...")
                
                match_count = 0
                if search_query:
                    text1 = [line for line in text1 if search_query in line]
                    text2 = [line for line in text2 if search_query in line]
                    match_count = sum(line.count(search_query) for line in text1) + sum(line.count(search_query) for line in text2)
                
                with col_count:
                    if search_query:
                        badge_color = "#0d6efd" if match_count > 0 else "#dc3545"
                        msg = f"เจอ {match_count} จุด" if match_count > 0 else "ไม่พบข้อมูล"
                        st.markdown(f"<div style='text-align:right; padding-top: 8px;'><span class='match-badge' style='background-color:{badge_color};'>{msg}</span></div>", unsafe_allow_html=True)

                comparator = TextComparator()
                current_mode = "all" if search_query else mode_key
                
                raw_html = comparator.generate_diff_html(text1, text2, mode=current_mode)
                final_html = comparator.get_final_display_html(raw_html, search_query)

                st.markdown('<div class="css-card">', unsafe_allow_html=True)
                components.html(final_html, height=800, scrolling=True)
                st.markdown('</div>', unsafe_allow_html=True)

            except Exception as e:
                st.error(f"เกิดข้อผิดพลาด: {e}")
    else:
        st.info("👈 กรุณาอัปโหลดไฟล์ Word/PDF ที่เมนูด้านซ้าย")

# 3. Spell Check
elif app_mode == "ตรวจการสะกดคำ":
    render_spell_check_mode()

# 4. Compare Code
elif app_mode == "เปรียบเทียบโค้ด":
    render_code_compare_mode("all")
