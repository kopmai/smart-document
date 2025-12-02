import difflib

class TextComparator:
    def __init__(self):
        self.differ = difflib.HtmlDiff(wrapcolumn=80) 

    def generate_diff_html(self, text1_lines, text2_lines, mode="all"):
        """สร้างตาราง HTML Diff ดิบๆ"""
        show_context = True if mode == "diff_only" else False
        return self.differ.make_table(
            text1_lines, 
            text2_lines, 
            context=show_context, 
            numlines=2
        )

    def get_final_display_html(self, raw_html_diff, search_query=""):
        """
        หน้าที่: ห่อหุ้มตาราง Diff ด้วย CSS และฝัง JavaScript สำหรับ Highlight
        Return: HTML String ก้อนสมบูรณ์พร้อมแสดงผล
        """
        
        # 1. สร้าง Script Highlight (ถ้ามีคำค้นหา)
        js_script = ""
        if search_query:
            js_script = f"""
            <script>
                document.addEventListener("DOMContentLoaded", function() {{
                    var keyword = "{search_query}";
                    if (keyword && keyword.trim() !== "") {{
                        var cells = document.getElementsByTagName('td');
                        for (var i = 0; i < cells.length; i++) {{
                            var innerHTML = cells[i].innerHTML;
                            var regex = new RegExp(keyword, "g"); 
                            cells[i].innerHTML = innerHTML.replace(regex, "<span style='background-color: #ff9800; color: white; padding: 0 4px; border-radius: 4px; box-shadow: 0 1px 2px rgba(0,0,0,0.2);'>" + keyword + "</span>");
                        }}
                    }}
                }});
            </script>
            """

        # 2. CSS สำหรับตกแต่งตาราง (Iframe Style)
        css_style = """
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Kanit:wght@300;400&display=swap');
            body { font-family: 'Kanit', sans-serif; margin: 0; padding: 0;}
            table.diff { width: 100%; border-collapse: collapse; font-size: 14px; }
            .diff_header { background-color: #f8f9fa; color: #6c757d; padding: 8px; text-align: right; border-bottom: 2px solid #dee2e6; width: 40px; font-weight: bold;}
            td { padding: 10px; border-bottom: 1px solid #f0f0f0; vertical-align: top;}
            
            /* Diff Colors */
            .diff_add { background-color: #e2f0d9; color: #38761d; }
            .diff_chg { background-color: #fff2cc; color: #bf9000; }
            .diff_sub { background-color: #fce8e6; color: #c00000; text-decoration: line-through;}
        </style>
        """

        # รวมร่างส่งกลับไป
        return js_script + css_style + raw_html_diff
