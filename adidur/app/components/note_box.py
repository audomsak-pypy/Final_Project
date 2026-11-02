"""note_box.py — คอมโพเนนต์กล่องข้อค้นพบ ข้อจำกัด และคำอธิบายความหมาย"""
from dash import html

def render_findings_and_limitations(findings_text, limitations_text):
    return html.Div([
        html.Div([
            html.Div("📌 ข้อค้นพบจากข้อมูล", className="box-header-findings"),
            html.Div(findings_text, className="box-content-findings")
        ], className="note-card note-findings"),
        html.Div([
            html.Div("⚠️ ข้อจำกัดและข้อควรระวัง", className="box-header-limitations"),
            html.Div(limitations_text, className="box-content-limitations")
        ], className="note-card note-limitations"),
    ], className="findings-limitations-container")

def render_why_and_definitions_section():
    definitions = [
        ("Deepfake", "ภาพ เสียง หรือวิดีโอที่ใช้ AI สร้างหรือดัดแปลงให้ดูเหมือนคนจริงพูดหรือทำสิ่งที่ไม่ได้ทำ ในเว็บนี้นับจากคำค้นใน AIID"),
        ("Misinformation", "ข้อมูลที่ไม่ถูกต้อง ในเว็บนี้หมายถึงเหตุการณ์ใน AIID ที่กลุ่มวิจัย MIT จัดไว้ใน Risk Domain 'Misinformation'"),
        ("ข่าวปลอม", "คำตัดสินของศูนย์ต่อต้านข่าวปลอม (AFNC) ว่าเนื้อหาไม่เป็นความจริง"),
        ("ข่าวบิดเบือน", "คำตัดสินของ AFNC ว่ามีส่วนจริงแต่ถูกนำเสนอให้เข้าใจผิด"),
        ("ข่าวเท็จ (ในเว็บนี้)", "ผลรวมของข่าวปลอม + ข่าวบิดเบือน"),
        ("การหักล้าง (debunk)", "บันทึก 1 เรื่องของ EUvsDisinfo ที่อธิบายว่ากล่าวอ้างอะไรและทำไมไม่จริง"),
        ("คะแนนเสรีภาพอินเทอร์เน็ต", "คะแนน 0–100 จาก Freedom House ยิ่งสูงยิ่งเสรี มี 3 ส่วน: การเข้าถึง /25, การจำกัดเนื้อหา /35, การละเมิดสิทธิผู้ใช้ /40"),
        ("ปีข้อมูล / ปีรายงาน", "ปีที่การประเมินครอบคลุม / ปีที่รายงานตีพิมพ์ (ปีรายงาน = ปีข้อมูล + 1)"),
        ("ยอดเข้าชม", "view_count ณ 1 พ.ย. 2569 สะสมตั้งแต่วันโพสต์ ไม่ใช่ตัววัดความน่าเชื่อถือหรือความรุนแรง"),
    ]

    def_items = []
    for term, desc in definitions:
        def_items.append(html.Div([
            html.Span(f"{term}: ", className="def-term"),
            html.Span(desc, className="def-desc")
        ], className="def-row"))

    why_points = [
        "เทคโนโลยี AI ทำให้การผลิตและเผยแพร่ข้อมูลบิดเบือน ภาพ และเสียงปลอม ทำได้รวดเร็วและแนบเนียนยิ่งขึ้น",
        "ศูนย์ต่อต้านข่าวปลอม (AFNC) และศูนย์ต่อต้านการฉ้อโกงออนไลน์ (ACSC) ในไทย ได้เผยแพร่ข้อมูลสถิติที่สะท้อนสถานการณ์ในประเทศ",
        "แดชบอร์ดนี้วางข้อมูลจากหลายแหล่ง (AIID, AFNC, ACSC, EUvsDisinfo, Freedom House) ไว้บนแกนเวลาเดียวกัน เพื่อให้ผู้ใช้สำรวจและกดดูหลักฐานต้นทางได้เอง",
        "ข้อมูลแต่ละชุดบันทึกคนละสิ่ง จึงใช้เปรียบเทียบช่วงเวลาและประเด็นได้ แต่ห้ามใช้สรุปความสัมพันธ์เชิงสาเหตุ"
    ]

    why_items = [html.Li(p, className="why-bullet") for p in why_points]

    return html.Div([
        html.Div([
            html.H3("ทำไมจึงจัดทำ Dashboard นี้", className="info-section-title"),
            html.Ul(why_items, className="why-list")
        ], className="info-card why-card"),
        html.Div([
            html.H3("ค่าแต่ละค่าคืออะไร (คำนิยาม)", className="info-section-title"),
            html.Div(def_items, className="def-list")
        ], className="info-card def-card")
    ], className="info-sections-container")
