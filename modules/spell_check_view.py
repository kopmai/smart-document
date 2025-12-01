import streamlit as st
import google.generativeai as genai
from modules.comparator import TextComparator

def get_ai_correction(api_key, text):
    try:
        genai.configure(api_key=api_key)
        # ลองใช้ Flash เหมือนเดิม (เพราะไลบรารีเราใหม่แล้ว)
        model = genai.GenerativeModel('gemini-2.5-flash')
        
        prompt = f"""
        Act as a professional proofreader. 
        Please correct the spelling, grammar, and punctuation errors in the following text (Thai and English).
        Maintain the original tone and style. 
        RETURN ONLY THE CORRECTED TEXT without any explanation or markdown formatting.
        
        Text to correct:
        {text}
        """
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        return f"Error: {str(e)}"

def render_spell_check_mode():
    col_setup, col_result = st.columns([1, 1])
    
    with col_setup:
        st.markdown("### 1. ใส่เนื้อหา (Input)")
        st.caption(f"System Info: google-generativeai v{genai.__version__}")

        api_key = None
        if "GEMINI_API_KEY" in st.secrets:
            api_key = st.secrets["GEMINI_API_KEY"]
            st.success("✅ เชื่อมต่อกับ API Key อัตโนมัติแล้ว")
        else:
            api_key = st.text_input("🔑 Gemini API Key", type="password", help="รับ Key ฟรีได้ที่ aistudio.google.com")
        
        st.markdown("---")
        text_input = st.text_area("✍️ ต้นฉบับ (Original Text)", height=400, placeholder="วางข้อความที่ต้องการตรวจทานที่นี่...")
        btn_check = st.button("✨ ให้ AI ตรวจทาน (AI Proofread)", type="primary", use_container_width=True, disabled=(not api_key or not text_input))

        # --- เพิ่มส่วน Debug ---
        with st.expander("🛠️ Debug API Key (กดเมื่อ Error)"):
            if st.button("Test List Models"):
                if api_key:
                    try:
                        genai.configure(api_key=api_key)
                        st.write("โมเดลที่ Key นี้มองเห็น:")
                        found_models = []
                        for m in genai.list_models():
                            found_models.append(m.name)
                            st.code(m.name)
                        if not found_models:
                            st.error("❌ Key นี้มองไม่เห็นโมเดลใดๆ เลย (กรุณาสร้าง Key ใหม่)")
                    except Exception as e:
                        st.error(f"❌ Key นี้ใช้ไม่ได้: {e}")
                else:
                    st.warning("ใส่ Key ก่อนกด Test")
        # --------------------

    with col_result:
        st.markdown("### 2. ผลการตรวจทาน (AI Suggestion)")
        
        if btn_check and api_key and text_input:
            with st.spinner("🤖 AI กำลังอ่านและแก้ไขประโยค..."):
                corrected_text = get_ai_correction(api_key, text_input)
                
                if "Error:" in corrected_text:
                    st.error(corrected_text)
                    st.warning("คำแนะนำ: ลองกดที่ 'Debug API Key' ด้านซ้ายดูครับ ถ้าไม่เจอชื่อ models/gemini-1.5-flash แสดงว่า Key นี้ใช้ไม่ได้")
                else:
                    original_lines = text_input.splitlines()
                    corrected_lines = corrected_text.splitlines()
                    
                    comparator = TextComparator()
                    raw_html = comparator.generate_diff_html(original_lines, corrected_lines, mode="all")
                    final_html = comparator.get_final_display_html(raw_html)
                    
                    st.success("✅ ตรวจเสร็จเรียบร้อย!")
                    st.markdown('<div class="css-card">', unsafe_allow_html=True)
                    import streamlit.components.v1 as components
                    components.html(final_html, height=600, scrolling=True)
                    st.markdown('</div>', unsafe_allow_html=True)
