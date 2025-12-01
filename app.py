import streamlit as st
from streamlit_option_menu import option_menu
from modules.loader import DocumentLoader
from modules.comparator import TextComparator 
# Import Modules
from modules.code_view import render_code_compare_mode
from modules.spell_check_view import render_spell_check_mode
from modules.ocr_view import render_ocr_mode
from modules.document_view import render_document_compare_mode # <--- Import ตัวใหม่
import streamlit.components.v1 as components

# --- 1. CONFIG & STYLES ---
st.set_page_config(layout="wide", page_title="Smart Document - Intelligent Platform", page_icon="📑")

st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Kanit:wght@300;400;500;600&display=swap');
        @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;700&display=swap');

        html, body, [class*="css"], font, button, input, textarea, div { font-family: 'Kanit', sans-serif !important; }
        
        header[data-testid="stHeader"] { background-color: transparent !important; z-index: 999999 !important; }
        div[data-testid="stDecoration"] { display: none; }
        .block-container { padding-top: 50px !important; padding-bottom: 1rem !important; }
        
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
        
        div[data-baseweb="base-input"], div[data-baseweb="textarea"] { 
            border: 1px solid #ced4da !important; border-radius: 8px !important; background-color: #ffffff !important; 
        }
        .css-card { background-color: white; padding: 1rem 1.5rem; border-radius: 10px; box-shadow: 0 2px 8px rgba(0,0,0,0.05); border: 1px solid #eef0f2; margin-top: -15px; }
        .match-badge { background-color: #0d6efd; color: white; padding: 5px 12px; border-radius: 20px; font-size: 0.9rem; }
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
        options=[
            "แปลง PDF เป็นข้อความ (AI OCR)",
            "เปรียบเทียบเอกสาร",
            "ตรวจการสะกดคำ",
            "เปรียบเทียบโค้ด"
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
    
    # Contextual Info (เหลือแค่ Tips เล็กน้อย ไม่ต้องมี Input แล้ว)
    if app_mode == "แปลง PDF เป็นข้อความ (AI OCR)":
        st.info("💡 **Tips:** ใช้ AI แปลงภาพเอกสาร PDF ให้เป็นข้อความ Text/Word")

    elif app_mode == "เปรียบเทียบเอกสาร":
        st.info("💡 **Tips:** อัปโหลดไฟล์ที่กล่องด้านขวา เพื่อเริ่มเปรียบเทียบ")
        
    elif app_mode == "ตรวจการสะกดคำ":
        st.info("💡 **Tips:** ใช้ AI ตรวจทานไวยากรณ์และคำผิด")
        
    elif app_mode == "เปรียบเทียบโค้ด":
        st.info("💡 **Tips:** เทียบ Code Change หรือ Config Files")

# --- 3. MAIN LOGIC (Controller) ---

# 1. OCR
if app_mode == "แปลง PDF เป็นข้อความ (AI OCR)":
    render_ocr_mode()

# 2. Compare Docs (เรียกฟังก์ชันใหม่)
elif app_mode == "เปรียบเทียบเอกสาร":
    render_document_compare_mode()

# 3. Spell Check
elif app_mode == "ตรวจการสะกดคำ":
    render_spell_check_mode()

# 4. Compare Code
elif app_mode == "เปรียบเทียบโค้ด":
    render_code_compare_mode("all")
