import streamlit as st
from loader import DocumentLoader
from comparator import TextComparator
import streamlit.components.v1 as components

# 1. Page Config
st.set_page_config(
    layout="wide", 
    page_title="Pro Document Comparator",
    page_icon="⚖️"
)

# 2. CSS Styling
st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Kanit:wght@300;400;600&display=swap');
        
        html, body, [class*="css"], font, button, input, textarea, div {
            font-family: 'Kanit', sans-serif !important;
        }

        /* --- Navbar --- */
        header[data-testid="stHeader"] { background-color: transparent !important; z-index: 999999 !important; }
        div[data-testid="stDecoration"] { display: none; }

        .top-navbar {
            position: fixed; top: 0; left: 0; right: 0; height: 60px;
            background-color: #ffffff; border-bottom: 1px solid #e0e0e0;
            z-index: 99999; display: flex; align-items: center;
            padding-left: 80px; box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        }
        
        .navbar-logo {
            font-size: 22px; font-weight: 600; color: #2b5876;
            display: flex; align-items: center; gap: 10px; cursor: default;
        }

        /* --- Spacing & Layout --- */
        .block-container { padding-top: 75px !important; padding-bottom: 1rem !important; }
        
        div[data-baseweb="base-input"] {
            border: 1px solid #ced4da !important; border-radius: 8px !important; background-color: #ffffff !important;
        }
        div[data-baseweb="base-input"]:focus-within {
            border: 1px solid #2b5876 !important; box-shadow: 0 0 0 2px rgba(43, 88, 118, 0.2);
        }

        .css-card {
            background-color: white; padding: 1rem 1.5rem; border-radius: 10px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.05); border: 1px solid #eef0f2;
            margin-top: -15px;
        }

        /* Match Counter Badge */
        .match-badge {
            background-color: #2b5876; color: white; padding: 5px 12px;
            border-radius: 20px; font-size: 0.9rem; font-weight: 500;
            white-space: nowrap; display: inline-block;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }

        section[data-testid="stSidebar"] { top: 60px !important; background-color: #f8f9fa; }
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
            
            # --- Search Bar & Count UI ---
            col_search, col_count = st.columns([4, 1])
            with col_search:
                search_query = st.text_input("", placeholder="🔍 พิมพ์คำค้นหา (ระบบจะ Highlight และกรองให้)...")
            
            match_count = 0
            if search_query:
                # Logic: กรองบรรทัด
                text1 = [line for line in text1 if search_query in line]
                text2 = [line for line in text2 if search_query in line]
                
                # Logic: นับจำนวนคำที่เจอ (รวมทั้ง 2 ฝั่ง)
                c1 = sum(line.count(search_query) for line in text1)
                c2 = sum(line.count(search_query) for line in text2)
                match_count = c1 + c2

            # แสดงจำนวนที่เจอตรงมุมขวา
            with col_count:
                if search_query:
                    if match_count > 0:
                        st.markdown(f"<div style='text-align:right; padding-top: 8px;'><span class='match-badge'>เจอ {match_count} จุด</span></div>", unsafe_allow_html=True)
                    else:
                        st.markdown(f"<div style='text-align:right; padding-top: 8px;'><span class='match-badge' style='background-color:#dc3545;'>ไม่พบข้อมูล</span></div>", unsafe_allow_html=True)

            # Generate HTML Diff
            comparator = TextComparator()
            html_code = comparator.generate_diff_html(text1, text2, mode=mode_key)

            # --- Result Card ---
            st.markdown('<div class="css-card">', unsafe_allow_html=True)
            
            # JavaScript สำหรับ Highlight คำค้นหา
            # เราจะส่ง search_query เข้าไปใน JS เพื่อให้มันไประบายสีพื้นหลัง text
            js_highlight = f"""
            <script>
                document.addEventListener("DOMContentLoaded", function() {{
                    var keyword = "{search_query}";
                    if (keyword && keyword.trim() !== "") {{
                        // ค้นหาเฉพาะใน tag <td> เพื่อไม่ให้กระทบ HTML structure
                        var cells = document.getElementsByTagName('td');
                        for (var i = 0; i < cells.length; i++) {{
                            var innerHTML = cells[i].innerHTML;
                            // ใช้ Regex เพื่อแทนที่คำด้วย span ที่มีสีพื้นหลัง
                            // flag 'g' = global (ทุกคำ), 'i' = case-insensitive (ถ้าต้องการ)
                            var regex = new RegExp(keyword, "g"); 
                            
                            // Highlight สีส้มสดใส (Orange) และตัวหนา
                            cells[i].innerHTML = innerHTML.replace(regex, "<span style='background-color: #ff9800; color: white; padding: 0 4px; border-radius: 4px; box-shadow: 0 1px 2px rgba(0,0,0,0.2);'>" + keyword + "</span>");
                        }}
                    }}
                }});
            </script>
            """

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
            
            # รวม JS + CSS + HTML
            final_html = js_highlight + iframe_style + html_code
            
            components.html(final_html, height=800, scrolling=True)
            st.markdown('</div>', unsafe_allow_html=True)

        except Exception as e:
            st.error(f"เกิดข้อผิดพลาด: {e}")

else:
    st.info("👈 กรุณาอัปโหลดไฟล์ที่เมนูด้านซ้ายเพื่อเริ่มเปรียบเทียบ")
