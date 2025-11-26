import streamlit as st
from modules.loader import DocumentLoader
from modules.comparator import TextComparator
import streamlit.components.v1 as components

# 1. Page Config
st.set_page_config(
    layout="wide", 
    page_title="Pro Document Comparator",
    page_icon="⚖️"
)

# 2. CSS Styling (ปรับระยะห่าง และ ใส่ขอบให้ช่องค้นหา)
st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Kanit:wght@300;400;600&display=swap');
        
        /* Force Font */
        html, body, [class*="css"], font, button, input, textarea, div {
            font-family: 'Kanit', sans-serif !important;
        }

        /* --- Navbar Styles --- */
        header[data-testid="stHeader"] {
            background-color: transparent !important;
            z-index: 999999 !important;
        }
        div[data-testid="stDecoration"] { display: none; }

        .top-navbar {
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            height: 60px;
            background-color: #ffffff;
            border-bottom: 1px solid #e0e0e0;
            z-index: 99999;
            display: flex;
            align-items: center;
            padding-left: 80px; 
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        }
        
        .navbar-logo {
            font-size: 22px;
            font-weight: 600;
            color: #2b5876;
            display: flex;
            align-items: center;
            gap: 10px;
            cursor: default;
        }

        /* --- Spacing Optimization (รีดระยะห่าง) --- */
        
        /* 1. ขยับเนื้อหาทั้งหมดขึ้นไปชิด Navbar (ลดจาก 90px เหลือ 75px) */
        .block-container {
            padding-top: 75px !important;
            padding-bottom: 1rem !important;
        }
        
        /* 2. Style ช่องค้นหาให้มีขอบสีเทาชัดเจน */
        div[data-baseweb="base-input"] {
            border: 1px solid #ced4da !important; /* สีเทาชัดเจน */
            border-radius: 8px !important;
            background-color: #ffffff !important;
        }
        /* ตอนกำลังพิมพ์ให้เป็นสีฟ้า */
        div[data-baseweb="base-input"]:focus-within {
            border: 1px solid #2b5876 !important;
            box-shadow: 0 0 0 2px rgba(43, 88, 118, 0.2);
        }

        /* 3. ลดช่องว่างด้านล่างของ Search ก่อนถึง Card */
        /* ดึง Card ขึ้นมาด้วย Margin ติดลบเล็กน้อย */
        .css-card {
            background-color: white;
            padding: 1rem 1.5rem; /* ลด padding แนวตั้งของ card ลงหน่อย */
            border-radius: 10px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.05);
            border: 1px solid #eef0f2;
            margin-top: -15px; /* <--- ดึงตารางขึ้นมาชิดช่องค้นหา */
        }

        /* Sidebar & Others */
        section[data-testid="stSidebar"] {
            top: 60px !important; 
            background-color: #f8f9fa;
        }
        
        /* Diff Colors */
        .diff_add { background-color: #d4edda; color: #155724; }
        .diff_chg { background-color: #fff3cd; color: #856404; }
        .diff_sub { background-color: #f8d7da; color: #721c24; text-decoration: line-through; opacity: 0.6;}
        
    </style>
    
    <div class="top-navbar">
        <div class="navbar-logo">
            <span>⚖️</span> DocCompare <span style="font-size: 14px; color: #adb5bd; margin-left: 10px; font-weight: 300;">| ระบบเปรียบเทียบเอกสาร</span>
        </div>
    </div>
""", unsafe_allow_html=True)

# --- Sidebar ---
with st.sidebar:
    st.markdown("### 📂 Upload Files")
    file1 = st.file_uploader("ต้นฉบับ (Original)", type=["docx", "pdf"])
    file2 = st.file_uploader("ฉบับแก้ไข (Modified)", type=["docx", "pdf"])
    
    st.markdown("---")
    st.markdown("### 👁️ Options")
    view_mode = st.radio("มุมมอง", ["แสดงทั้งหมด", "เฉพาะจุดต่าง"], index=1)
    mode_key = "diff_only" if view_mode == "เฉพาะจุดต่าง" else "all"

# --- Main Content ---
if file1 and file2:
    type1 = file1.name.split('.')[-1].lower()
    type2 = file2.name.split('.')[-1].lower()

    with st.spinner('⏳ กำลังประมวลผล...'):
        try:
            text1 = DocumentLoader.extract_text(file1, type1)
            text2 = DocumentLoader.extract_text(file2, type2)
            
            # --- Search Bar ---
            # ใช้ columns เพื่อจัดวาง แต่มันจะมี gap ล่างมาให้ เราจะดึง card ข้างล่างขึ้นมาแทน
            search_query = st.text_input("", placeholder="🔍 พิมพ์คำค้นหาตรงนี้...")
            
            if search_query:
                text1 = [line for line in text1 if search_query in line]
                text2 = [line for line in text2 if search_query in line]

            comparator = TextComparator()
            html_code = comparator.generate_diff_html(text1, text2, mode=mode_key)

            # --- Result Card ---
            # ใส่ class css-card เพื่อดึง margin-top: -15px ตามที่เขียนใน CSS ข้างบน
            st.markdown('<div class="css-card">', unsafe_allow_html=True)
            
            iframe_style = """
            <style>
                @import url('https://fonts.googleapis.com/css2?family=Kanit:wght@300;400&display=swap');
                body { font-family: 'Kanit', sans-serif; margin: 0; padding: 0;}
                table.diff { width: 100%; border-collapse: collapse; font-size: 14px; }
                .diff_header { background-color: #f8f9fa; color: #6c757d; padding: 8px; text-align: right; border-bottom: 2px solid #dee2e6; width: 40px; font-weight: bold;}
                td { padding: 10px; border-bottom: 1px solid #f0f0f0; vertical-align: top;}
                .diff_add { background-color: #e2f0d9; color: #38761d; }
                .diff_chg { background-color: #fff2cc; color: #bf9000; }
                .diff_sub { background-color: #fce8e6; color: #c00000; text-decoration: line-through;}
            </style>
            """
            
            components.html(iframe_style + html_code, height=800, scrolling=True)
            st.markdown('</div>', unsafe_allow_html=True)

        except Exception as e:
            st.error(f"เกิดข้อผิดพลาด: {e}")

else:
    st.info("👈 กรุณาอัปโหลดไฟล์ที่เมนูด้านซ้ายเพื่อเริ่มเปรียบเทียบ")