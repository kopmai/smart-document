# ... imports เดิม ...
from modules.utils import log_event, get_api_key # <--- 1. เพิ่ม Import นี้

# ... functions เดิม ...

def render_quick_convert_mode():
    st.markdown("## ⚡ แก้ PDF เพี้ยนเป็น Word (Quick Fix)")
    # ...

    with st.expander("⚙️ ตั้งค่า (Settings)", expanded=True):
        col_key, col_model = st.columns([1, 1])
        with col_key:
            # --- 2. แก้ตรงรับ Key ให้ดึงจาก Global ---
            global_key = get_api_key()
            if global_key:
                api_key = global_key
                st.success("✅ ใช้ Global API Key")
            else:
                api_key = st.text_input("🔑 Gemini API Key", type="password")
            # -------------------------------------
        
        # ... (ส่วนเลือกโมเดลเหมือนเดิม) ...

    # ... (ส่วน Upload เหมือนเดิม) ...

    if uploaded_file and api_key and selected_model:
        # ... (ส่วน Tabs เหมือนเดิม) ...
        
        # === TAB 1: BATCH ===
        with tab_all:
            # ...
            if st.button("🚀 เริ่มแปลงทุกหน้า (Convert All)", ...):
                # ... (Process เดิม) ...
                try:
                    # ... (Loop Process) ...

                    # --- 3. แทรก Log เมื่อทำงานสำเร็จ ---
                    log_event("Quick Fix (Batch)", f"แปลงไฟล์ {uploaded_file.name} ({total_pages} หน้า)", "Success")
                    # ---------------------------------

                    progress_bar.progress(1.0, text="✅ เสร็จเรียบร้อย!")
                    # ... (ส่วนสร้างปุ่ม Download) ...
                    
                except Exception as e:
                    # --- 4. แทรก Log เมื่อ Error ---
                    log_event("Quick Fix (Batch)", f"Error: {uploaded_file.name}", "Failed")
                    # ----------------------------
                    st.error(f"เกิดข้อผิดพลาด: {e}")
