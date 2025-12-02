import google.generativeai as genai
import streamlit as st

# ตั้งค่า Safety ครั้งเดียวใช้ได้ทั้งแอป
SAFETY_SETTINGS = [
    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
]

def configure_api(api_key):
    """ตั้งค่า Key"""
    if api_key:
        genai.configure(api_key=api_key)

def get_gemini_models(api_key):
    """ดึงรายชื่อโมเดล"""
    try:
        configure_api(api_key)
        return [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
    except:
        return []

def generate_content(api_key, model_name, prompt, image=None, stream=False):
    """ฟังก์ชันอเนกประสงค์สำหรับยิง AI"""
    try:
        configure_api(api_key)
        model = genai.GenerativeModel(model_name, safety_settings=SAFETY_SETTINGS)
        
        inputs = [prompt]
        if image:
            inputs.append(image)
            
        response = model.generate_content(inputs, stream=stream)
        
        if stream:
            return response # คืนค่าเป็น Generator
        else:
            return response.text
    except Exception as e:
        return f"AI_ERROR: {str(e)}"
