import streamlit as st
from modules.comparator import TextComparator
import streamlit.components.v1 as components

def clear_code_inputs():
    """ฟังก์ชันสำหรับล้างค่าในช่องกรอกโค้ด"""
    st.session_state["code_input_1"] = ""
    st.session_state["code_input_2"] = ""

def move_modified_to_original():
    """ฟังก์ชันย้ายโค้ดจากช่อง Modified ไปใส่ Original และเคลียร์ช่อง Modified"""
    st.session_state["code_input_1"] = st.session_state["code_input_2"]
    st.session_state["code_input_2"] = ""

def render_code_compare_mode(mode_key):
    """
    ฟังก์ชันสำหรับแสดงผลหน้าจอเปรียบเทียบ Source Code
    """
    
    # --- 1. ส่วนตั้งค่าและใส่โค้ด (Expander) ---
    with st.expander("⚙️ ใส่โค้ดเพื่อเปรียบเทียบ (Input Code)", expanded=True):
        
        # Layout ช่องกรอกข้อมูล
        col_input1, col_input2 = st.columns(2)
        
        with col_input1:
            st.markdown("👇 **Original Code**")
            code1_raw = st.text_area("Original Code", height=300, 
                                     label_visibility="collapsed", 
                                     placeholder="วางโค้ดต้นฉบับที่นี่...",
                                     key="code_input_1")
        
        with col_input2:
            st.markdown("👇 **Modified Code**")
            code2_raw = st.text_area("Modified Code", height=300, 
                                     label_visibility="collapsed", 
                                     placeholder="วางโค้ดใหม่ที่นี่...",
                                     key="code_input_2")

        st.markdown("---")

        # กลุ่มปุ่มกด
        col_btn_compare, col_btn_shift, col_btn_clear = st.columns([3, 2, 1])
        
        with col_btn_compare:
            run_compare = st.button("🚀 เปรียบเทียบ (Compare)", type="primary", use_container_width=True)
            
        with col_btn_shift:
            st.button("⬅️ ใช้เป็นต้นฉบับใหม่", 
                      help="ย้ายโค้ดจากช่อง Modified ไปใส่ Original เพื่อเปรียบเทียบต่อ",
                      use_container_width=True, 
                      on_click=move_modified_to_original)
        
        with col_btn_clear:
            st.button("🧹 ล้างค่า", use_container_width=True, on_click=clear_code_inputs)

    # --- 2. ส่วนแสดงผล (Outside Expander) ---
    if run_compare:
        if code1_raw or code2_raw:
            
            st.markdown("### 🔍 ผลลัพธ์ (Diff Result)")
            
            with st.spinner('⏳ กำลังประมวลผลโค้ด...'):
                text1 = code1_raw.splitlines()
                text2 = code2_raw.splitlines()

                # UI Search Logic
                col_search, col_count = st.columns([4, 1])
                with col_search:
                    search_query = st.text_input("", placeholder="🔍 พิมพ์คำค้นหาในโค้ด...", key="code_search")
                
                match_count = 0
                if search_query:
                    match_count = sum(line.count(search_query) for line in text1) + sum(line.count(search_query) for line in text2)
                
                with col_count:
                    if search_query:
                        badge_color = "#0d6efd" if match_count > 0 else "#dc3545"
                        msg = f"เจอ {match_count} จุด" if match_count > 0 else "ไม่พบข้อมูล"
                        st.markdown(f"<div style='text-align:right; padding-top: 8px;'><span class='match-badge' style='background-color:{badge_color};'>{msg}</span></div>", unsafe_allow_html=True)

                # Process
                comparator = TextComparator()
                current_mode = "all" if search_query else mode_key
                
                raw_html = comparator.generate_diff_html(text1, text2, mode=current_mode)
                final_html = comparator.get_final_display_html(raw_html, search_query)

                # Output
                st.markdown('<div class="css-card">', unsafe_allow_html=True)
                components.html(final_html, height=800, scrolling=True)
                st.markdown('</div>', unsafe_allow_html=True)
        else:
            st.warning("กรุณาวางโค้ดอย่างน้อย 1 ฝั่งเพื่อเปรียบเทียบ")
            
    elif not run_compare:
        st.info("👈 วางโค้ดในกล่องด้านบน แล้วกดปุ่ม 'เปรียบเทียบ'")
