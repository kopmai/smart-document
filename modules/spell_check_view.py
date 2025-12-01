import streamlit as st
import google.generativeai as genai
from modules.comparator import TextComparator

def get_available_models(api_key):
    """ดึงรายชื่อโมเดลทั้งหมดที่ Key นี้ใช้ได้จริง"""
    try:
        genai.configure(api_key=api_key)
        all_models = []
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                all_models.append(m.name)
        return all_models
    except:
        return []

def get_ai_correction_stream(api_key, text, model_name, progress_bar=None, status_box=None):
    try:
        genai.configure(api_key=api_key)
        
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
        
        # --- FIX: ใช้โหมด stream=True เพื่อให้รับข้อมูลทีละนิด ---
        response = model.generate_content(prompt, stream=True)
        
        full_text = ""
        total_len = len(text) # ความยาวคร่าวๆ ของต้นฉบับ
        
        for chunk in response:
            if chunk.text:
                full_text += chunk.text
                
                # คำนวณ % คร่าวๆ (เทียบความยาวที่ได้ กับความยาวต้นฉบับ)
                # ปกติแก้คำผิด ความยาวจะไม่ต่างจากเดิมมาก
                if progress_bar:
                    current_len = len(full_text)
                    # สูตรคำนวณ: เอาความยาวที่ได้ / ความยาวต้นฉบับ (Max 95% เผื่อไว้ตอนจบ)
                    progress = min(current_len / total_len, 0.95)
                    progress_bar.progress(progress)
                    
                if status_box:
                    status_box.caption(f"🤖 AI กำลังเขียน... (ได้มาแล้ว {len(full_text)} ตัวอักษร)")

        # จบแล้วปรับเป็น 100%
        if progress_bar:
            progress_bar.progress(1.0)
            
        return full_text.strip()
        
    except Exception as e:
        if "429" in str(e):
            return "API_ERROR: โควต้าเต็ม (Quota Exceeded) กรุณาเปลี่ยนโมเดล"
        return f"API_ERROR: {str(e)}"

def render_spell_check_mode():
    col_setup, col_result = st.columns([1, 1])
    
    with col_setup:
        st.markdown("### 1. ตั้งค่า (Settings)")
        
        api_key = None
        if "GEMINI_API_KEY" in st.secrets:
            api_key = st.secrets["GEMINI_API_KEY"]
            st.success("✅ เชื่อมต่อกับ API Key อัตโนมัติแล้ว")
        else:
            api_key = st.text_input("🔑 Gemini API Key", type="password")

        selected_model = None
        if api_key:
            model_options = get_available_models(api_key)
            if model_options:
                default_idx = 0
                for i, name in enumerate(model_options):
                    if "flash" in name and "exp" not in name:
                        default_idx = i
                        break
                    elif "gemini-pro" in name and "exp" not in name:
                        default_idx = i
                selected_model = st.selectbox("🤖 เลือก AI Model", model_options, index=default_idx)
            else:
                st.error("❌ ไม่พบโมเดล")
        
        st.markdown("---")
        text_input = st.text_area("✍️ ต้นฉบับ (Original Text)", height=400, placeholder="วางข้อความที่ต้องการตรวจทานที่นี่...")
        
        btn_check = st.button("✨ เริ่มตรวจทาน (Start)", type="primary", use_container_width=True, disabled=(not api_key or not text_input or not selected_model))

    with col_result:
        st.markdown("### 2. ผลการตรวจทาน (AI Suggestion)")

        if btn_check and api_key and text_input and selected_model:
            
            # --- ส่วนแสดง Progress Bar ---
            progress_bar = st.progress(0, text="กำลังเตรียมการ...")
            status_box = st.empty() # กล่องข้อความเล็กๆ ใต้หลอดโหลด
            
            try:
                # เรียกฟังก์ชันแบบ Stream
                corrected_text = get_ai_correction_stream(api_key, text_input, selected_model, progress_bar, status_box)
                
                # โหลดเสร็จแล้ว ล้างหลอดทิ้ง เพื่อความสะอาดตา
                progress_bar.empty()
                status_box.empty()

                if corrected_text.startswith("API_ERROR:"):
                    st.error("เกิดข้อผิดพลาดในการเชื่อมต่อ AI:")
                    st.error(corrected_text.replace("API_ERROR:", ""))
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
            except Exception as e:
                st.error(f"เกิดข้อผิดพลาดที่ไม่คาดคิด: {e}")
