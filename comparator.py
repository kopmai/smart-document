import difflib

class TextComparator:
    def __init__(self):
        # wrapcolumn=60 คือตัดบรรทัดถ้าตัวอักษรยาวเกิน เพื่อให้แสดงผลในตารางสวย
        self.differ = difflib.HtmlDiff(wrapcolumn=60) 

    # --- จุดที่ต้องแก้ไขคือบรรทัดด้านล่างนี้ครับ ต้องมี mode="all" ---
    def generate_diff_html(self, text1_lines, text2_lines, mode="all"):
        
        # ถ้า mode เป็น diff_only (แสดงเฉพาะจุดต่าง) ให้ context=True
        show_context = True if mode == "diff_only" else False
        
        html_diff = self.differ.make_table(
            text1_lines, 
            text2_lines, 
            fromdesc="Original File", 
            todesc="Modified File",
            context=show_context, 
            numlines=2
        )
        return html_diff