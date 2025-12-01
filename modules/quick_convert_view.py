import streamlit as st
import google.generativeai as genai
import fitz  # PyMuPDF
from PIL import Image
import io
from docx import Document
import re

def get_available_models(api_key):
    """ดึงรายชื่อโมเดลที่ใช้ได้จริง (ไม่มโน)"""
    try:
        genai.configure(api_key=api_key)
        all_models = []
        for m in genai.list_models():
            # เอาเฉพาะตัวที่รองรับ Vision (Generate Content)
            if 'generateContent' in m.supported_generation_methods:
                all_models.append(m.name)
        return all_models
    except:
        return []

def clean_ocr_text(text):
    """ล้างเส้นตารางออก"""
    if not text: return ""
    lines = text.split('\n')
    cleaned_lines = []
    for line in lines:
        if re.match(r'^[\s\|\-\_\=\:\+]{3,}$', line.strip()):
            continue
        cleaned_lines.append(line)
    return '\n'.join(cleaned_lines)

def process_page_to_text(api_key, image, model_name):
    """ส่งรูปให้ AI แกะข้อความ"""
    try:
        genai.configure(api_key=api_key)
        safety_settings = [
            {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
        ]
        model = genai.GenerativeModel(model_name, safety_settings=safety_settings)
        
        # Prompt: เน้นอ่านจากภาพ ไม่สน Text layer
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
    st.caption("เหมาะสำหรับไฟล์ PDF ที่ก๊อปวางแล้วเป็นภาษาต่างดาว ระบบจะใช้ AI อ่านจากภาพโดยตรงแล้วแปลงเป็น Word ให้ทันที")

    # --- 1. Compact Settings ---
    with st.container():
        col_key, col_model = st.columns([1, 1])
        with col_key:
            api_key = None
            if "GEMINI_API_KEY" in st.secrets:
                api_key = st.secrets["GEMINI_API_KEY"]
                st.success("✅ API Key Connected")
            else:
                api_key = st.text_input("🔑 Gemini API Key", type="password")
        
        with col_model:
            # --- FIX: ใช้ Dynamic Model Selection (ไม่ Hardcode แล้ว) ---
            selected_model = None
            if api_key:
                model_options = get_available_models(api_key)
                if model_options:
                    # พยายามเลือกตัวที่มี flash หรือ pro เป็นค่าเริ่มต้น
                    default_idx = 0
                    for i, name in enumerate(model_options):
                        if "flash" in name and "exp" not in name:
                            default_idx = i; break
                        elif "gemini-pro" in name and "exp" not in name:
                            default_idx = i
                    
                    selected_model = st.selectbox("🤖 AI Model (เลือกตัวที่ใช้ได้)", model_options, index=default_idx)
                else:
                    st.error("❌ ไม่พบโมเดล")
            else:
                st.info("กรุณาใส่ Key เพื่อโหลดรายชื่อโมเดล")

    st.markdown("---")

    # --- 2. Upload Zone ---
    uploaded_file = st.file_uploader("วางไฟล์ PDF ที่มีปัญหาตรงนี้ (Drag & Drop)", type=["pdf"])

    if uploaded_file and api_key and selected_model:
        
        if st.button("🚀 แปลงเป็น Word เดี๋ยวนี้ (Convert Now)", type="primary", use_container_width=True):
            
            progress_bar = st.progress(0, text="กำลังเตรียมไฟล์...")
            
            try:
                doc = fitz.open(stream=uploaded_file.read(), filetype="pdf")
                total_pages = len(doc)
                extracted_texts = []

                for i in range(total_pages):
                    progress_bar.progress((i / total_pages), text=f"⏳ กำลังแปลงหน้า {i+1} จาก {total_pages}...")
                    
                    page = doc.load_page(i)
                    pix = page.get_pixmap(dpi=150)
                    img = Image.open(io.BytesIO(pix.tobytes()))
                    
                    # ส่ง model ที่เลือกมาจริงๆ เข้าไป
                    text_result = process_page_to_text(api_key, img, selected_model)
                    extracted_texts.append(text_result)

                progress_bar.progress(0.9, text="💾 กำลังสร้างไฟล์ Word...")
                docx_file = create_doc_from_results(extracted_texts)
                
                progress_bar.progress(1.0, text="✅ เสร็จเรียบร้อย!")
                st.balloons()
                
                st.success(f"แปลงไฟล์ {uploaded_file.name} สำเร็จ! ({total_pages} หน้า)")
                
                st.download_button(
                    label="📥 คลิกเพื่อดาวน์โหลดไฟล์ Word (.docx)",
                    data=docx_file,
                    file_name=f"fixed_{uploaded_file.name}.docx",
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                    type="primary",
                    use_container_width=True
                )

            except Exception as e:
                st.error(f"เกิดข้อผิดพลาด: {e}")
