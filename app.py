import streamlit as st
from streamlit_option_menu import option_menu

# Import Views
from modules.loader import DocumentLoader
from modules.comparator import TextComparator 
from modules.code_view import render_code_compare_mode
from modules.spell_check_view import render_spell_check_mode
from modules.ocr_view import render_ocr_mode
from modules.document_view import render_document_compare_mode
from modules.quick_convert_view import render_quick_convert_mode
from modules.settings_view import render_settings_page
from modules.summarize_view import render_summarize_mode # <--- Import ตัวใหม่

# --- CONFIG ---
st.set_page_config(layout="wide", page_title="Smart Document - Intelligent Platform", page_icon="📑")

# ... (CSS เดิม ไม่ต้องแก้) ...
st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Kanit:wght@300;400;500;600&display=swap');
        @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;700&display=swap');
        html, body, [class*="css"], font, button, input, textarea, div { font-family: 'Kanit', sans-serif !important; }
        header[data-testid="stHeader"] { background-color: transparent !important; z-index: 999999 !important; }
        div[data-testid="stDecoration"] { display: none; }
        .block-container { padding-top: 50px !important; padding-bottom: 1rem !important; }
        .top-navbar { position: fixed; top: 0; left: 0; right: 0; height: 50px; background-color: #ffffff; border-bottom: 1px solid #e0e0e0; z-index: 99999; display: flex; align-items: center; padding-left: 80px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
        .navbar-logo { font-size: 20px; font-weight: 600; color: #0d6efd; display: flex; align-items: center; gap: 10px; letter-spacing: 0.5px; }
        .navbar-tagline { font-size: 13px; color: #6c757d; margin-left: 15px; font-weight: 300; border-left: 1px solid #dee2e6; padding-left: 15px; }
        section[data-testid="stSidebar"] { top: 50px !important; background-color: #f8f9fa; }
        div[data-baseweb="base-input"], div[data-baseweb="textarea"] { border: 1px solid #ced4da !important; border-radius: 8px !important; background-color: #ffffff !important; }
        .css-card { background-color: white; padding: 1rem 1.5rem; border-radius: 10px; box-shadow: 0 2px 8px rgba(0,0,0,0.05); border: 1px solid #eef0f2; margin-top: -15px; }
        .match-badge { background-color: #0d6efd; color: white; padding: 5px 12px; border-radius: 20px; font-size: 0.9rem; }
        textarea { font-family: 'JetBrains Mono', monospace !important; font-size: 14px !important; }
        .nav-link-selected { font-weight: 600 !important; }
    </style>
    <div class="top-navbar">
        <div class="navbar-logo">
            <span>📑</span> Smart Document
            <span class="navbar-tagline">ระบบจัดการเอกสารอัจฉริยะ (Complete Suite)</span>
        </div>
    </div>
""", unsafe_allow_html=True)

# --- SIDEBAR ---
with st.sidebar:
    app_mode = option_menu(
        menu_title="รายการระบบ", 
        options=[
            "AI OCR (แปลง PDF)",
            "แก้ PDF เพี้ยน (Quick Fix)",
            "สรุปย่อเอกสาร (Summarizer)", # <--- เมนูใหม่
            "เปรียบเทียบเอกสาร",
            "ตรวจการสะกดคำ",
            "เปรียบเทียบโค้ด",
            "---",
            "ตั้งค่า & ประวัติ"
        ],
        icons=['qr-code-scan', 'magic', 'file-text', 'file-earmark-diff', 'spellcheck', 'code-slash', '', 'gear'], 
        menu_icon="grid-fill", 
        default_index=0,
        styles={
            "container": {"padding": "5px", "background-color": "#f8f9fa"},
            "icon": {"color": "#0d6efd", "font-size": "16px"}, 
            "nav-link": {"font-size": "14px", "text-align": "left", "margin":"2px", "--hover-color": "#eef0f2"},
            "nav-link-selected": {"background-color": "#0d6efd", "color": "white"},
            "menu-title": {"color": "#495057", "font-size": "16px", "font-weight": "bold", "margin-bottom": "10px"}
        }
    )
    
    st.markdown("---")
    
    # Tips
    if app_mode == "สรุปย่อเอกสาร (Summarizer)":
        st.info("💡 **Tips:** เหมาะสำหรับผู้บริหาร ช่วยสรุปเอกสารหลายสิบหน้าให้เหลือหน้าเดียว")

# --- ROUTER ---

if app_mode == "AI OCR (แปลง PDF)":
    render_ocr_mode()
elif app_mode == "แก้ PDF เพี้ยน (Quick Fix)":
    render_quick_convert_mode()
elif app_mode == "สรุปย่อเอกสาร (Summarizer)":
    render_summarize_mode() # <--- เรียกใช้
elif app_mode == "เปรียบเทียบเอกสาร":
    render_document_compare_mode()
elif app_mode == "ตรวจการสะกดคำ":
    render_spell_check_mode()
elif app_mode == "เปรียบเทียบโค้ด":
    render_code_compare_mode("all")
elif app_mode == "ตั้งค่า & ประวัติ":
    render_settings_page()
