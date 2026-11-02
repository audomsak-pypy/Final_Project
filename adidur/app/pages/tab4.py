"""tab4.py — แท็บ 4: แหล่งข้อมูลและดาวน์โหลด (S4.1–S4.3, D4.1–D4.3)"""
from dash import html, dcc
import app.queries as q

DATASET_METADATA = [
    {
        'name': 'AI Incident Database (AIID)',
        'provider': 'Responsible AI Collaborative',
        'grain': '1 แถว = 1 เหตุการณ์ที่เกี่ยวกับ AI',
        'period': '26 ก.ย. 2526 – 22 ต.ค. 2569 (หลักๆ ตั้งแต่ 2558)',
        'file_date': '26 ต.ค. 2569',
        'rows': '1,775 แถว (ID ไม่ซ้ำ 1,775)',
        'cols': 'Incident ID, date, title, description, Implicated Systems, Risk Domain, is_deepfake (ตั้งเอง)',
        'method': 'นับจำนวนเหตุการณ์ = COUNT(DISTINCT incident_id), Deepfake ค้นจากคำค้น',
        'limits': 'เอนเอียงไปทางภาษาอังกฤษและสหรัฐฯ ไม่ใช่เหตุการณ์จริงทั้งหมดของโลก',
        'link': 'https://incidentdatabase.ai'
    },
    {
        'name': 'Freedom on the Net (FOTN)',
        'provider': 'Freedom House / QoG Standard Dataset',
        'grain': '1 แถว = 1 ประเทศ ใน 1 ปีข้อมูล',
        'period': 'ปีข้อมูล 2553–2567 (ปีรายงาน 2554–2568)',
        'file_date': 'ม.ค. 2569',
        'rows': '940 แถว (72 ประเทศ)',
        'cols': 'iso3, country, country_th (ตั้งเอง), data_year, report_edition, total_score, 3 องค์ประกอบ, status_th',
        'method': 'คะแนนรวม 0–100 จากผลรวม 3 องค์ประกอบ (เข้าถึง /25, จำกัดเนื้อหา /35, สิทธิ /40)',
        'limits': 'เป็นการประเมินของผู้เชี่ยวชาญ ไม่ใช่การตรวจนับคดี อาเซียนมีข้อมูล 8 ประเทศ (ไม่มีลาวและบรูไน)',
        'link': 'https://freedomhouse.org/report/freedom-net'
    },
    {
        'name': 'EUvsDisinfo',
        'provider': 'EEAS (EU) / Leite et al. (2024)',
        'grain': '1 แถว = บทความ 1 ชิ้นที่ผูกกับการหักล้าง 1 เรื่อง',
        'period': '6 ม.ค. 2558 – 1 ส.ค. 2566',
        'file_date': '1 ส.ค. 2566',
        'rows': '18,249 แถว (การหักล้าง debunk_id ไม่ซ้ำ 8,522 เรื่อง)',
        'cols': 'debunk_id, debunk_date, keywords, article_url, article_language, class',
        'method': 'จำนวนการหักล้าง = COUNT(DISTINCT debunk_id), จำนวนบทความ = COUNT(*)',
        'limits': 'เน้นข้อมูลบิดเบือนที่สนับสนุนรัสเซีย มีข้อมูลถึง 1 ส.ค. 2566 ห้ามใช้ภาษาหรือโดเมนอนุมานประเทศต้นทาง',
        'link': 'https://euvsdisinfo.eu'
    },
    {
        'name': 'ศูนย์ต่อต้านข่าวปลอม ประเทศไทย (AFNC)',
        'provider': 'กระทรวงดิจิทัลเพื่อเศรษฐกิจและสังคม',
        'grain': '1 แถว = 1 โพสต์ผลการตรวจสอบข่าว',
        'period': '5 ม.ค. 2562 – 31 ต.ค. 2569',
        'file_date': '31 ต.ค. 2569',
        'rows': '17,726 แถว (คำตัดสิน 14,458 โพสต์, ข่าวเท็จ 10,955 โพสต์)',
        'cols': 'post_id, date, verdict_en, category_th, title, content_500, view_count, url',
        'method': 'ข่าวเท็จ = Fake + Distorted, ข่าว AI ค้นจากคำค้นและคำบ่งชี้สื่อ AI (ตั้งเอง)',
        'limits': 'เนื้อหาในไฟล์ถูกตัดที่ 500 ตัวอักษร จำนวนข่าว AI ที่พบ (56 โพสต์) จึงเป็นค่าขั้นต่ำ',
        'link': 'https://www.antifakenewscenter.com'
    },
    {
        'name': 'ศูนย์ต่อต้านการฉ้อโกงออนไลน์ (ACSC)',
        'provider': 'สำนักงานตำรวจแห่งชาติ (แถลงข่าวรายสัปดาห์)',
        'grain': '1 แถว = การแถลงข่าวสรุปสถิติคดี 1 สัปดาห์',
        'period': '9 พ.ย. 2568 – 24 ต.ค. 2569 (48 สัปดาห์ที่มีการแถลง)',
        'file_date': '24 ต.ค. 2569',
        'rows': '48 แถว',
        'cols': 'week_start, week_end, cases, loss_baht, loss_precision, flag_type (ตั้งเอง)',
        'method': 'ยอดรวม = SUM(cases), SUM(loss_baht), เฉลี่ยบาท/คดี = SUM(loss_baht)/SUM(cases)',
        'limits': 'ไม่มีข้อมูลก่อน พ.ย. 2568, มีสัปดาห์ขาด 3 สัปดาห์, ปัดเลขเป็นล้านตั้งแต่ ส.ค. 2569, ไม่สามารถระบุได้ว่าคดีใดเกี่ยวกับ AI',
        'link': 'https://thaipoliceonline.go.th'
    },
    {
        'name': 'ตารางพาเนลรายสัปดาห์ (weekly_panel)',
        'provider': 'สร้างขึ้นเพื่อจัดแกนเวลาปฏิทินอาทิตย์–เสาร์',
        'grain': '1 แถว = 1 สัปดาห์ปฏิทินมาตรฐาน',
        'period': 'พ.ย. 2561 – ต.ค. 2569',
        'file_date': '2 พ.ย. 2569',
        'rows': '409 สัปดาห์',
        'cols': 'week_start, week_end, afnc_verdicts, acsc_reported, acsc_cases, acsc_loss_baht',
        'method': 'ผูกข้อมูล AFNC และ ACSC ลงสัปดาห์ปฏิทินเดียวกัน สัปดาห์ที่ไม่มีแถลงเป็น NULL (ช่องว่าง)',
        'limits': 'ใช้แสดงผลกราฟแนวโน้มรายสัปดาห์ เพื่อป้องกันปัญหาสัปดาห์ที่มี 8 วันหลุดการเชื่อมโยง',
        'link': '-'
    }
]

def render_tab4_content(con):
    # S4.1 Dataset cards
    ds_cards = []
    for d in DATASET_METADATA:
        ds_cards.append(html.Div([
            html.Div(d['name'], className="dataset-card-title"),
            html.Div([html.Strong("ผู้จัดทำ: "), d['provider']], className="dataset-meta-item"),
            html.Div([html.Strong("หน่วยข้อมูล (Grain): "), d['grain']], className="dataset-meta-item"),
            html.Div([html.Strong("ช่วงเวลา: "), d['period']], className="dataset-meta-item"),
            html.Div([html.Strong("จำนวนข้อมูล: "), d['rows']], className="dataset-meta-item"),
            html.Div([html.Strong("คอลัมน์สำคัญ: "), d['cols']], className="dataset-meta-item"),
            html.Div([html.Strong("วิธีนับและตัวชี้วัด: "), d['method']], className="dataset-meta-item"),
            html.Div([html.Strong("ข้อจำกัดสำคัญ: "), d['limits']], className="dataset-meta-item"),
            html.Div([
                html.A("เว็บไซต์ต้นฉบับ ↗", href=d['link'], target="_blank", rel="noopener noreferrer", className="btn-link-sm")
                if d['link'] != '-' else None
            ], style={'marginTop': '6px'})
        ], className="dataset-card"))

    # S4.2 KPI Formulas
    kpi_formulas = [
        ("K1.1", "Deepfake ทั่วโลก (AIID)", "COUNT(DISTINCT incident_id) WHERE is_deepfake=1 AND year BETWEEN :y0 AND :y1"),
        ("K1.2", "ข่าวเท็จเกี่ยวกับ AI ในไทย (AFNC)", "COUNT(DISTINCT a.post_id) จาก afnc_ai_match JOIN afnc_item โดยกรองตาม levels, category, imp"),
        ("K1.3", "จำนวนคดีออนไลน์ (ACSC)", "SUM(cases) WHERE week_start ในช่วงที่เลือก และ inc_suspect ตามที่กำหนด (ไม่กรองด้วย AI)"),
        ("K1.4", "ความเสียหายและเฉลี่ยบาท/คดี (ACSC)", "SUM(loss_baht) และ SUM(loss_baht)/SUM(cases) เฉพาะแถวที่มีทั้งสองค่า (ห้ามใช้ AVG(loss_per_case))"),
        ("K2.1–K2.3", "สถิติเปรียบเทียบประเด็น (EU/AFNC/AIID)", "EU: COUNT(DISTINCT debunk_id), AFNC: ข่าวเท็จ Fake+Distorted, AIID: is_misinfo=1 (แยกการ์ด ห้ามรวม)"),
        ("C2.1, C2.2", "สัดส่วนประเด็น (%)", "เรื่องในประเด็น ÷ จำนวนเรื่องทั้งหมดของแหล่งนั้นในปีนั้น × 100 (สเกลสีเดียวกัน 0–100%)"),
        ("K3.1, C3.1", "คะแนนและอันดับเสรีภาพ (FOTN)", "total_score ในปี :fy, อันดับคิดภายในกลุ่มที่เลือกในปีเดียว (ห้ามรวมหลายปีจัดอันดับ)"),
    ]

    formula_rows = [
        html.Tr([html.Td(html.Strong(code)), html.Td(name), html.Td(html.Code(sql))])
        for code, name, sql in kpi_formulas
    ]

    # S4.3 AI & Theme Dictionaries
    theme_df = q.get_theme_definitions(con)
    theme_rows = [
        html.Tr([
            html.Td(r['theme_id']),
            html.Td(f"{r['theme_th']} (ตั้งเอง)"),
            html.Td(r['eu_rule']),
            html.Td(r['afnc_rule'])
        ])
        for _, r in theme_df.iterrows()
    ]

    # Download sections D4.1, D4.2, D4.3
    download_section = html.Div([
        html.H3("ดาวน์โหลดข้อมูล", className="section-title", style={'marginBottom': '14px'}),
        html.Div([
            # Box 1: Raw
            html.Div([
                html.Div("กล่อง 1: ดาวน์โหลดไฟล์ต้นฉบับ (Raw Data)", className="download-box-title"),
                html.P("ไฟล์ข้อมูลดิบดั้งเดิมก่อนการประมวลผล (Excel / CSV)", style={'fontSize': '12.5px', 'color': 'var(--muted)'}),
                html.Div([
                    html.Button("AIID Excel", id="btn-dl-raw-aiid", className="btn-dl btn-dl-raw"),
                    html.Button("FOTN Scores CSV", id="btn-dl-raw-fotn", className="btn-dl btn-dl-raw"),
                    html.Button("EUvsDisinfo CSV", id="btn-dl-raw-eu", className="btn-dl btn-dl-raw"),
                    html.Button("Thai Scam Dataset Excel", id="btn-dl-raw-thai", className="btn-dl btn-dl-raw"),
                ], className="btn-group-dl"),
                dcc.Download(id="download-raw-files")
            ], className="download-box download-box-raw"),

            # Box 2: Prepared
            html.Div([
                html.Div("กล่อง 2: ข้อมูลที่เตรียมแล้ว (CSV UTF-8 พร้อม BOM)", className="download-box-title"),
                html.P("ตารางฐานข้อมูล SQLite adidur.db พร้อมใช้งาน", style={'fontSize': '12.5px', 'color': 'var(--muted)'}),
                html.Div([
                    html.Button("aiid_incident", id="btn-dl-prep-aiid", className="btn-dl btn-dl-prep"),
                    html.Button("afnc_item", id="btn-dl-prep-afnc", className="btn-dl btn-dl-prep"),
                    html.Button("afnc_ai_match", id="btn-dl-prep-aimatch", className="btn-dl btn-dl-prep"),
                    html.Button("acsc_week", id="btn-dl-prep-acsc", className="btn-dl btn-dl-prep"),
                    html.Button("weekly_panel", id="btn-dl-prep-wp", className="btn-dl btn-dl-prep"),
                    html.Button("eu_debunk", id="btn-dl-prep-eu", className="btn-dl btn-dl-prep"),
                    html.Button("fotn_score", id="btn-dl-prep-fotn", className="btn-dl btn-dl-prep"),
                    html.Button("theme", id="btn-dl-prep-theme", className="btn-dl btn-dl-prep"),
                ], className="btn-group-dl"),
                dcc.Download(id="download-prep-files")
            ], className="download-box download-box-prep"),

            # Box 3: Filtered Current
            html.Div([
                html.Div("กล่อง 3: ผลตามตัวกรองปัจจุบัน", className="download-box-title"),
                html.P("ส่งออกข้อมูลตารางหลักฐานตามเงื่อนไขที่เลือกอยู่ในแท็บ 1–3", style={'fontSize': '12.5px', 'color': 'var(--muted)'}),
                html.Div([
                    html.Button("ตารางแท็บ 1 (หลักฐาน AI)", id="btn-dl-filtered-t1", className="btn-dl btn-dl-filter"),
                    html.Button("ตารางแท็บ 2 (หลักฐานประเด็น)", id="btn-dl-filtered-t2", className="btn-dl btn-dl-filter"),
                    html.Button("ตารางแท็บ 3 (คะแนนเสรีภาพ)", id="btn-dl-filtered-t3", className="btn-dl btn-dl-filter"),
                ], className="btn-group-dl"),
                dcc.Download(id="download-filtered-files")
            ], className="download-box download-box-filter")
        ], className="download-boxes-grid")
    ], className="evidence-section")

    return html.Div([
        html.Div([
            html.H2("S4.1 ข้อมูลจำเพาะของชุดข้อมูลทั้ง 6 ชุด", className="section-title"),
            html.Div(ds_cards, className="datasets-grid")
        ], className="evidence-section"),

        html.Div([
            html.H2("S4.2 สูตรการคำนวณ KPI และกราฟ", className="section-title"),
            html.Div([
                html.Table([
                    html.Thead(html.Tr([html.Th("รหัส"), html.Th("ชื่อตัวชี้วัด"), html.Th("สูตร SQL")])),
                    html.Tbody(formula_rows)
                ], className="evidence-table")
            ], className="table-responsive-box")
        ], className="evidence-section"),

        html.Div([
            html.H2("S4.3 วิธีค้นคำ AI และพจนานุกรมประเด็น (ตั้งเอง)", className="section-title"),
            html.Div([
                html.P([
                    html.Strong("เกณฑ์ค้นข่าว AI ระดับ 2 (มีคำบ่งชี้ว่าใช้ AI สร้างสื่อ): "),
                    html.Code("deep\\s?-?fake|ดี[ปพ]\\s?เฟ[กคค์]|โคลนเสียง|ปลอมเสียง|เลียนเสียง|(?:สร้าง|ทำ|ตัดต่อ|ปลอม|ดัดแปลง|เจน)...ด้วย AI")
                ], style={'marginBottom': '8px', 'fontSize': '13px'}),
                html.P([
                    html.Strong("เกณฑ์ค้นข่าว AI ระดับ 1 (กล่าวถึง AI): "),
                    html.Code("(?<![A-Za-z])AI(?![A-Za-z])|artificial intelligence|ปัญญาประดิษฐ์|เอไอ|chatgpt|แชทบอท")
                ], style={'marginBottom': '14px', 'fontSize': '13px'}),
                html.Table([
                    html.Thead(html.Tr([html.Th("รหัสประเด็น"), html.Th("ชื่อประเด็น"), html.Th("กฎของ EUvsDisinfo"), html.Th("กฎของ AFNC")])),
                    html.Tbody(theme_rows)
                ], className="evidence-table")
            ], className="table-responsive-box")
        ], className="evidence-section"),

        download_section
    ])
