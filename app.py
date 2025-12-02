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
        
        /* --- 1. NAVBAR (แถบบนสุด) --- */
        .top-navbar {
            position: fixed; 
            top: 0; 
            left: 0; 
            right: 0; 
            height: 60px;
            background-color: #ffffff; 
            border-bottom: 1px solid #e0e0e0;
            z-index: 99999; /* อยู่เหนือทุกอย่าง */
            display: flex; 
            align-items: center; 
            padding-left: 80px; /* เว้นที่ให้ปุ่ม Hamburger */
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        }
        
        /* --- 2. STREAMLIT HEADER (ซ่อน Header เดิมทิ้งไปเลยเพื่อลดช่องว่าง) --- */
        header[data-testid="stHeader"] { 
            background-color: transparent !important;
            z-index: 100000 !important; /* ให้ปุ่ม Hamburger อยู่เหนือ Navbar เรา */
        }
        
        /* ซ่อนแถบสีรุ้ง */
        div[data-testid="stDecoration"] { display: none; }
        div[data-testid="stToolbar"] { display: none; } /* ซ่อน Toolbar ขวาบนถ้าไม่ใช้ */

        /* --- 3. SIDEBAR (ปรับให้เต็มจอและดันเนื้อหาลง) --- */
        section[data-testid="stSidebar"] { 
            top: 0px !important;      /* ชนขอบบนสุด */
            height: 100vh !important; /* สูงเต็มจอ */
            z-index: 99998 !important; /* อยู่ใต้ Navbar นิดนึง */
            padding-top: 60px !important; /* ดันเนื้อหาเมนูลงมา เท่าความสูง Navbar */
            background-color: #f8f9fa;
            box-shadow: 2px 0 5px rgba(0,0,0,0.05);
        }
        
        /* ปรับปุ่มปิด Sidebar (x) ให้ลงมาหน่อย */
        button[kind="header"] {
            top: 10px !important;
        }

        /* --- 4. MAIN CONTENT (เนื้อหาหลัก) --- */
        .block-container { 
            /* ดันเนื้อหาลงมาให้พ้น Navbar (60px) + ระยะห่างนิดหน่อย (20px) */
            padding-top: 80px !important; 
            padding-bottom: 2rem !important; 
        }
        
        /* ลบ Margin ส่วนเกินของ Element ตัวแรกสุด */
        .block-container > div:first-child {
            margin-top: 0px !important;
            padding-top: 0px !important;
        }
        
        /* --- Styles อื่นๆ --- */
        .navbar-logo { 
            font-size: 22px; font-weight: 600; color: #0d6efd;
            display: flex; align-items: center; gap: 10px; letter-spacing: 0.5px;
        }
        .navbar-tagline {
            font-size: 14px; color: #6c757d; margin-left: 15px; font-weight: 300;
            border-left: 1px solid #dee2e6; padding-left: 15px;
        }

        div[data-baseweb="base-input"], div[data-baseweb="textarea"] { 
            border: 1px solid #ced4da !important; border-radius: 8px !important; background-color: #ffffff !important; 
        }
        .css-card { background-color: white; padding: 1rem 1.5rem; border-radius: 10px; box-shadow: 0 2px 8px rgba(0,0,0,0.05); border: 1px solid #eef0f2; margin-top: -15px; }
        .match-badge { background-color: #0d6efd; color: white; padding: 5px 12px; border-radius: 20px; font-size: 0.9rem; }
        textarea { font-family: 'JetBrains Mono', monospace !important; font-size: 14px !important; }
        
        /* Option Menu Style */
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
    
    # Contextual Info
    info_dict = {
        "AI OCR (แปลง PDF)": "Advanced OCR: อ่านเอกสารภาพ/PDF เป็นข้อความ",
        "แก้ PDF เพี้ยน (Quick Fix)": "Fix PDF: แก้ภาษาต่างดาวให้เป็น Word",
        "เปรียบเทียบเอกสาร": "Compare Docs: หาจุดต่างระหว่าง 2 ไฟล์",
        "ตรวจการสะกดคำ": "Proofread: ตรวจคำผิดและแก้ประโยค",
        "เปรียบเทียบโค้ด": "Diff Code: เทียบ Source Code สำหรับ Dev",
        "ตั้งค่า & ประวัติ": "Settings: ดูประวัติการใช้งาน (Session Log)"
    }
    
    if app_mode in info_dict:
        st.info(f"💡 **Info:** {info_dict[app_mode]}")

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
