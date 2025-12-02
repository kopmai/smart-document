import streamlit as st
import google.generativeai as genai
import fitz  # PyMuPDF
from PIL import Image
import io
from docx import Document
import re
import pandas as pd # เพิ่ม Pandas สำหรับจัดการ Excel

def get_available_models(api_key):
    try:
        genai.configure(api_key=api_key)
        all_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        return all_models
    except:
        return []

def clean_ocr_text(text):
    if not text: return ""
    # ลบพวก Markdown code block ออก (เผื่อ AI เผลอใส่มา)
    text = text.replace("```csv", "").replace("```", "")
    return text.strip()

def process_page_ai(api_key, image, model_name, output_format="text"):
    """
    ฟังก์ชันส่งรูปให้ AI แกะข้อความ
    output_format: 'text' (Word) หรือ 'csv' (Excel)
    """
    try:
        genai.configure(api_key=api_key)
        safety_settings = [
            {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
        ]
        model = genai.GenerativeModel(model_name, safety_settings=safety_settings)
        
        if output_format == "csv":
            # Prompt สำหรับ Excel (ขอ CSV)
            prompt = """
            Act as a Data Entry Clerk. 
            Extract the table data from this image perfectly.
            - Output STRICTLY in CSV format (Comma Separated Values).
            - Do NOT use Markdown code blocks. Just raw CSV data.
            - Handle Thai characters correctly.
            - If there are merged cells, repeat the value in each cell or handle logically.
            """
        else:
            # Prompt สำหรับ Word (ขอ Text)
            prompt = """
            You are a high-speed OCR engine. 
            Convert this document image into plain text.
            - IGNORE any underlying text layer. READ VISUALLY.
            - Preserve the original layout (paragraphs/lists).
            - Thai Language accuracy is top priority.
            """
        
        response = model.generate_content([prompt, image])
        return clean_ocr_text(response.text)
    except Exception as e:
        return f"Error: {str(e)}"

def create_doc_from_results(results):
    """สร้าง Word จาก List ของข้อความ"""
    doc = Document()
    for text in results:
        doc.add_paragraph(text)
        doc.add_page_break()
    buffer = io.BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    return buffer

def create_excel_from_results(csv_results):
    """สร้าง Excel จาก List ของ CSV String (แยก Sheet ตามหน้า)"""
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
        has_data = False
        for i, csv_text in enumerate(csv_results):
            if not csv_text or "Error" in csv_text: continue
            
            try:
                # แปลง CSV String เป็น DataFrame
                df = pd.read_csv(io.StringIO(csv_text))
                sheet_name = f"Page_{i+1}"
                df.to_excel(writer, sheet_name=sheet_name, index=False)
                has_data = True
            except:
                # กรณีแปลง CSV ไม่ผ่าน (AI อาจตอบมาไม่ดี) ให้ข้าม
                pass
                
        if not has_data: # กัน Error กรณีไม่มีข้อมูลเลย
            pd.DataFrame({"Message": ["No valid table data found"]}).to_excel(writer, sheet_name="Error")
            
    buffer.seek(0)
    return buffer

def render_quick_convert_mode():
    
    # --- FIX: ย้าย Tabs เข้าไปใน Expander ---
    with st.expander("⚙️ แผงควบคุม (Control Panel)", expanded=True):
        
        # 1. Global Settings
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
                        elif "gemini-pro" in name and "exp" not in name:
                            default_idx = i
                    selected_model = st.selectbox("🤖 เลือก AI Model", model_options, index=default_idx)

        # 2. Upload Zone
        uploaded_file = st.file_uploader("วางไฟล์ PDF ที่มีปัญหาตรงนี้ (Drag & Drop)", type=["pdf"])

        if uploaded_file and api_key and selected_model:
            st.markdown("---")
            
            # 3. Selection Tabs (อยู่ใน Expander แล้ว!)
            tab_batch, tab_select = st.tabs(["🚀 แปลงทั้งหมด (Batch Word)", "👁️ เลือกหน้า & แยกตาราง (Custom)"])
            
            # === TAB 1: BATCH (เน้นเร็ว เป็น Word หมด) ===
            with tab_batch:
                st.info("ℹ️ แปลงทุกหน้าเป็น Word รวดเดียว (เหมาะกับเอกสารข้อความล้วน)")
                if st.button("🚀 เริ่มแปลงเป็น Word ทั้งหมด", type="primary", use_container_width=True):
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
                            # Batch Mode = Text Only
                            text_result = process_page_ai(api_key, img, selected_model, output_format="text")
                            extracted_texts.append(text_result)

                        progress_bar.progress(1.0, text="✅ เสร็จเรียบร้อย! (ผลลัพธ์อยู่ด้านล่าง)")
                        
                        # Save to session state
                        st.session_state['qf_word_result'] = create_doc_from_results(extracted_texts)
                        st.session_state['qf_excel_result'] = None # Clear Excel
                        st.session_state['qf_filename'] = uploaded_file.name
                        
                    except Exception as e:
                        st.error(f"เกิดข้อผิดพลาด: {e}")

            # === TAB 2: SELECTIVE (เลือกได้ว่าเป็น Text หรือ Table) ===
            with tab_select:
                st.info("ℹ️ ติ๊กเลือกหน้า และระบุได้ว่าหน้านั้นเป็น 'ตาราง (Excel)' หรือ 'ข้อความ (Word)'")
                
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

                # Grid Selection with Options
                with st.form("qf_select_form"):
                    images = st.session_state['qf_preview_images']
                    cols = st.columns(4)
                    
                    # เก็บสถานะการเลือก (ใช้ Dictionary)
                    selection_map = {} 
                    
                    for i, img in enumerate(images):
                        col = cols[i % 4]
                        with col:
                            st.image(img, use_container_width=True)
                            
                            # Checkbox หลัก (เลือกหน้านี้ไหม)
                            is_selected = st.checkbox(f"เลือกหน้า {i+1}", key=f"qf_sel_{i}")
                            
                            # Checkbox รอง (เป็นตารางไหม) -> แสดงเฉพาะถ้าเลือกหน้าหลัก (แต่ Streamlit ทำ dynamic ใน form ยาก เลยโชว์ตลอด)
                            is_table = st.toggle(f"เป็นตาราง (Excel)?", key=f"qf_tbl_{i}", help="ถ้าเปิด จะแปลงหน้านี้เป็น Excel")
                            
                            if is_selected:
                                selection_map[i] = "csv" if is_table else "text"
                    
                    st.markdown("---")
                    submitted = st.form_submit_button("✅ เริ่มแปลงตามที่เลือก", type="primary", use_container_width=True)

                if submitted:
                    if not selection_map:
                        st.warning("กรุณาเลือกอย่างน้อย 1 หน้า")
                    else:
                        progress_bar = st.progress(0, text="กำลังเตรียมไฟล์...")
                        try:
                            doc = fitz.open(stream=uploaded_file.read(), filetype="pdf")
                            
                            word_texts = []
                            excel_csvs = []
                            
                            total_selected = len(selection_map)
                            current_step = 0

                            # วนลูปตามหน้าที่เลือก
                            for page_idx, mode in sorted(selection_map.items()):
                                current_step += 1
                                progress_bar.progress((current_step / total_selected), text=f"⏳ กำลังแปลงหน้า {page_idx+1} (โหมด {mode})...")
                                
                                page = doc.load_page(page_idx)
                                pix = page.get_pixmap(dpi=150)
                                img = Image.open(io.BytesIO(pix.tobytes()))
                                
                                result = process_page_ai(api_key, img, selected_model, output_format=mode)
                                
                                if mode == "text":
                                    word_texts.append(result)
                                else:
                                    excel_csvs.append(result)

                            progress_bar.progress(1.0, text="✅ เสร็จเรียบร้อย! (ผลลัพธ์อยู่ด้านล่าง)")
                            
                            # เตรียมไฟล์ผลลัพธ์ (อาจมีทั้งคู่ หรืออย่างใดอย่างหนึ่ง)
                            st.session_state['qf_word_result'] = create_doc_from_results(word_texts) if word_texts else None
                            st.session_state['qf_excel_result'] = create_excel_from_results(excel_csvs) if excel_csvs else None
                            st.session_state['qf_filename'] = uploaded_file.name
                            
                        except Exception as e:
                            st.error(f"เกิดข้อผิดพลาด: {e}")

    # 3. Download Buttons (อยู่นอก Expander) - แสดงตามผลลัพธ์ที่มี
    if 'qf_filename' in st.session_state:
        st.markdown("### 📥 ดาวน์โหลดผลลัพธ์")
        
        col_d1, col_d2 = st.columns(2)
        
        has_result = False
        
        # ปุ่มโหลด Word
        if st.session_state.get('qf_word_result'):
            with col_d1:
                st.download_button(
                    label="📄 ดาวน์โหลด Word (.docx)",
                    data=st.session_state['qf_word_result'],
                    file_name=f"fixed_{st.session_state['qf_filename']}.docx",
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                    type="primary",
                    use_container_width=True
                )
                has_result = True

        # ปุ่มโหลด Excel
        if st.session_state.get('qf_excel_result'):
            with col_d2:
                st.download_button(
                    label="📊 ดาวน์โหลด Excel (.xlsx)",
                    data=st.session_state['qf_excel_result'],
                    file_name=f"tables_{st.session_state['qf_filename']}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    type="secondary", # ใช้สีต่างกันจะได้ไม่งง
                    use_container_width=True
                )
                has_result = True
                
        if has_result:
            st.success("เรียบร้อย! คุณสามารถพับกล่องด้านบนเก็บเพื่อดูปุ่มโหลดได้ชัดๆ ครับ")
