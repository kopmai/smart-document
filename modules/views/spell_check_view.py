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
        
        response = model.generate_content(prompt, stream=True)
        
        full_text = ""
        total_len = len(text) if len(text) > 0 else 1
        
        for chunk in response:
            if chunk.text:
                full_text += chunk.text
                
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
    
    # --- 1. Global Settings & Input (Expander) ---
    with st.expander("⚙️ ตั้งค่าและใส่เนื้อหา (Settings & Input)", expanded=True):
        col_key, col_model = st.columns([1, 1])
        
        with col_key:
            api_key = None
            if "GEMINI_API_KEY" in st.secrets:
                api_key = st.secrets["GEMINI_API_KEY"]
                st.success("✅ เชื่อมต่อกับ API Key อัตโนมัติแล้ว")
            else:
                api_key = st.text_input("🔑 Gemini API Key", type="password")

        with col_model:
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

        st.markdown("---")
        
        # Form สำหรับกรอกข้อความ (อยู่ใน Expander เลย)
        with st.form(key="spell_check_form"):
            text_input = st.text_area(
                "👇 วางข้อความต้นฉบับที่นี่ (Original Text)", 
                height=200, 
                placeholder="วางข้อความภาษาไทย หรืออังกฤษ...",
            )
            
            submit_btn = st.form_submit_button(
                label="✨ เริ่มตรวจทาน (Start Proofread)", 
                type="primary", 
                use_container_width=True,
                disabled=(not api_key)
            )

    # --- 2. ส่วนแสดงผล (Outside Expander) ---
    if submit_btn and api_key and text_input and selected_model:
        
        st.markdown("### 📝 ผลการตรวจทาน (AI Suggestion)")
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

                # 1. Diff View
                st.info("👁️ เปรียบเทียบจุดแก้ (Diff View)")
                st.markdown('<div class="css-card">', unsafe_allow_html=True)
                import streamlit.components.v1 as components
                components.html(final_html, height=500, scrolling=True)
                st.markdown('</div>', unsafe_allow_html=True)
                
                st.markdown("---")
                
                # 2. Final Text Box
                st.success("✅ ข้อความที่แก้ไขแล้ว (Final Text)")
                st.text_area(
                    label="Final Text", 
                    value=corrected_text, 
                    height=300,
                    label_visibility="collapsed"
                )
                
                st.caption("💡 กดปุ่ม Copy มุมขวาบนของกล่องด้านล่าง 👇")
                st.code(corrected_text, language=None)
                    
        except Exception as e:
            st.error(f"เกิดข้อผิดพลาด: {e}")
            
    elif not submit_btn:
        st.info("👈 กรอกข้อความในกล่องตั้งค่าด้านบน แล้วกดปุ่ม 'เริ่มตรวจทาน'")
