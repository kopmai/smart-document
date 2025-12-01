import streamlit as st
import google.generativeai as genai
import fitz  # PyMuPDF
from PIL import Image
import io
from docx import Document

def get_available_models(api_key):
    try:
        genai.configure(api_key=api_key)
        all_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        return all_models
    except:
        return []

def ocr_single_image(api_key, image, model_name):
    """ส่งรูปภาพ 1 รูป ไปให้ AI แกะข้อความ"""
    try:
        genai.configure(api_key=api_key)
        safety_settings = [
            {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
        ]
        model = genai.GenerativeModel(model_name, safety_settings=safety_settings)
        
        prompt = """
        Extract all text from this image perfectly.
        - Preserve the layout (paragraphs, tables) as much as possible.
        - If Thai text is present, ensure correct spelling.
        - Return ONLY the content, no conversational text.
        """
        response = model.generate_content([prompt, image])
        return response.text
    except Exception as e:
        return f"[Error on this page: {str(e)}]"

def create_word_docx(text_list):
    """สร้างไฟล์ Word จากรายการข้อความ"""
    doc = Document()
    doc.add_heading('OCR Result - Smart Document', 0)
    
    for i, text in enumerate(text_list):
        doc.add_heading(f'Page {i+1}', level=1)
        doc.add_paragraph(text)
        doc.add_page_break()
        
    buffer = io.BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    return buffer

def render_ocr_mode():
    # --- FIX: ย้าย Session State Init มาไว้ในฟังก์ชัน (รับประกันว่าทำงานชัวร์) ---
    if 'ocr_results' not in st.session_state:
        st.session_state['ocr_results'] = [] 
    if 'ocr_images' not in st.session_state:
        st.session_state['ocr_images'] = []
    if 'current_page_index' not in st.session_state:
        st.session_state['current_page_index'] = 0
    if 'processed_file_id' not in st.session_state:
        st.session_state['processed_file_id'] = None
    # -----------------------------------------------------------------------

    # 1. ส่วนตั้งค่า (Top Expander)
    with st.expander("⚙️ ตั้งค่าและอัปโหลดไฟล์ (Settings & Upload)", expanded=True):
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
                    selected_model = st.selectbox("🤖 เลือก AI Model", model_options, index=default_idx)

        uploaded_file = st.file_uploader("📄 อัปโหลดไฟล์ PDF (ระบบจะอ่านทุกหน้า)", type=["pdf"])

        # ปุ่มเริ่มทำงาน (Start)
        if uploaded_file and api_key and selected_model:
            # เช็คว่าไฟล์เปลี่ยนใหม่ไหม
            if st.session_state['processed_file_id'] != uploaded_file.file_id:
                st.session_state['ocr_results'] = []
                st.session_state['ocr_images'] = []
                st.session_state['current_page_index'] = 0
                st.session_state['processed_file_id'] = None 

            if st.button("🚀 เริ่มประมวลผล (Start Processing All Pages)", type="primary"):
                
                # Step A: แปลง PDF เป็นรูป
                with st.spinner("📦 กำลังแยกหน้า PDF เป็นรูปภาพ..."):
                    doc = fitz.open(stream=uploaded_file.read(), filetype="pdf")
                    temp_images = []
                    for page_num in range(len(doc)):
                        page = doc.load_page(page_num)
                        pix = page.get_pixmap(dpi=150)
                        img = Image.open(io.BytesIO(pix.tobytes()))
                        temp_images.append(img)
                    
                    st.session_state['ocr_images'] = temp_images
                    st.session_state['ocr_results'] = [""] * len(temp_images)
                    st.session_state['processed_file_id'] = uploaded_file.file_id

                # Step B: OCR ทีละหน้า
                progress_bar = st.progress(0, text="กำลังเริ่ม OCR...")
                total_pages = len(st.session_state['ocr_images'])
                
                for i, img in enumerate(st.session_state['ocr_images']):
                    progress_bar.progress((i) / total_pages, text=f"🔍 กำลังอ่านหน้า {i+1}/{total_pages}...")
                    text_result = ocr_single_image(api_key, img, selected_model)
                    st.session_state['ocr_results'][i] = text_result
                
                progress_bar.progress(1.0, text="เสร็จเรียบร้อย!")
                st.rerun()

    # 2. ส่วนแสดงผล (Synced View)
    # ใช้ .get() เพื่อป้องกัน KeyError หรือเช็คว่ามีค่าไหม
    if st.session_state.get('processed_file_id') and st.session_state.get('ocr_results'):
        
        st.markdown("---")
        
        total_pages = len(st.session_state['ocr_images'])
        col_prev, col_nav_info, col_next = st.columns([1, 4, 1])
        
        with col_prev:
            if st.button("⬅️ หน้าก่อนหน้า", use_container_width=True, disabled=(st.session_state['current_page_index'] == 0)):
                st.session_state['current_page_index'] -= 1
                st.rerun()

        with col_nav_info:
            st.markdown(f"<h4 style='text-align: center;'>📄 หน้า {st.session_state['current_page_index'] + 1} จาก {total_pages}</h4>", unsafe_allow_html=True)

        with col_next:
            if st.button("หน้าถัดไป ➡️", use_container_width=True, disabled=(st.session_state['current_page_index'] == total_pages - 1)):
                st.session_state['current_page_index'] += 1
                st.rerun()

        col_left_view, col_right_view = st.columns([1, 1])
        curr_idx = st.session_state['current_page_index']
        
        with col_left_view:
            st.info("👁️ ต้นฉบับ (PDF Preview)")
            if curr_idx < len(st.session_state['ocr_images']):
                st.image(st.session_state['ocr_images'][curr_idx], use_container_width=True, caption=f"Page {curr_idx+1}")

        with col_right_view:
            st.success("📝 ผลลัพธ์ (Editable Text)")
            if curr_idx < len(st.session_state['ocr_results']):
                edited_text = st.text_area(
                    label="ocr_output",
                    value=st.session_state['ocr_results'][curr_idx],
                    height=600,
                    label_visibility="collapsed",
                    key=f"text_area_{curr_idx}"
                )
                st.session_state['ocr_results'][curr_idx] = edited_text

        st.markdown("---")
        col_export, _ = st.columns([1, 3])
        with col_export:
            docx_file = create_word_docx(st.session_state['ocr_results'])
            st.download_button(
                label="💾 ดาวน์โหลดเป็น Word (.docx)",
                data=docx_file,
                file_name="ocr_result.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                type="primary",
                use_container_width=True
            )
