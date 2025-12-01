import streamlit as st
from streamlit_option_menu import option_menu
from modules.loader import DocumentLoader
from modules.comparator import TextComparator 
from modules.code_view import render_code_compare_mode
from modules.spell_check_view import render_spell_check_mode
import streamlit.components.v1 as components

# --- 1. CONFIG & STYLES ---
# เปลี่ยนชื่อตรง Tab Browser
st.set_page_config(layout="wide", page_title="Smart Document - Intelligent Platform", page_icon="📑")

st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Kanit:wght@300;400;600&display=swap');
        @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;700&display=swap');

        html, body, [class*="css"], font, button, input, textarea, div { font-family: 'Kanit', sans-serif !important; }
        
        header[data-testid="stHeader"] { background-color: transparent !important; z-index: 999999 !important; }
        div[data-testid="stDecoration"] { display: none; }
        .block-container { padding-top: 75px !important; padding-bottom: 1rem !important; }
        
        .top-navbar {
            position: fixed; top: 0; left: 0; right: 0; height: 60px;
            background-color: #ffffff; border-bottom: 1px solid #e0e0e0;
            z-index: 99999; display: flex; align-items: center; padding-left: 80px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        }
        
        .navbar-logo { 
            font-size: 24px; 
            font-weight: 700; 
            color: #0d6efd; /* เปลี่ยนสี Logo เป็นสีฟ้าให้ดู Smart */
            display: flex; 
            align-items: center; 
            gap: 10px; 
            letter-spacing: 0.5px;
        }
        .navbar-tagline {
            font-size: 14px; 
            color: #6c757d; 
            margin-left: 15px; 
            font-weight: 300;
            border-left: 1px solid #dee2e6;
            padding-left: 15px;
        }

        div[data-baseweb="base-input"], div[data-baseweb="textarea"] { 
            border: 1px solid #ced4da !important; border-radius: 8px !important; background-color: #ffffff !important; 
        }
        
        .css-card { background-color: white; padding: 1rem 1.5rem; border-radius: 10px; box-shadow: 0 2px 8px rgba(0,0,0,0.05); border: 1px solid #eef0f2; margin-top: -15px; }
        .match-badge { background-color: #0d6efd; color: white; padding: 5px 12px; border-radius: 20px; font-size: 0.9rem; }
        section[data-testid="stSidebar"] { top: 60px !important; background-color: #f8f9fa; }
        textarea { font-family: 'JetBrains Mono', monospace !important; font-size: 14px !important; }
        
        .nav-link-selected { font-weight: 600 !important; }
    </style>
    
    <div class="top-navbar">
        <div class="navbar-logo">
            <span>📑</span> Smart Document
            <span class="navbar-tagline">ระบบจัดการเอกสารอัจฉริยะ (Compare / Proofread / OCR)</span>
        </div>
    </div>
""", unsafe_allow_html=True)

# --- 2. SIDEBAR (MENU) ---
with st.sidebar:
    
    app_mode = option_menu(
        menu_title="รายการระบบ", 
        options=["เปรียบเทียบเอกสาร", "เปรียบเทียบโค้ด", "ตรวจการสะกดคำ (AI)", "OCR แปลงภาพเป็นข้อความ"],
        icons=['file-earmark-diff', 'code-slash', 'spellcheck', 'qr-code-scan'], 
        menu_icon="grid-fill", 
        default_index=0,
        styles={
            "container": {"padding": "5px", "background-color": "#f8f9fa"},
            "icon": {"color": "#0d6efd", "font-size": "18px"}, 
            "nav-link": {"font-size": "15px", "text-align": "left", "margin":"5px", "--hover-color": "#eef0f2"},
            "nav-link-selected": {"background-color": "#0d6efd", "color": "white"}, # ปรับธีมเป็นสีฟ้า Smart Blue
        }
    )
    
    st.markdown("---")
    
    # --- Contextual Sidebar Content ---
    if app_mode == "เปรียบเทียบเอกสาร":
        st.markdown("### 📂 Upload Files")
        file1 = st.file_uploader("ต้นฉบับ (Original)", type=["docx", "pdf"])
        file2 = st.file_uploader("ฉบับแก้ไข (Modified)", type=["docx", "pdf"])
        st.markdown("---")
        st.markdown("### 👁️ Options")
        view_mode = st.radio("มุมมอง", ["แสดงทั้งหมด", "เฉพาะจุดต่าง"], index=0)
        mode_key = "diff_only" if view_mode == "เฉพาะจุดต่าง" else "all"
        
    elif app_mode == "เปรียบเทียบโค้ด":
        st.info("💡 **Tips:** เหมาะสำหรับ Developer ใช้เทียบ Code Change หรือ Config Files")
        mode_key = "all"

    elif app_mode == "ตรวจการสะกดคำ (AI)":
        st.info("💡 **Tips:** ใช้ AI ช่วยตรวจสอบความถูกต้องของไวยากรณ์และรูปประโยค")
    
    elif app_mode == "OCR แปลงภาพเป็นข้อความ":
        st.warning("🚧 **Coming Soon:** ระบบแปลงภาพสแกนเป็นข้อความ (AI OCR) กำลังอยู่ในระหว่างการพัฒนา")

# --- 3. MAIN LOGIC (Controller) ---

if app_mode == "เปรียบเทียบเอกสาร":
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

elif app_mode == "เปรียบเทียบโค้ด":
    render_code_compare_mode("all")

elif app_mode == "ตรวจการสะกดคำ (AI)":
    render_spell_check_mode()

elif app_mode == "OCR แปลงภาพเป็นข้อความ":
    # หน้า Placeholder สำหรับ OCR
    st.markdown("""
        <div style="text-align: center; padding: 50px; background-color: white; border-radius: 10px; border: 2px dashed #ddd;">
            <h1>📷 AI OCR System</h1>
            <h3 style="color: #888;">Coming Soon...</h3>
            <p>ระบบแปลงภาพเอกสารเป็นข้อความด้วย AI ความแม่นยำสูง</p>
            <p><i>(เตรียมพบกันในเวอร์ชันถัดไป ของ Smart Document)</i></p>
        </div>
    """, unsafe_allow_html=True)
