import streamlit as st
import google.generativeai as genai
import fitz  # PyMuPDF
from PIL import Image
import io

def get_available_models(api_key):
    """ดึงรายชื่อโมเดล (ต้องเป็นตัวที่รองรับ Vision ได้ด้วย)"""
    try:
        genai.configure(api_key=api_key)
        all_models = []
        for m in genai.list_models():
            # เช็คว่ารองรับการ generateContent ไหม
            if 'generateContent' in m.supported_generation_methods:
                all_models.append(m.name)
        return all_models
    except:
        return []

def perform_ocr(api_key, image, model_name):
    """ส่งรูปภาพไปให้ AI แกะข้อความ"""
    try:
        genai.configure(api_key=api_key)
        
        # ตั้งค่าความปลอดภัย
        safety_settings = [
            {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
        ]
        
        model = genai.GenerativeModel(model_name, safety_settings=safety_settings)
        
        # Prompt สั่งงาน
        prompt = """
        Analyze this image and extract all text content visible in it.
        - Preserve the original layout and structure as much as possible.
        - If there are tables, try to represent them clearly.
        - If the text is in Thai, ensure accurate Thai character recognition.
        - Output ONLY the extracted text.
        """
        
        # ส่งทั้ง Prompt และ รูปภาพ ไปพร้อมกัน
        response = model.generate_content([prompt, image], stream=True)
        
        full_text = ""
        for chunk in response:
            if chunk.text:
                full_text += chunk.text
                yield chunk.text # ส่งค่ากลับแบบ Stream
                
    except Exception as e:
        yield f"Error: {str(e)}"

def render_ocr_mode():
    # แบ่งหน้าจอ ซ้าย(Input) | ขวา(Output)
    col_left, col_right = st.columns([1, 1])
    
    with col_left:
        st.markdown("### 1. ตั้งค่าและอัปโหลด (Setup)")
        
        # --- ส่วน Key และเลือก Model (เหมือนโมดูลอื่น) ---
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
                selected_model = st.selectbox("🤖 เลือก AI Model (ต้องรองรับรูปภาพ)", model_options, index=default_idx)
        # -----------------------------------------------
        
        st.markdown("---")
        
        # อัปโหลดไฟล์ PDF
        uploaded_file = st.file_uploader("📄 อัปโหลดไฟล์ PDF ที่นี่", type=["pdf"])
        
        pil_image = None # ตัวแปรเก็บรูปภาพที่จะส่งให้ AI
        
        if uploaded_file:
            # ใช้ PyMuPDF แปลง PDF เป็นรูปภาพเพื่อโชว์ Preview
            doc = fitz.open(stream=uploaded_file.read(), filetype="pdf")
            total_pages = len(doc)
            
            # ถ้ามีหลายหน้า ให้เลือกหน้าได้
            page_num = st.number_input(f"เลือกหน้า (จากทั้งหมด {total_pages} หน้า)", min_value=1, max_value=total_pages, value=1)
            
            # แปลงหน้านั้นเป็นรูป
            page = doc.load_page(page_num - 1) 
            pix = page.get_pixmap(dpi=150) # แปลงเป็น Pixmap
            pil_image = Image.open(io.BytesIO(pix.tobytes())) # แปลงเป็น PIL Image
            
            # แสดง Preview
            st.markdown(f"**👁️ ตัวอย่างเอกสาร (หน้า {page_num}):**")
            st.image(pil_image, use_container_width=True, caption=f"Preview Page {page_num}")
            
            # ปุ่มกด Start OCR
            btn_ocr = st.button("🔍 แปลงภาพเป็นข้อความ (Start AI OCR)", type="primary", use_container_width=True, disabled=(not api_key or not pil_image))

    with col_right:
        st.markdown("### 2. ผลลัพธ์ (Extracted Text)")
        
        # สร้างพื้นที่รอผลลัพธ์
        output_box = st.empty()
        
        if uploaded_file and pil_image and 'btn_ocr' in locals() and btn_ocr:
            
            full_extracted_text = ""
            output_box.text_area("ผลลัพธ์", "🤖 AI กำลังสแกนเอกสาร...", height=600)
            
            try:
                # เรียกใช้งานแบบ Stream
                stream_generator = perform_ocr(api_key, pil_image, selected_model)
                
                for chunk in stream_generator:
                    full_extracted_text += chunk
                    # อัปเดตข้อความสดๆ
                    output_box.text_area("ผลลัพธ์", full_extracted_text, height=600)
                
                # เสร็จแล้ว
                st.success("✅ OCR เสร็จเรียบร้อย!")
                
            except Exception as e:
                st.error(f"เกิดข้อผิดพลาด: {e}")
        
        elif not uploaded_file:
            st.info("👈 กรุณาอัปโหลดไฟล์ PDF ทางด้านซ้าย")
        elif uploaded_file and not btn_ocr:
            st.info("👈 กดปุ่ม 'Start AI OCR' เพื่อเริ่มทำงาน")
