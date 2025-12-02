import streamlit as st
from modules.utils import get_logs_dataframe

def render_settings_page():
    st.markdown("## 📜 ประวัติการใช้งาน (History Logs)")
    st.caption("บันทึกกิจกรรมต่างๆ ที่เกิดขึ้นในระบบ (Session Log)")
    
    # ดึงข้อมูล Log
    df = get_logs_dataframe()
    
    if not df.empty:
        # 1. สรุปสถิติ (Metrics)
        st.markdown("---")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("📝 ทำรายการไปแล้ว", f"{len(df)} ครั้ง")
        with col2:
            st.metric("🕒 ล่าสุดเมื่อ", df.iloc[0]['Timestamp'].split(' ')[1])
        with col3:
            status = df.iloc[0]['Status']
            # ใส่สีให้สถานะหน่อย
            if status == "Success":
                st.metric("สถานะล่าสุด", "✅ สำเร็จ")
            else:
                st.metric("สถานะล่าสุด", "❌ ผิดพลาด")
        
        st.markdown("---")

        # 2. ตาราง Log (ปรับแต่งให้สวยงาม)
        st.dataframe(
            df, 
            use_container_width=True, 
            hide_index=True,
            column_config={
                "Timestamp": st.column_config.TextColumn("เวลา (Time)", width="medium"),
                "Action": st.column_config.TextColumn("กิจกรรม (Action)", width="medium"),
                "Detail": st.column_config.TextColumn("รายละเอียด (Detail)", width="large"),
                "Status": st.column_config.TextColumn("สถานะ (Status)", width="small"),
            }
        )
        
        # 3. ปุ่ม Download
        col_dl, _ = st.columns([1, 4])
        with col_dl:
            csv = df.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 ดาวน์โหลดประวัติ (CSV)",
                data=csv,
                file_name="smart_doc_logs.csv",
                mime="text/csv",
                type="primary"
            )
            
    else:
        # กรณีไม่มี Log
        st.info("ℹ️ ยังไม่มีประวัติการใช้งานในรอบนี้ (ลองไปใช้งานเมนูอื่นๆ ดูก่อนนะครับ)")
        
    # --- Footer ---
    st.markdown("---")
    st.caption("🔒 **Security Note:** API Key ถูกจัดการผ่านระบบ Secrets หลังบ้านเพื่อความปลอดภัยสูงสุด")
    st.caption("Version: Smart Document v1.0 (Final Release)")
