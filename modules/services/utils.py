import streamlit as st
from datetime import datetime
import pandas as pd

# --- LOGGING SYSTEM ---
def init_logger():
    if 'activity_log' not in st.session_state:
        st.session_state['activity_log'] = []

def log_event(action, detail, status="Success"):
    """บันทึกเหตุการณ์ลงใน Session State"""
    init_logger()
    entry = {
        "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "Action": action,
        "Detail": detail,
        "Status": status
    }
    # ใส่ไว้บนสุด (ล่าสุดอยู่บน)
    st.session_state['activity_log'].insert(0, entry)

def get_logs_dataframe():
    """แปลง Log เป็น DataFrame เพื่อแสดงผล"""
    init_logger()
    if not st.session_state['activity_log']:
        return pd.DataFrame(columns=["Timestamp", "Action", "Detail", "Status"])
    return pd.DataFrame(st.session_state['activity_log'])

# --- SETTINGS SYSTEM ---
def init_settings():
    if 'global_api_key' not in st.session_state:
        # พยายามดึงจาก Secrets ก่อน
        if "GEMINI_API_KEY" in st.secrets:
            st.session_state['global_api_key'] = st.secrets["GEMINI_API_KEY"]
        else:
            st.session_state['global_api_key'] = ""

def get_api_key():
    init_settings()
    return st.session_state['global_api_key']

def set_api_key(key):
    st.session_state['global_api_key'] = key
