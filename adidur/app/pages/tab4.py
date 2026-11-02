"""แท็บ 4 — แหล่งข้อมูลและดาวน์โหลด"""
import importlib.util
import os
from dash import html, dcc, Input, Output, State, ctx
from dash.exceptions import PreventUpdate

from .. import queries as Q
from ..components import fmt
from ..state import be

DATASETS = [
    ("AIID · AI Incident Database", "Responsible AI Collaborative", "1 แถว = 1 เหตุการณ์ AI",
     "ฉบับส่งออก 26 ต.ค. 2569", "1,775 แถว → ตารางเตรียมแล้ว aiid_incident",
     "incident_id, date, title, description, risk_domain, report_count",
     "Deepfake (ตั้งเอง) = ค้นคำใน title + description + Implicated Systems · Misinformation = Risk Domain",
     "นับเฉพาะเหตุการณ์ที่มีคนบันทึก เอนไปทางภาษาอังกฤษและสหรัฐฯ ปีล่าสุดอาจบันทึกล่าช้า ห้ามสรุปว่า Deepfake ลดลง",
     "https://incidentdatabase.ai/"),
    ("FOTN · Freedom on the Net", "Freedom House ผ่าน QoG Standard Dataset (ม.ค. 2026) มหาวิทยาลัยโกเธนเบิร์ก",
     "1 แถว = 1 ประเทศ ใน 1 ปีข้อมูล", "ปีข้อมูล 2553–2567 (รายงาน 2554–2568)", "940 แถว 72 ประเทศ",
     "iso3, data_year, total_score, 3 องค์ประกอบ, status_th",
     "คะแนน 0–100 สูง = เสรีมาก เทียบอันดับในปีเดียวและในกลุ่มเดียวกัน",
     "เป็นการประเมินของผู้เชี่ยวชาญ ไม่ใช่การนับเหตุการณ์ จำนวนประเทศแต่ละปีไม่เท่ากัน",
     "https://freedomhouse.org/report/freedom-net"),
    ("EUvsDisinfo", "EEAS (EU) และ Leite et al. (2024) ผ่าน Zenodo สัญญาอนุญาต CC BY 4.0",
     "1 แถว = บทความ 1 ชิ้นที่ผูกกับการหักล้าง 1 เรื่อง", "6 ม.ค. 2558 – 1 ส.ค. 2566",
     "18,249 แถว → eu_article, 8,522 การหักล้าง → eu_debunk",
     "debunk_id, debunk_date, keywords, class",
     "จำนวนการหักล้าง = COUNT(DISTINCT debunk_id) · จำนวนบทความ = COUNT(*) (ติดป้ายหน่วยเสมอ)",
     "เก็บเฉพาะข้อมูลเท็จฝั่งสนับสนุนรัสเซีย ห้ามใช้ภาษาหรือโดเมนอนุมานประเทศต้นทาง",
     "https://euvsdisinfo.eu/"),
    ("AFNC · ศูนย์ต่อต้านข่าวปลอม", "กระทรวงดิจิทัลเพื่อเศรษฐกิจและสังคม (opendata.antifakenewscenter.com)",
     "1 แถว = โพสต์ 1 ชิ้น", "5 ม.ค. 2562 – 31 ต.ค. 2569 (ดาวน์โหลด 1 พ.ย. 2569)",
     "17,726 แถว → afnc_item, ข่าว AI 56 แถว → afnc_ai_match",
     "post_id, date, item_type, verdict_en, category_th, title, view_count, url",
     "ข่าวเท็จ = ปลอม + บิดเบือน · ข่าว AI ตามเกณฑ์ตั้งเอง 2 ระดับ ทุกรายการต้องตรวจสอบ",
     "เนื้อหาในไฟล์ถูกตัดความยาว จำนวนข่าว AI จึงเป็นค่าขั้นต่ำ · ไม่ใช่ปริมาณข่าวปลอมในสังคม · ปี 2562 ไม่ใช่ปีเต็ม",
     "https://www.antifakenewscenter.com/"),
    ("ACSC · ศูนย์ต่อต้านการฉ้อโกงออนไลน์", "สำนักงานตำรวจแห่งชาติ (ตัวเลขรวบรวมจากข่าว)",
     "1 แถว = การแถลง 1 สัปดาห์", "9 พ.ย. 2568 – 24 ต.ค. 2569", "48 แถว → acsc_week",
     "week_start, cases, loss_baht, loss_precision, flag_type, source_url",
     "บาทต่อคดี = SUM(loss)/SUM(cases) · สัปดาห์ที่ตัวเลขน่าสงสัย (suspect) รวม/ไม่รวมได้",
     "ไม่มีตัวแปรบอกว่าคดีเกี่ยวกับ AI · ตั้งแต่ ส.ค. 2569 ปัดเป็นล้านบาท · มีสัปดาห์ที่ไม่มีแถลง",
     "https://www.thaipoliceonline.go.th/"),
    ("weekly_panel · ตารางรวมรายสัปดาห์", "ชุดข้อมูลรวม thai-disinfo-scam-dataset (AFNC + ACSC)",
     "1 แถว = 1 สัปดาห์ (อาทิตย์–เสาร์)", "30 ธ.ค. 2561 – 31 ต.ค. 2569", "409 แถว → weekly_panel",
     "week_start, afnc_*, acsc_*", "ใช้เป็นปฏิทินสัปดาห์เพื่อวาดช่องว่างของ ACSC",
     "ฝั่ง ACSC ว่างในสัปดาห์ที่ไม่มีแถลง (ไม่ใช่ 0)", None),
]

KPI_FORMULAS = [
    ("K1.1 Deepfake", "COUNT(DISTINCT incident_id) WHERE is_deepfake=1 · เหตุการณ์ · AIID"),
    ("K1.2 ข่าวเท็จเกี่ยวกับ AI", "COUNT(DISTINCT post_id) จาก afnc_ai_match · โพสต์ · แยก 2 ระดับ"),
    ("K1.3 คดี", "SUM(cases) · คดี · ACSC"),
    ("K1.4 ความเสียหาย", "SUM(loss_baht) และ SUM(loss_baht)/SUM(cases) เฉพาะแถวที่มีทั้งคู่ (ไม่ใช้ค่าเฉลี่ยของบาทต่อคดี)"),
    ("C2.1 / C2.2 สัดส่วนประเด็น", "เรื่องในประเด็น ÷ เรื่องทั้งหมดของปีนั้นในแหล่งเดียวกัน × 100 (1 เรื่องอยู่ได้หลายประเด็น)"),
    ("C3.1 อันดับ", "RANK() ของ total_score ภายในกลุ่มที่เลือก ปีเดียว"),
    ("เปลี่ยนแปลง 2569 เทียบ 2568", "(ค่า 2569 − ค่า 2568) ÷ ค่า 2568 ช่วงเดียวกัน · ฐาน 0 = คำนวณไม่ได้ · ฐานน้อยกว่า 10 แสดงจำนวนคู่กัน"),
]


def _regexes():
    """อ่านค่าคงที่จาก scripts/build_db.py (import ไม่ทำงานอื่นนอกจากกำหนดค่าคงที่)"""
    path = os.path.join(Q.ROOT, "scripts", "build_db.py")
    try:
        spec = importlib.util.spec_from_file_location("build_db_consts", path)
        m = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(m)
        return {"media": m.AI_MEDIA.pattern, "mention": m.AI_MENTION.pattern,
                "imp": m.IMPERSONATE.pattern, "deepfake": m.AIID_DEEPFAKE.pattern}
    except Exception:
        return None


def _card(d):
    name, who, row, period, rows, cols, how, limit, link = d
    return html.Div([
        html.H4(name),
        html.Dl([html.Dt("ผู้จัดทำ"), html.Dd(who), html.Dt("1 แถว ="), html.Dd(row), html.Dt("ช่วงเวลา / วันที่ไฟล์"),
                 html.Dd(period), html.Dt("จำนวนแถวก่อน/หลังเตรียม"), html.Dd(rows), html.Dt("คอลัมน์สำคัญ"), html.Dd(cols),
                 html.Dt("วิธีนับ"), html.Dd(how), html.Dt("ข้อจำกัด"), html.Dd(limit)]),
        html.A("ลิงก์ต้นทาง", href=link, target="_blank", rel="noopener") if link else html.Span("ไม่มีลิงก์เฉพาะ", className="muted"),
    ], className="ds-card")


def layout():
    th = Q.themes()
    rx = _regexes()
    raw_files = sorted(os.listdir(Q.RAW_DIR)) if os.path.isdir(Q.RAW_DIR) else []
    return html.Section([
        html.H2("แหล่งข้อมูลและดาวน์โหลด", className="question"),
        html.Div([_card(d) for d in DATASETS], className="ds-grid"),
        html.Div([
            html.Div([html.H3("กล่อง 1 · ดาวน์โหลดต้นฉบับ"), html.P("ไฟล์ต้นฉบับตามเดิม ไม่แปลง", className="muted small"),
                      dcc.Dropdown(id="t4-raw", options=[{"label": f, "value": f} for f in raw_files],
                                   value=raw_files[0] if raw_files else None, clearable=False),
                      html.Button("ดาวน์โหลดต้นฉบับ", id="t4-btn-raw", className="btn dl raw", n_clicks=0)],
                     className="dlbox raw"),
            html.Div([html.H3("กล่อง 2 · ข้อมูลที่เตรียมแล้ว (CSV)"), html.P("UTF-8 พร้อม BOM ต่อตาราง", className="muted small"),
                      dcc.Dropdown(id="t4-table", options=[{"label": t, "value": t} for t in Q.PREPARED_TABLES],
                                   value=Q.PREPARED_TABLES[0], clearable=False),
                      html.Button("ดาวน์โหลดข้อมูลที่เตรียมแล้ว", id="t4-btn-prep", className="btn dl prep", n_clicks=0)],
                     className="dlbox prep"),
            html.Div([html.H3("กล่อง 3 · ผลตามตัวกรองปัจจุบัน"), html.P("ใช้ตัวกรองของแท็บ 1–3 ที่เลือกอยู่", className="muted small"),
                      dcc.Dropdown(id="t4-tab", clearable=False, value="1",
                                   options=[{"label": "แท็บ 1 · ตารางหลักฐาน T1", "value": "1"},
                                            {"label": "แท็บ 2 · ตารางหลักฐาน T2 (AFNC + EU)", "value": "2"},
                                            {"label": "แท็บ 3 · เทียบประเทศ C3.1", "value": "3"}]),
                      html.Button("ดาวน์โหลดผลตามตัวกรอง", id="t4-btn-filt", className="btn dl filt", n_clicks=0)],
                     className="dlbox filt"),
        ], className="dl-grid"),
        dcc.Download(id="t4-dl"),
        html.Div([
            html.Div([html.H3("สูตร KPI"),
                      html.Table([html.Tr([html.Th("ตัวชี้วัด"), html.Th("สูตร")])] +
                                 [html.Tr([html.Td(a), html.Td(b)]) for a, b in KPI_FORMULAS], className="tbl")],
                     className="panel"),
            html.Div([html.H3("วิธีค้นคำ AI (ตั้งเอง)"),
                      html.P("ใช้เฉพาะข่าวเท็จ (ปลอม + บิดเบือน) หลังลบแท็ก HTML และ URL ไม่ค้น ai ตัวพิมพ์เล็กแบบหลวม "
                             "เพื่อไม่ให้จับ AIS หรือคำอื่นผิด", className="small"),
                      html.H5("ระดับ มีคำบ่งชี้ว่าใช้ AI สร้างสื่อ (ตั้งเอง)"),
                      html.Pre(rx["media"] if rx else "ดูใน scripts/build_db.py"),
                      html.H5("ระดับ กล่าวถึง AI (ตั้งเอง)"),
                      html.Pre(rx["mention"] if rx else "ดูใน scripts/build_db.py"),
                      html.H5("ป้าย แอบอ้างหน่วยงาน/บุคคล (ตั้งเอง)"),
                      html.Pre(rx["imp"] if rx else "แอบอ้าง"),
                      html.H5("Deepfake ใน AIID (ตั้งเอง)"),
                      html.Pre(rx["deepfake"] if rx else "ดูใน scripts/build_db.py")], className="panel"),
        ], className="two"),
        html.Div([html.H3("พจนานุกรมประเด็น (ตั้งเอง)"),
                  html.Table([html.Tr([html.Th("ประเด็น"), html.Th("ที่มา"), html.Th("กติกา EUvsDisinfo"),
                                       html.Th("กติกา AFNC")])] +
                             [html.Tr([html.Td(r.theme_th), html.Td(f"{r.named_by} (ตั้งเอง)"), html.Td(r.eu_rule),
                                       html.Td(r.afnc_rule)]) for r in th.itertuples()], className="tbl")],
                 className="panel wide scroll"),
        html.Div([html.H3("ชื่อที่ตั้งเองในเว็บนี้"),
                  html.Ul([html.Li("is_deepfake, is_misinfo, deepfake_terms (ตั้งเอง)"),
                           html.Li("ai_level: mention / media_evidence, review_status, impersonation_flag (ตั้งเอง)"),
                           html.Li("flag_type: suspect / note (ตั้งเอง)"),
                           html.Li("theme, theme_id, country_group, country_th (ตั้งเอง)")])], className="panel wide"),
    ], id="tab4-body")


def register(app, stores):
    @app.callback(
        Output("t4-dl", "data"),
        Input("t4-btn-raw", "n_clicks"), Input("t4-btn-prep", "n_clicks"), Input("t4-btn-filt", "n_clicks"),
        State("t4-raw", "value"), State("t4-table", "value"), State("t4-tab", "value"),
        State("store-tab1", "data"), State("store-tab2", "data"), State("store-tab3", "data"),
        prevent_initial_call=True)
    def download(n1, n2, n3, raw, table, tab, s1, s2, s3):
        trig = ctx.triggered_id
        if not ctx.triggered[0]["value"]:
            raise PreventUpdate
        if trig == "t4-btn-raw":
            safe = os.path.basename(raw or "")
            path = os.path.join(Q.RAW_DIR, safe)
            if not safe or not os.path.isfile(path):
                raise PreventUpdate
            return dcc.send_file(path)
        if trig == "t4-btn-prep":
            return dict(content=Q.to_csv_bytes_str(Q.table(table)), filename=f"adidur_{table}.csv", type="text/csv")
        return filtered_download(tab, s1, s2, s3)


def filtered_download(tab, s1, s2, s3):
    """ผลตามตัวกรองปัจจุบัน -> dict สำหรับ dcc.Download (CSV UTF-8 BOM)"""
    import pandas as pd
    if tab == "1":
        df = Q.t1(s1)
        name = f"adidur_tab1_{be(s1['y0'])}-{be(s1['y1'])}" + (f"_{be(s1['year'])}" if s1.get("year") else "") + "_filtered.csv"
    elif tab == "2":
        af, eu = Q.t2(s2)
        df = pd.concat([af, eu], ignore_index=True)
        name = f"adidur_tab2_{s2['theme']}_{be(s2['y0'])}-{be(s2['y1'])}_filtered.csv"
    else:
        df = Q.c31(s3)
        name = f"adidur_tab3_{be(s3['fy'])}_filtered.csv"
    return dict(content=Q.to_csv_bytes_str(df), filename=name, type="text/csv")
