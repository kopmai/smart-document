import streamlit as st
from modules.utils import get_logs_dataframe, set_api_key, get_api_key

def render_settings_page():
    st.markdown("## ⚙️ ตั้งค่าและประวัติการใช้งาน (Settings & Logs)")
    
    tab_settings, tab_logs = st.tabs(["🔑 ตั้งค่าระบบ (Settings)", "📜 ประวัติการใช้งาน (History Logs)"])
    
    # === TAB 1: SETTINGS ===
    with tab_settings:
        st.info("ตั้งค่าครั้งเดียว ใช้ได้ทุกโมดูลในระบบ")
        
        current_key = get_api_key()
        new_key = st.text_input("🔑 Gemini API Key (Global)", value=current_key, type="password")
        
        if new_key != current_key:
            set_api_key(new_key)
            st.success("✅ บันทึก API Key เรียบร้อยแล้ว (ไปหน้าอื่นได้เลย)")
            
        st.markdown("---")
        st.caption("เวอร์ชันระบบ: Smart Document v1.2 (Beta)")

    # === TAB 2: LOGS ===
    with tab_logs:
        st.markdown("### 📊 บันทึกกิจกรรม (Session Activity)")
        
        df = get_logs_dataframe()
        
        if not df.empty:
            # สรุปสถิติเล็กๆ
            col1, col2, col3 = st.columns(3)
            col1.metric("ทำรายการไปแล้ว", f"{len(df)} ครั้ง")
            col2.metric("ล่าสุดเมื่อ", df.iloc[0]['Timestamp'].split(' ')[1])
            col3.metric("สถานะล่าสุด", df.iloc[0]['Status'])
            
            # ตาราง Log
            st.dataframe(df, use_container_width=True, hide_index=True)
            
            # ปุ่ม Download CSV
            csv = df.to_csv(index=False).encode('utf-8')
            st.download_button(
                "📥 ดาวน์โหลดประวัติ (CSV)",
                csv,
                "smart_doc_logs.csv",
                "text/csv",
                key='download-csv'
            )
        else:
            st.info("ยังไม่มีประวัติการใช้งานในรอบนี้")
