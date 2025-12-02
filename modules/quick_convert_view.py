import streamlit as st
import google.generativeai as genai
import fitz  # PyMuPDF
from PIL import Image
import io
from docx import Document
import re

def get_available_models(api_key):
    try:
        genai.configure(api_key=api_key)
        all_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        return all_models
    except:
        return []

def clean_ocr_text(text):
    if not text: return ""
    lines = text.split('\n')
    cleaned_lines = []
    for line in lines:
        if re.match(r'^[\s\|\-\_\=\:\+]{3,}$', line.strip()):
            continue
        cleaned_lines.append(line)
    return '\n'.join(cleaned_lines)

def process_page_to_text(api_key, image, model_name):
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
        You are a high-speed OCR engine. 
        Convert this document image into plain text.
        - IGNORE any underlying text layer (it might be corrupted). READ VISUALLY.
        - Preserve the original layout (paragraphs/lists).
        - If there are tables, keep the data structure clean (use tabs/spacing).
        - Thai Language accuracy is top priority.
        """
        
        response = model.generate_content([prompt, image])
        return clean_ocr_text(response.text)
    except Exception as e:
        return f"[Error Page: {str(e)}]"

def create_doc_from_results(results):
    doc = Document()
    for text in results:
        doc.add_paragraph(text)
        doc.add_page_break()
    buffer = io.BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    return buffer

def render_quick_convert_mode():
    st.markdown("## ⚡ แก้ PDF เพี้ยนเป็น Word (Quick Fix)")
    st.caption("แปลงไฟล์ PDF ที่ก๊อปวางแล้วเป็นภาษาต่างดาว ให้เป็น Word โดยใช้วิธีอ่านจากภาพ (Vision OCR)")

    # 1. Global Settings
    with st.expander("⚙️ ตั้งค่า (Settings)", expanded=True):
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

    # 2. Upload Zone
    uploaded_file = st.file_uploader("วางไฟล์ PDF ที่มีปัญหาตรงนี้ (Quick Fix)", type=["pdf"])

    if uploaded_file and api_key and selected_model:
        
        # 3. Selection Tabs
        tab_all, tab_select = st.tabs(["🚀 แปลงทั้งหมด (Batch)", "👁️ เลือกเฉพาะหน้า (Selective)"])
        
        # === TAB 1: BATCH ===
        with tab_all:
            st.info("ℹ️ แปลงทั้งไฟล์รวดเดียว เหมาะสำหรับไฟล์เสียทั้งฉบับ")
            if st.button("🚀 เริ่มแปลงทุกหน้า (Convert All)", type="primary", use_container_width=True):
                progress_bar = st.progress(0, text="กำลังเตรียมไฟล์...")
                try:
                    doc = fitz.open(stream=uploaded_file.read(), filetype="pdf")
                    total_pages = len(doc)
                    extracted_texts = []

                    for i in range(total_pages):
                        progress_bar.progress((i / total_pages), text=f"⏳ กำลังแปลงหน้า {i+1}/{total_pages}...")
                        page = doc.load_page(i)
                        pix = page.get_pixmap(dpi=150)
                        img = Image.open(io.BytesIO(pix.tobytes()))
                        text_result = process_page_to_text(api_key, img, selected_model)
                        extracted_texts.append(text_result)

                    progress_bar.progress(1.0, text="✅ เสร็จเรียบร้อย!")
                    docx_file = create_doc_from_results(extracted_texts)
                    
                    st.success(f"แปลงไฟล์สำเร็จ! ({total_pages} หน้า)")
                    st.download_button(
                        label="📥 ดาวน์โหลดไฟล์ Word (.docx)",
                        data=docx_file,
                        file_name=f"fixed_all_{uploaded_file.name}.docx",
                        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                        type="primary",
                        use_container_width=True
                    )
                except Exception as e:
                    st.error(f"เกิดข้อผิดพลาด: {e}")

        # === TAB 2: SELECTIVE ===
        with tab_select:
            st.info("ℹ️ เลือกแปลงเฉพาะหน้าที่ต้องการ")
            
            # Preview Gen
            if 'qf_preview_images' not in st.session_state or st.session_state.get('qf_file_id') != uploaded_file.file_id:
                with st.spinner("🖼️ สร้างภาพตัวอย่าง..."):
                    doc = fitz.open(stream=uploaded_file.read(), filetype="pdf")
                    previews = []
                    for i in range(len(doc)):
                        page = doc.load_page(i)
                        pix = page.get_pixmap(dpi=72) 
                        img = Image.open(io.BytesIO(pix.tobytes()))
                        previews.append(img)
                    
                    st.session_state['qf_preview_images'] = previews
                    st.session_state['qf_file_id'] = uploaded_file.file_id

            # Grid Selection
            with st.form("qf_select_form"):
                images = st.session_state['qf_preview_images']
                cols = st.columns(4)
                selected_indices = []
                
                for i, img in enumerate(images):
                    col = cols[i % 4]
                    with col:
                        st.image(img, use_container_width=True)
                        if st.checkbox(f"หน้า {i+1}", key=f"qf_chk_{i}"):
                            selected_indices.append(i)
                
                st.markdown("---")
                submitted = st.form_submit_button("✅ แปลงเฉพาะหน้าที่เลือก", type="primary", use_container_width=True)

            if submitted:
                if not selected_indices:
                    st.warning("กรุณาเลือกอย่างน้อย 1 หน้า")
                else:
                    progress_bar = st.progress(0, text="กำลังเตรียมไฟล์...")
                    try:
                        doc = fitz.open(stream=uploaded_file.read(), filetype="pdf")
                        extracted_texts = []
                        total_selected = len(selected_indices)
                        selected_indices.sort()

                        for idx, page_num in enumerate(selected_indices):
                            progress_bar.progress((idx / total_selected), text=f"⏳ กำลังแปลงหน้า {page_num+1} ({idx+1}/{total_selected})...")
                            
                            page = doc.load_page(page_num)
                            pix = page.get_pixmap(dpi=150)
                            img = Image.open(io.BytesIO(pix.tobytes()))
                            
                            text_result = process_page_to_text(api_key, img, selected_model)
                            extracted_texts.append(text_result)

                        progress_bar.progress(1.0, text="✅ เสร็จเรียบร้อย!")
                        docx_file = create_doc_from_results(extracted_texts)
                        
                        st.success(f"แปลงไฟล์สำเร็จ! ({total_selected} หน้าที่เลือก)")
                        st.download_button(
                            label="📥 ดาวน์โหลดไฟล์ Word (Selected)",
                            data=docx_file,
                            file_name=f"fixed_selected_{uploaded_file.name}.docx",
                            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                            type="primary",
                            use_container_width=True
                        )
                    except Exception as e:
                        st.error(f"เกิดข้อผิดพลาด: {e}")
