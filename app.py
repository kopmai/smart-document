import streamlit as st
from streamlit_option_menu import option_menu

# Import Views
from modules.services.loader import DocumentLoader
from modules.services.comparator import TextComparator 

from modules.views.code_view import render_code_compare_mode
from modules.views.spell_check_view import render_spell_check_mode
from modules.views.ocr_view import render_ocr_mode
from modules.views.document_view import render_document_compare_mode
from modules.views.quick_convert_view import render_quick_convert_mode
from modules.views.settings_view import render_settings_page

import streamlit.components.v1 as components

# --- 1. CONFIG & STYLES ---
st.set_page_config(layout="wide", page_title="Smart Document - Intelligent Platform", page_icon="📑")

st.markdown("""
    <style>
        /* Import Fonts */
        @import url('https://fonts.googleapis.com/css2?family=Kanit:wght@300;400;500;600&display=swap');
        @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;700&display=swap');

        /* Global Font */
        html, body, [class*="css"], font, button, input, textarea, div { 
            font-family: 'Kanit', sans-serif !important; 
        }
        
        /* --- 1. Z-INDEX STRATEGY (สำคัญมาก!) --- */
        
        /* Level 1: Navbar (อยู่ล่างสุดในกลุ่ม Header) */
        .top-navbar {
            position: sticky; 
            top: 0; 
            z-index: 990; /* ต่ำกว่า Header และ Sidebar */
            background-color: #ffffff; 
            height: 60px;
            border-bottom: 1px solid #e0e0e0;
            display: flex; 
            align-items: center; 
            padding-left: 60px; /* เว้นที่ให้ปุ่ม Hamburger */
            width: 100%;
            margin-bottom: 20px;
        }

        /* Level 2: Streamlit Header (อยู่เหนือ Navbar เพื่อให้ปุ่ม Hamburger กดได้) */
        header[data-testid="stHeader"] { 
            background-color: transparent !important; 
            z-index: 991 !important; 
            pointer-events: none; /* อนุญาตให้คลิกทะลุพื้นที่ว่างไปโดน Navbar ได้ */
        }
        
        /* Level 3: เฉพาะปุ่มใน Header (ต้องกดได้) */
        header[data-testid="stHeader"] button {
            pointer-events: auto !important; /* กลับมาคลิกได้ */
            color: #0d6efd !important; /* บังคับปุ่มเป็นสีฟ้า (จะได้เห็นชัดๆ บนพื้นขาว) */
        }

        /* Level 4: Sidebar (อยู่สูงสุด ทับทุกอย่างเมื่อเปิดออกมา) */
        section[data-testid="stSidebar"] { 
            top: 0px !important;      
            height: 100vh !important;
            z-index: 9999 !important; /* สูงสุด */
            padding-top: 50px !important; 
            background-color: #f8f9fa;
            box-shadow: 2px 0 10px rgba(0,0,0,0.1);
        }

        /* --- 2. LAYOUT FIXES --- */
        div[data-testid="stDecoration"] { display: none; }
        
        .block-container { 
            padding-top: 0px !important; /* ดึงเนื้อหาขึ้นบนสุด */
            padding-bottom: 2rem !important; 
        }
        
        /* Styles อื่นๆ */
        .navbar-logo { font-size: 22px; font-weight: 600; color: #0d6efd; display: flex; align-items: center; gap: 10px; letter-spacing: 0.5px; }
        .navbar-tagline { font-size: 14px; color: #6c757d; margin-left: 15px; font-weight: 300; border-left: 1px solid #dee2e6; padding-left: 15px; }
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

# --- 2. SIDEBAR (MENU) ---
with st.sidebar:
    
    app_mode = option_menu(
        menu_title="รายการระบบ", 
        options=[
            "AI OCR (แปลง PDF)",
            "แก้ PDF เพี้ยน (Quick Fix)",
            "เปรียบเทียบเอกสาร",
            "ตรวจการสะกดคำ",
            "เปรียบเทียบโค้ด",
            "---",
            "ตั้งค่า & ประวัติ"
        ],
        icons=['file-earmark-text', 'magic', 'file-earmark-diff', 'spellcheck', 'code-slash', '', 'gear'], 
        menu_icon="grid-fill", 
        default_index=0,
        styles={
            "container": {"padding": "5px", "background-color": "#f8f9fa"},
            "icon": {"font-size": "16px"}, 
            "nav-link": {
                "font-size": "14px", 
                "text-align": "left", 
                "margin": "2px", 
                "--hover-color": "#eef0f2",
                "color": "#495057"
            },
            "nav-link-selected": {"background-color": "#0d6efd", "color": "white"},
            "menu-title": {"color": "#495057", "font-size": "16px", "font-weight": "bold", "margin-bottom": "10px"}
        }
    )
    
    st.markdown("---")
    
    if app_mode == "AI OCR (แปลง PDF)":
        st.info("💡 **Advanced:** อ่านเอกสารภาพ/PDF เป็นข้อความ")
    elif app_mode == "แก้ PDF เพี้ยน (Quick Fix)":
        st.info("💡 **Fast Track:** แก้ภาษาต่างดาวให้เป็น Word")
    elif app_mode == "เปรียบเทียบเอกสาร":
        st.info("💡 **Compare:** หาจุดต่างระหว่าง 2 ไฟล์")
    elif app_mode == "ตรวจการสะกดคำ":
        st.info("💡 **Proofread:** ตรวจคำผิดและแก้ประโยค")
    elif app_mode == "เปรียบเทียบโค้ด":
        st.info("💡 **Diff Code:** เทียบ Source Code")
    elif app_mode == "ตั้งค่า & ประวัติ":
        st.info("⚙️ **Settings:** ดูประวัติการใช้งาน")

# --- 3. MAIN LOGIC (Router) ---

if app_mode == "AI OCR (แปลง PDF)":
    render_ocr_mode()

elif app_mode == "แก้ PDF เพี้ยน (Quick Fix)":
    render_quick_convert_mode()

elif app_mode == "เปรียบเทียบเอกสาร":
    render_document_compare_mode()

elif app_mode == "ตรวจการสะกดคำ":
    render_spell_check_mode()

elif app_mode == "เปรียบเทียบโค้ด":
    render_code_compare_mode("all")

elif app_mode == "ตั้งค่า & ประวัติ":
    render_settings_page()
