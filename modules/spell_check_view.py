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

def get_ai_correction_stream(api_key, text, model_name, progress_bar, stream_box):
    try:
        genai.configure(api_key=api_key)
        
        # ปิด Safety Filter (เพื่อให้รับข้อความได้ทุกรูปแบบ)
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
        
        response = model.generate_content(prompt, stream=True)
        
        full_text = ""
        total_len = len(text) if len(text) > 0 else 1
        
        for chunk in response:
            if chunk.text:
                chunk_text = chunk.text
                full_text += chunk_text
                
                # Update UI
                current_len = len(full_text)
                progress = min(current_len / total_len, 0.99)
                progress_bar.progress(progress, text=f"🤖 AI กำลังพิมพ์... ({int(progress*100)}%)")
                
                # Live Preview
                stream_box.markdown(
                    f"""
                    <div style="background-color: #f0f2f6; padding: 15px; border-radius: 8px; font-family: monospace; color: #333; font-size: 0.9rem; height: 200px; overflow-y: auto; border: 1px dashed #ccc;">
                        {full_text}
                    </div>
                    """, 
                    unsafe_allow_html=True
                )

        progress_bar.progress(1.0, text="เสร็จเรียบร้อย!")
        return full_text.strip()
        
    except Exception as e:
        if "429" in str(e):
            return "API_ERROR: โควต้าเต็ม (Quota Exceeded)"
        return f"API_ERROR: {str(e)}"

def render_spell_check_mode():
    col_setup, col_result = st.columns([1, 1])
    
    # --- ส่วนตั้งค่า (อยู่นอก Form เพราะต้องการให้ Update ทันที) ---
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
                        default_idx = i; break
                    elif "gemini-pro" in name and "exp" not in name:
                        default_idx = i
                selected_model = st.selectbox("🤖 เลือก AI Model", model_options, index=default_idx)
            else:
                st.error("❌ ไม่พบโมเดล")

    # --- ส่วนฟอร์มรับข้อมูล (ใช้ st.form แก้ปัญหา Ctrl+Enter) ---
    with col_setup:
        st.markdown("---")
        # เริ่มต้น Form
        with st.form(key="spell_check_form"):
            st.markdown("👇 **วางข้อความต้นฉบับที่นี่**")
            text_input = st.text_area(
                "Original Text", 
                height=300, 
                placeholder="วางข้อความภาษาไทย หรืออังกฤษ...",
                label_visibility="collapsed"
            )
            
            # ปุ่ม Submit (กดปุ๊บ ทำงานปั๊บ ไม่ต้อง Ctrl+Enter)
            submit_btn = st.form_submit_button(
                label="✨ เริ่มตรวจทาน (Start Proofread)", 
                type="primary", 
                use_container_width=True,
                disabled=(not api_key) # ถ้าไม่มี Key ปุ่มจะกดไม่ได้
            )

    # --- ส่วนแสดงผล ---
    with col_result:
        st.markdown("### 2. ผลการตรวจทาน (AI Suggestion)")

        if submit_btn and api_key and text_input and selected_model:
            
            st.caption("🚀 สถานะการทำงาน:")
            progress_bar = st.progress(0, text="กำลังเชื่อมต่อ AI...")
            stream_box = st.empty()
            
            try:
                corrected_text = get_ai_correction_stream(api_key, text_input, selected_model, progress_bar, stream_box)
                
                stream_box.empty() 
                progress_bar.empty()

                if corrected_text.startswith("API_ERROR:"):
                    st.error("เกิดข้อผิดพลาด:")
                    st.error(corrected_text.replace("API_ERROR:", ""))
                else:
                    original_lines = text_input.splitlines()
                    corrected_lines = corrected_text.splitlines()

                    comparator = TextComparator()
                    raw_html = comparator.generate_diff_html(original_lines, corrected_lines, mode="all")
                    final_html = comparator.get_final_display_html(raw_html)

                    # 1. แสดง Diff View
                    st.success("✅ เปรียบเทียบจุดแก้ (Diff View)")
                    st.markdown('<div class="css-card">', unsafe_allow_html=True)
                    import streamlit.components.v1 as components
                    components.html(final_html, height=500, scrolling=True)
                    st.markdown('</div>', unsafe_allow_html=True)
                    
                    st.markdown("---")
                    
                    # 2. แสดงกล่องข้อความใหญ่ๆ (ตามที่ขอ)
                    st.markdown("### 📝 ข้อความที่แก้ไขแล้ว (Final Text)")
                    st.text_area(
                        label="ก๊อปปี้ไปใช้ได้เลย", 
                        value=corrected_text, 
                        height=400  # จัดให้ใหญ่สะใจ
                    )
                    
                    # 3. ปุ่ม Copy (ใช้ st.code ช่วย เพราะมันมีปุ่ม Copy ในตัว)
                    st.info("💡 หรือกดปุ่ม Copy ที่มุมขวาบนของกล่องด้านล่างนี้ 👇")
                    st.code(corrected_text, language=None)
                        
            except Exception as e:
                st.error(f"เกิดข้อผิดพลาด: {e}")
        
        elif not submit_btn:
            # หน้าจอว่างๆ ตอนยังไม่กดปุ่ม
            st.info("👈 กรอกข้อความด้านซ้าย แล้วกดปุ่ม 'เริ่มตรวจทาน'")
