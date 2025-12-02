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

def ocr_single_image(api_key, image, model_name):
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
        - If there is a table, preserve the data structure but DO NOT print ASCII borders or Markdown divider lines (like |---|). 
        - Just use spacing or tabs to separate columns if possible.
        - If Thai text is present, ensure correct spelling.
        """
        response = model.generate_content([prompt, image])
        final_text = clean_ocr_text(response.text)
        return final_text
    except Exception as e:
        return f"[Error on this page: {str(e)}]"

def create_word_docx(text_list):
    doc = Document()
    for i, text in enumerate(text_list):
        doc.add_heading(f'Page {i+1}', level=1)
        doc.add_paragraph(text)
        doc.add_page_break()
    buffer = io.BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    return buffer

def render_ocr_mode():
    # --- Session State ---
    if 'ocr_results' not in st.session_state: st.session_state['ocr_results'] = [] 
    if 'ocr_images' not in st.session_state: st.session_state['ocr_images'] = []
    if 'current_page_index' not in st.session_state: st.session_state['current_page_index'] = 0
    if 'processed_file_id' not in st.session_state: st.session_state['processed_file_id'] = None

    # --- FIX: ย้ายทุกอย่างเข้าไปใน Expander ใหญ่ (Control Panel) ---
    with st.expander("🛠️ แผงควบคุม: ตั้งค่า / อัปโหลด / เลือกหน้า (Control Panel)", expanded=True):
        
        # 1. Settings
        col_key, col_model = st.columns([1, 1])
        with col_key:
            api_key = None
            if "GEMINI_API_KEY" in st.secrets:
                api_key = st.secrets["GEMINI_API_KEY"]
                st.success("✅ API Key Connected")
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

        # 2. Upload
        uploaded_file = st.file_uploader("📄 อัปโหลดไฟล์ PDF (AI OCR)", type=["pdf"])

        # 3. Processing Tabs
        if uploaded_file and api_key and selected_model:
            st.markdown("---")
            # Tabs อยู่ใน Expander แล้ว ไม่กินที่ข้างล่าง
            tab_batch, tab_select = st.tabs(["🚀 แปลงทั้งหมด (Batch)", "👁️ เลือกเฉพาะหน้า (Selective)"])

            # === TAB 1: BATCH ===
            with tab_batch:
                st.info("ℹ️ อ่านเอกสารรวดเดียวทุกหน้า")
                if st.button("🚀 เริ่ม OCR ทุกหน้า", type="primary", use_container_width=True):
                    # Reset Data
                    st.session_state['ocr_results'] = []
                    st.session_state['ocr_images'] = []
                    st.session_state['current_page_index'] = 0
                    st.session_state['processed_file_id'] = uploaded_file.file_id

                    with st.spinner("📦 กำลังแยกหน้า PDF..."):
                        doc = fitz.open(stream=uploaded_file.read(), filetype="pdf")
                        temp_images = []
                        for page_num in range(len(doc)):
                            page = doc.load_page(page_num)
                            pix = page.get_pixmap(dpi=150)
                            img = Image.open(io.BytesIO(pix.tobytes()))
                            temp_images.append(img)
                        st.session_state['ocr_images'] = temp_images
                        st.session_state['ocr_results'] = [""] * len(temp_images)

                    progress_bar = st.progress(0, text="กำลังเริ่ม OCR...")
                    total_pages = len(st.session_state['ocr_images'])
                    for i, img in enumerate(st.session_state['ocr_images']):
                        progress_bar.progress((i) / total_pages, text=f"🔍 กำลังอ่านหน้า {i+1}/{total_pages}...")
                        text_result = ocr_single_image(api_key, img, selected_model)
                        st.session_state['ocr_results'][i] = text_result
                    progress_bar.progress(1.0, text="เสร็จเรียบร้อย! (พับกล่องนี้เก็บเพื่อดูผลลัพธ์ได้เลย)")
                    st.rerun()

            # === TAB 2: SELECTIVE ===
            with tab_select:
                st.info("ℹ️ เลือกเฉพาะหน้าที่ต้องการใช้งาน")
                # Preview Gen
                if 'ocr_preview_imgs' not in st.session_state or st.session_state.get('ocr_preview_fid') != uploaded_file.file_id:
                    with st.spinner("🖼️ สร้างภาพตัวอย่าง..."):
                        doc = fitz.open(stream=uploaded_file.read(), filetype="pdf")
                        previews = []
                        for i in range(len(doc)):
                            page = doc.load_page(i)
                            pix = page.get_pixmap(dpi=72)
                            img = Image.open(io.BytesIO(pix.tobytes()))
                            previews.append(img)
                        st.session_state['ocr_preview_imgs'] = previews
                        st.session_state['ocr_preview_fid'] = uploaded_file.file_id

                # Grid Selection
                with st.form("ocr_select_form"):
                    images = st.session_state['ocr_preview_imgs']
                    cols = st.columns(4)
                    selected_indices = []
                    for i, img in enumerate(images):
                        col = cols[i % 4]
                        with col:
                            st.image(img, use_container_width=True)
                            if st.checkbox(f"หน้า {i+1}", key=f"ocr_chk_{i}"):
                                selected_indices.append(i)
                    
                    st.markdown("---")
                    submitted = st.form_submit_button("✅ เริ่ม OCR เฉพาะหน้าที่เลือก", type="primary", use_container_width=True)

                if submitted:
                    if not selected_indices:
                        st.warning("กรุณาเลือกอย่างน้อย 1 หน้า")
                    else:
                        st.session_state['ocr_results'] = []
                        st.session_state['ocr_images'] = []
                        st.session_state['current_page_index'] = 0
                        st.session_state['processed_file_id'] = uploaded_file.file_id
                        
                        selected_indices.sort()
                        progress_bar = st.progress(0, text="เริ่มทำงาน...")
                        
                        doc = fitz.open(stream=uploaded_file.read(), filetype="pdf")
                        total_sel = len(selected_indices)
                        
                        for idx, page_num in enumerate(selected_indices):
                            progress_bar.progress((idx / total_sel), text=f"🔍 กำลังอ่านหน้า {page_num+1} ({idx+1}/{total_sel})...")
                            
                            page = doc.load_page(page_num)
                            pix = page.get_pixmap(dpi=150)
                            img = Image.open(io.BytesIO(pix.tobytes()))
                            
                            st.session_state['ocr_images'].append(img)
                            text_res = ocr_single_image(api_key, img, selected_model)
                            st.session_state['ocr_results'].append(text_res)
                        
                        progress_bar.progress(1.0, text="เสร็จเรียบร้อย! (พับกล่องนี้เก็บเพื่อดูผลลัพธ์ได้เลย)")
                        st.rerun()

    # 2. ส่วนแสดงผล (อยู่นอก Expander)
    # ตรงนี้จะโชว์เด่นๆ เลย ไม่ต้องเลื่อนหา
    if st.session_state.get('processed_file_id') == uploaded_file.file_id if uploaded_file else False:
        if st.session_state.get('ocr_results'):
            
            st.markdown("### 📄 ผลลัพธ์ (Result)") # หัวข้อชัดเจน
            
            total_pages = len(st.session_state['ocr_images'])
            
            # Controller
            col_prev, col_nav_info, col_next, col_download = st.columns([1, 2, 1, 1.5])
            with col_prev:
                if st.button("⬅️ ก่อนหน้า", use_container_width=True, disabled=(st.session_state['current_page_index'] == 0)):
                    st.session_state['current_page_index'] -= 1
                    st.rerun()
            with col_nav_info:
                st.markdown(f"<div style='text-align: center; padding-top: 5px; font-weight: bold;'>หน้า {st.session_state['current_page_index'] + 1} / {total_pages}</div>", unsafe_allow_html=True)
            with col_next:
                if st.button("ถัดไป ➡️", use_container_width=True, disabled=(st.session_state['current_page_index'] == total_pages - 1)):
                    st.session_state['current_page_index'] += 1
                    st.rerun()
            with col_download:
                docx_file = create_word_docx(st.session_state['ocr_results'])
                st.download_button(
                    label="💾 Export Word",
                    data=docx_file,
                    file_name="ocr_result.docx",
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                    type="primary",
                    use_container_width=True
                )

            st.markdown("<br>", unsafe_allow_html=True)
            col_left_view, col_right_view = st.columns([1, 1])
            curr_idx = st.session_state['current_page_index']
            
            with col_left_view:
                st.info("👁️ ต้นฉบับ")
                if curr_idx < len(st.session_state['ocr_images']):
                    st.image(st.session_state['ocr_images'][curr_idx], use_container_width=True)

            with col_right_view:
                st.success("📝 ข้อความที่ได้")
                if curr_idx < len(st.session_state['ocr_results']):
                    edited_text = st.text_area(
                        label="ocr_output",
                        value=st.session_state['ocr_results'][curr_idx],
                        height=800,
                        label_visibility="collapsed",
                        key=f"text_area_{curr_idx}"
                    )
                    st.session_state['ocr_results'][curr_idx] = edited_text
