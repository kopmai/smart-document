import streamlit as st
from modules.loader import DocumentLoader
from modules.comparator import TextComparator
import streamlit.components.v1 as components

def render_document_compare_mode():
    # --- 1. ส่วนตั้งค่า (Expander) ---
    with st.expander("⚙️ ตั้งค่าและอัปโหลดไฟล์ (Settings & Upload)", expanded=True):
        
        # แบ่งคอลัมน์ซ้ายขวาสำหรับอัปโหลด
        col1, col2 = st.columns(2)
        
        with col1:
            file1 = st.file_uploader("📄 ไฟล์ต้นฉบับ (Original)", type=["docx", "pdf"], key="doc_file1")
        
        with col2:
            file2 = st.file_uploader("📄 ไฟล์ฉบับแก้ไข (Modified)", type=["docx", "pdf"], key="doc_file2")

        st.markdown("---")
        
        # ตัวเลือกโหมด (วางแนวนอนให้สวยงาม)
        col_mode, _ = st.columns([1, 2])
        with col_mode:
            view_mode = st.radio(
                "มุมมอง (View Mode)", 
                ["แสดงทั้งหมด", "เฉพาะจุดต่าง"], 
                index=0, 
                horizontal=True,
                key="doc_view_mode"
            )
            mode_key = "diff_only" if view_mode == "เฉพาะจุดต่าง" else "all"

        # เช็คสถานะไฟล์
        ready_to_process = file1 is not None and file2 is not None

    # --- 2. ส่วนประมวลผลและแสดงผล ---
    if ready_to_process:
        # ใช้ Spinner ระหว่างโหลด (เผื่อไฟล์ใหญ่)
        with st.spinner('⏳ กำลังอ่านและเปรียบเทียบเอกสาร...'):
            try:
                # 1. Load Text
                type1 = file1.name.split('.')[-1].lower()
                type2 = file2.name.split('.')[-1].lower()
                
                text1 = DocumentLoader.extract_text(file1, type1)
                text2 = DocumentLoader.extract_text(file2, type2)
                
                # --- ส่วน Search Filter (ย้ายมาอยู่เหนือผลลัพธ์) ---
                st.markdown("### 🔍 ผลการเปรียบเทียบ (Comparison Result)")
                
                col_search, col_count = st.columns([4, 1])
                with col_search:
                    search_query = st.text_input("", placeholder="🔍 พิมพ์คำค้นหาเพื่อกรองเฉพาะบรรทัดที่เกี่ยวข้อง...", key="doc_search")
                
                # Logic การค้นหาและนับจำนวน
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

                # 2. Compare
                comparator = TextComparator()
                # ถ้ามีการค้นหา ให้บังคับโหมด all เพื่อไม่ให้ diff ซ่อนผลลัพธ์
                current_mode = "all" if search_query else mode_key
                
                raw_html = comparator.generate_diff_html(text1, text2, mode=current_mode)
                final_html = comparator.get_final_display_html(raw_html, search_query)

                # 3. Display
                st.markdown('<div class="css-card">', unsafe_allow_html=True)
                components.html(final_html, height=800, scrolling=True)
                st.markdown('</div>', unsafe_allow_html=True)

            except Exception as e:
                st.error(f"เกิดข้อผิดพลาด: {e}")
    else:
        # หน้าจอว่างๆ (Empty State)
        st.info("👈 กรุณาอัปโหลดไฟล์ทั้ง 2 ฝั่งในกล่องตั้งค่าด้านบน เพื่อเริ่มเปรียบเทียบ")
