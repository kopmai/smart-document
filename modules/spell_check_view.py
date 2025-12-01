import streamlit as st
import google.generativeai as genai
from modules.comparator import TextComparator

def get_ai_correction(api_key, text):
    """ส่งข้อความไปให้ Gemini ช่วยแก้คำผิด (พร้อมปิด Safety Filter)"""
    try:
        genai.configure(api_key=api_key)
        
        # ตั้งค่า Safety ให้เป็น BLOCK_NONE (ยอมรับทุกเนื้อหา) 
        # เพื่อป้องกัน Error เวลาตรวจคำผิดที่มีคำหยาบหรือเรื่องละเอียดอ่อน
        safety_settings = [
            {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
        ]
        
        # ใช้โมเดล gemini-1.5-flash (เสถียรและเร็วสุด ณ ตอนนี้)
        model = genai.GenerativeModel('gemini-1.5-flash', safety_settings=safety_settings)
        
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
        # ดักจับ Error ทุกอย่างแล้วส่งกลับไปบอก User
        return f"Error: {str(e)}"

def render_spell_check_mode():
    col_setup, col_result = st.columns([1, 1])
    
    with col_setup:
        st.markdown("### 1. ใส่เนื้อหา (Input)")
        
        # แสดงเวอร์ชันไลบรารีเพื่อเช็คความชัวร์
        try:
            st.caption(f"System Info: google-generativeai v{genai.__version__}")
        except:
            pass

        api_key = None
        if "GEMINI_API_KEY" in st.secrets:
            api_key = st.secrets["GEMINI_API_KEY"]
            st.success("✅ เชื่อมต่อกับ API Key อัตโนมัติแล้ว")
        else:
            api_key = st.text_input("🔑 Gemini API Key", type="password", help="รับ Key ฟรีได้ที่ aistudio.google.com")

        st.markdown("---")
        text_input = st.text_area("✍️ ต้นฉบับ (Original Text)", height=400, placeholder="วางข้อความที่ต้องการตรวจทานที่นี่...")
        
        btn_check = st.button("✨ ให้ AI ตรวจทาน (AI Proofread)", type="primary", use_container_width=True, disabled=(not api_key or not text_input))

        # --- ส่วน Debug (กดเมื่อ Error) ---
        with st.expander("🛠️ Debug API Key (กดเมื่อ Error)"):
            if st.button("Test List Models"):
                if api_key:
                    try:
                        genai.configure(api_key=api_key)
                        st.write("🔍 กำลังค้นหาโมเดล...")
                        found_models = []
                        for m in genai.list_models():
                            # กรองเอาเฉพาะรุ่นที่ generateContent ได้
                            if 'generateContent' in m.supported_generation_methods:
                                found_models.append(m.name)
                                st.code(m.name)
                        
                        if not found_models:
                            st.error("❌ Key นี้เชื่อมต่อได้ แต่มองไม่เห็นโมเดลเลย (อาจเป็นที่สิทธิ์ของ Key)")
                        else:
                            st.success(f"✅ พบ {len(found_models)} โมเดล (Key ใช้ได้ปกติ)")
                            
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
                    st.error("เกิดข้อผิดพลาดในการเชื่อมต่อ AI:")
                    st.error(corrected_text)
                    st.info("คำแนะนำ: ลองกดปุ่ม Debug API Key ด้านซ้ายเพื่อเช็คสถานะ")
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
                    
                    with st.expander("📄 ดูข้อความที่แก้แล้ว (Plain Text)"):
                        st.code(corrected_text, language=None)
