import streamlit as st
import re
from pythainlp import word_tokenize
from pythainlp.spell import correct as thai_correct
from pythainlp.spell import spell as thai_suggest
from spellchecker import SpellChecker

# โหลด Dictionary อังกฤษเตรียมไว้ (จะได้ไม่ต้องโหลดใหม่ทุกครั้ง)
eng_spell = SpellChecker()

def is_thai(word):
    """เช็คว่าเป็นคำไทยหรือไม่"""
    return re.search(r'[\u0E00-\u0E7F]', word)

def highlight_errors(text):
    """
    ฟังก์ชันหลัก: ตัดคำ -> ตรวจคำผิด -> สร้าง HTML Highlight
    Return: (HTML String, List ของคำผิดและคำแนะนำ)
    """
    if not text.strip():
        return "", []

    # 1. ตัดคำ (ใช้ Engine ของ PyThaiNLP ตัดผสมคำไทย/อังกฤษได้เลย)
    words = word_tokenize(text, engine="newmm")
    
    processed_html = ""
    error_list = []
    
    for word in words:
        clean_word = word.strip()
        
        # ข้ามพวกตัวเลข หรือสัญลักษณ์
        if not clean_word or clean_word.isnumeric() or len(clean_word) <= 1:
            processed_html += word
            continue

        is_error = False
        suggestion = ""

        # --- ตรวจคำไทย ---
        if is_thai(clean_word):
            # ลองแก้คำผิดดู ถ้าแก้แล้วไม่เหมือนเดิม แสดงว่าผิด
            corrected = thai_correct(clean_word)
            if corrected != clean_word:
                is_error = True
                suggestion = corrected
        
        # --- ตรวจคำอังกฤษ ---
        elif re.match(r'^[a-zA-Z]+$', clean_word):
            # spellchecker จะคืนค่าเป็น set ถ้าคำถูกจะคืนค่าว่างหรือหาไม่เจอ
            if clean_word.lower() not in eng_spell:
                is_error = True
                suggestion = eng_spell.correction(clean_word)

        # --- สร้าง HTML ---
        if is_error:
            # Highlight สีแดงอ่อนๆ + Tooltip
            span = f'<span style="background-color: #ffcccc; border-bottom: 2px solid red; cursor: help;" title="แนะนำ: {suggestion}">{word}</span>'
            processed_html += span
            error_list.append({"wrong": word, "suggest": suggestion})
        else:
            processed_html += word

    # Wrap ด้วย div ให้สวยงาม
    final_html = f"""
    <div style="font-family: 'Kanit'; font-size: 16px; line-height: 1.8; color: #333; background: white; padding: 20px; border-radius: 10px; border: 1px solid #ddd;">
        {processed_html}
    </div>
    """
    return final_html, error_list

def render_spell_check_mode():
    col_input, col_result = st.columns([1, 1])
    
    with col_input:
        st.markdown("### ✍️ ต้นฉบับ (Input Text)")
        text_input = st.text_area("วางข้อความที่นี่...", height=500, label_visibility="collapsed", placeholder="วางข้อความภาษาไทย หรือ ภาษาอังกฤษ ที่ต้องการตรวจทาน...")

    with col_result:
        st.markdown("### 🔍 ผลการตรวจสอบ (Result)")
        
        if text_input:
            with st.spinner("กำลังตรวจคำผิด..."):
                html_output, errors = highlight_errors(text_input)
                
                # แสดงจำนวนคำผิด
                if errors:
                    st.error(f"พบคำที่น่าจะผิด {len(errors)} จุด")
                else:
                    st.success("ไม่พบคำผิด (หรือระบบอาจจะไม่รู้จัก)")

                # แสดงเนื้อหาที่ Highlight (ใช้ st.markdown แสดง HTML)
                st.markdown(html_output, unsafe_allow_html=True)
                
                # แสดงตารางสรุปคำผิดด้านล่าง
                if errors:
                    st.markdown("---")
                    st.markdown("**💡 รายการคำแนะนำ**")
                    
                    # จัดรูปแบบแสดงผลคำแนะนำ
                    for err in list(set([tuple(d.items()) for d in errors])): # remove duplicates logic
                        err_dict = dict(err)
                        st.markdown(f"- ❌ **{err_dict['wrong']}** → ✅ `{err_dict['suggest']}`")
        else:
            st.info("รอรับข้อความ...")
