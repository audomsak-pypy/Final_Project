"""หน้าเปิด และส่วนเลื่อนลง (ทำไมจึงจัดทำ / ค่าแต่ละค่าคืออะไร)"""
from dash import html, dcc

CREATOR = "[ชื่อผู้จัดทำ]"
COURSE = "Basic Programming for Data Scientist and Data Visualization"

GLOSSARY = [
    ("Deepfake", "ภาพ เสียง หรือวิดีโอที่ใช้ AI สร้างหรือดัดแปลงให้ดูเหมือนคนจริงพูดหรือทำสิ่งที่ไม่ได้ทำ ในเว็บนี้นับจากคำค้นใน AIID"),
    ("Misinformation", "ข้อมูลที่ไม่ถูกต้อง ในเว็บนี้หมายถึงเหตุการณ์ใน AIID ที่กลุ่มวิจัย MIT จัดไว้ใน Risk Domain \"Misinformation\""),
    ("ข่าวปลอม", "คำตัดสินของ AFNC ว่าเนื้อหาไม่เป็นความจริง"),
    ("ข่าวบิดเบือน", "คำตัดสินของ AFNC ว่ามีส่วนจริงแต่ถูกนำเสนอให้เข้าใจผิด"),
    ("ข่าวเท็จ (ในเว็บนี้)", "ข่าวปลอม + ข่าวบิดเบือน"),
    ("การหักล้าง (debunk)", "บันทึก 1 เรื่องของ EUvsDisinfo ที่อธิบายว่ากล่าวอ้างอะไรและทำไมไม่จริง"),
    ("คะแนนเสรีภาพอินเทอร์เน็ต", "คะแนน 0–100 จาก Freedom House ยิ่งสูงยิ่งเสรี มี 3 ส่วน: การเข้าถึง /25, การจำกัดเนื้อหา /35, การละเมิดสิทธิผู้ใช้ /40"),
    ("ปีข้อมูล / ปีรายงาน", "ปีที่การประเมินครอบคลุม / ปีที่รายงานตีพิมพ์ (ปีรายงาน = ปีข้อมูล + 1)"),
    ("ยอดเข้าชม", "view_count ณ 1 พ.ย. 2569 สะสมตั้งแต่วันโพสต์ ไม่ใช่ความน่าเชื่อถือหรือความรุนแรง"),
]


def landing():
    return html.Section([
        html.Div([
            html.Div(f"ผู้จัดทำ: {CREATOR}", className="creator"),
            html.Div([
                html.H1("Adidur", className="brand-big"),
                html.Div([html.Div("จริง", className="word w1"), html.Div("หรือ", className="word w2"),
                          html.Div("เฟค", className="word w3")], className="words"),
            ], className="hero-grid"),
            html.H2("AI ข่าวปลอม และภัยออนไลน์: มองโลก เปรียบเทียบไทย", className="hero-sub"),
            html.P("แดชบอร์ดวางข้อมูลจากหลายแหล่งไว้บนแกนเวลาเดียวกัน ให้ดูว่าแต่ละแหล่งบันทึกอะไรไว้ "
                   "และกดดูหลักฐานต้นทางได้เอง โดยไม่สรุปเกินข้อมูล", className="hero-desc"),
            dcc.Link("สำรวจ Dashboard", href="?tab=1", className="btn primary", refresh=False),
            html.Div(f"รายวิชา: {COURSE}", className="course"),
        ], className="hero"),
    ], id="landing-body")


def footer_sections():
    return html.Section([
        html.Div([
            html.H3("ทำไมจึงจัดทำ Dashboard นี้"),
            html.Ul([
                html.Li("AI ทำให้สร้างภาพ เสียง และวิดีโอปลอมได้ง่ายขึ้น"),
                html.Li("ศูนย์ต่อต้านข่าวปลอมและศูนย์ต่อต้านการฉ้อโกงออนไลน์เผยแพร่ข้อมูลที่ช่วยให้เห็นภาพในไทย"),
                html.Li("แดชบอร์ดนี้วางข้อมูลจากหลายแหล่งไว้บนแกนเวลาเดียวกัน เพื่อให้ผู้ใช้เห็นว่าแต่ละแหล่งบันทึกอะไรไว้ และกดดูหลักฐานต้นทางได้เอง"),
                html.Li("ข้อมูลเหล่านี้บันทึกคนละสิ่ง จึงใช้เทียบช่วงเวลาและประเด็นได้ แต่ใช้สรุปสาเหตุไม่ได้"),
            ]),
        ], className="panel wide"),
        html.Div([
            html.H3("ค่าแต่ละค่าคืออะไร"),
            html.Dl([x for k, v in GLOSSARY for x in (html.Dt(k), html.Dd(v))]),
        ], className="panel wide"),
    ], className="footer-sections")
