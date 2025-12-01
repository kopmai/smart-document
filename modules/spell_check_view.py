import streamlit as st
import google.generativeai as genai
from modules.comparator import TextComparator

def get_best_available_model(api_key):
    """ฟังก์ชันค้นหาโมเดลที่ดีที่สุดที่มีให้ใช้ใน Key นี้"""
    try:
        genai.configure(api_key=api_key)
        
        # 1. ดึงรายชื่อโมเดลทั้งหมดที่ Key นี้มองเห็น
        all_models = [m for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        model_names = [m.name for m in all_models]
        
        # --- FIX: ปรับลำดับความสำคัญใหม่ (เอาตัวเสถียรและฟรีเยอะๆ ขึ้นก่อน) ---
        preferred_list = [
            'models/gemini-1.5-flash',          # <--- ตัวนี้เร็วและโควต้าฟรีเยอะสุด (แนะนำ!)
            'models/gemini-1.5-flash-latest',
            'models/gemini-1.5-pro',            # <--- ตัวนี้ฉลาดแต่ช้ากว่า
            'models/gemini-1.5-pro-latest',
            'models/gemini-1.0-pro',
            'models/gemini-pro',
            # พวก Experimental เอาไว้ท้ายสุด เพราะมักจะ Limit 0
            'models/gemini-2.5-pro-exp', 
            'models/gemini-exp-1206'
        ]
        # ------------------------------------------------------------------
        
        # 3. วนหา: ถ้าเจอตัวไหนในลิสต์ ก็เอาตัวนั้นเลย
        for preferred in preferred_list:
            if preferred in model_names:
                return preferred
        
        # 4. ถ้าไม่เจอตัวที่อยากได้เลย... เอาตัวแรกสุดที่มีให้ใช้ (กันตาย)
        if model_names:
            return model_names[0]
            
        return None
        
    except Exception as e:
        return None

def get_ai_correction(api_key, text, model_name):
    """ส่งข้อความไปให้ Gemini (ใช้โมเดลที่หามาได้)"""
    try:
        genai.configure(api_key=api_key)
        
        # ปิด Safety Filter
        safety_settings = [
            {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
        ]
        
        model = genai.GenerativeModel(model_name, safety_settings=safety_settings)
        
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
        # ดักจับ Error 429 (Quota Exceeded) แล้วแจ้งเตือนให้ชัดเจน
        if "429" in str(e):
            return "Error 429: โควต้าการใช้งานเกินลิมิต (Quota Exceeded) กรุณารอสักครู่แล้วลองใหม่ หรือเปลี่ยน API Key"
        return f"Error: {str(e)}"

def render_spell_check_mode():
    col_setup, col_result = st.columns([1, 1])
    
    with col_setup:
        st.markdown("### 1. ใส่เนื้อหา (Input)")
        
        try:
            st.caption(f"Lib Version: {genai.__version__}")
        except: pass

        api_key = None
        if "GEMINI_API_KEY" in st.secrets:
            api_key = st.secrets["GEMINI_API_KEY"]
            st.success("✅ เชื่อมต่อกับ API Key อัตโนมัติแล้ว")
        else:
            api_key = st.text_input("🔑 Gemini API Key", type="password")

        st.markdown("---")
        text_input = st.text_area("✍️ ต้นฉบับ (Original Text)", height=400, placeholder="วางข้อความที่ต้องการตรวจทานที่นี่...")
        
        btn_check = st.button("✨ ให้ AI ตรวจทาน (Auto-Detect Model)", type="primary", use_container_width=True, disabled=(not api_key or not text_input))

    with col_result:
        st.markdown("### 2. ผลการตรวจทาน (AI Suggestion)")

        if btn_check and api_key and text_input:
            with st.spinner("🤖 ระบบกำลังเลือกโมเดลที่เหมาะสมและเริ่มตรวจทาน..."):
                
                # --- STEP 1: หาโมเดลก่อน ---
                best_model = get_best_available_model(api_key)
                
                if not best_model:
                    st.error("❌ ไม่พบโมเดลที่ใช้งานได้ใน Key นี้")
                else:
                    st.info(f"⚡ กำลังใช้งานโมเดล: `{best_model}`") 
                    
                    # --- STEP 2: เริ่มแก้คำผิด ---
                    corrected_text = get_ai_correction(api_key, text_input, best_model)

                    if "Error" in corrected_text:
                        st.error("เกิดข้อผิดพลาดในการเชื่อมต่อ AI:")
                        st.error(corrected_text)
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
