import pdfplumber
from docx import Document

class DocumentLoader:
    @staticmethod
    def extract_text(file, file_type):
        """
        แยกข้อความออกจากไฟล์ตามประเภท
        Return: list ของ string (แยกตามบรรทัด หรือ ย่อหน้า)
        """
        text_content = []

        if file_type == "docx":
            doc = Document(file)
            for para in doc.paragraphs:
                if para.text.strip(): # ตัดบรรทัดว่างทิ้ง
                    text_content.append(para.text)
                    
        elif file_type == "pdf":
            with pdfplumber.open(file) as pdf:
                for page in pdf.pages:
                    text = page.extract_text()
                    if text:
                        # แยกบรรทัดใน PDF เพื่อให้เทียบง่ายขึ้น
                        text_content.extend(text.split('\n'))
                        
        return text_content