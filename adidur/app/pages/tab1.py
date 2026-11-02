"""แท็บ 1 — AI และภัยออนไลน์ในไทย (AIID + AFNC + ACSC)
กราฟทุกใบใช้เวลาชุดเดียวกัน: เลือกปี/เดือนที่กราฟใดก็ได้ ทุก KPI กราฟ การ์ด และตารางเปลี่ยนตาม"""
import pandas as pd
from dash import html, dcc, Input, Output, State, ALL, ctx
from dash.exceptions import PreventUpdate

from .. import queries as Q, figures as F
from ..components import (kpi, note_box, chips, chipbar, crumbbar, breadcrumb, graph, evidence_table, news_card,
                         link_md, fmt, panel)
from ..exports import filtered_download
from ..state import DEFAULTS, be, month_label, date_th

LEVEL_TH = {"mention": "กล่าวถึง AI", "media_evidence": "มีคำบ่งชี้ว่าใช้ AI สร้างสื่อ"}
YEARS = list(range(2015, 2027))


def layout():
    return html.Section([
        html.H2("Deepfake ข่าวเท็จเกี่ยวกับ AI และคดีออนไลน์ ช่วงเดียวกันเป็นอย่างไร", className="question"),
        html.Details([
            html.Summary("ตัวกรอง"),
            html.Div([
                html.Label(["ปีเริ่ม", dcc.Dropdown(id="t1-y0", clearable=False,
                           options=[{"label": str(be(y)), "value": y} for y in YEARS])]),
                html.Label(["ปีสิ้นสุด", dcc.Dropdown(id="t1-y1", clearable=False,
                           options=[{"label": str(be(y)), "value": y} for y in YEARS])]),
                html.Label(["ระดับข่าว AI", dcc.Checklist(id="t1-levels", options=[
                    {"label": " กล่าวถึง AI", "value": "mention"},
                    {"label": " มีคำบ่งชี้ว่าใช้ AI สร้างสื่อ", "value": "media_evidence"}], className="check")]),
                html.Label(["หมวดข่าว", dcc.Dropdown(id="t1-category", placeholder="ทุกหมวด",
                           options=[{"label": c, "value": c} for c in Q.categories_ai()])]),
                html.Label(["แอบอ้างหน่วยงาน/บุคคล", dcc.Dropdown(id="t1-imp", placeholder="ทั้งหมด", clearable=True,
                            options=[{"label": "เฉพาะที่พบ", "value": 1}, {"label": "เฉพาะที่ไม่พบ", "value": 0}])]),
                html.Label(["ACSC", dcc.Checklist(id="t1-susp", options=[
                    {"label": " รวมสัปดาห์ที่ตัวเลขน่าสงสัย", "value": "1"}], className="check")]),
            ], className="filters"),
        ], open=True, className="filter-box"),
        chipbar("t1"),
        crumbbar("t1-crumb", "t1-back"),
        html.Div([html.Div(id="t1-k11", className="kcell"), html.Div(id="t1-k12", className="kcell"),
                  html.Div(id="t1-k13", className="kcell"), html.Div(id="t1-k14", className="kcell")], className="kpis"),
        html.Div([
            panel("Deepfake และข่าวเท็จเกี่ยวกับ AI", graph("t1-g1"), tag="แตะจุดเพื่อเจาะลงปี › เดือน"),
            panel("หมวดข่าว AI", graph("t1-g3"),
                  html.Button(id="t1-impchip", n_clicks=0, className="chip"), tag="แตะแท่งเพื่อกรอง"),
        ], className="two"),
        panel("คดีหลอกลวงออนไลน์", graph("t1-g5"), html.Div(id="t1-detail", className="detail"),
              tag="ไม่ขึ้นกับตัวกรองข่าว AI · จุดกลวง = ปัดเลข · ช่องว่าง = ไม่มีแถลง", cls="wide"),
        html.H3("ข่าวเด่น AFNC (ยอดเข้าชม ณ 1 พ.ย. 2569)", className="section-title"),
        html.Div(id="t1-cards", className="cards"),
        panel("หลักฐาน", html.Div(id="t1-table"),
              html.Button("ดาวน์โหลด CSV", id="t1-dl-btn", n_clicks=0, className="btn small-btn"),
              dcc.Download(id="t1-dl"), cls="wide"),
        html.Div([html.Div(id="t1-find"), html.Div(id="t1-limit")], className="two"),
    ], id="tab1-body")


def _update_state(cur, trig, val):
    s = dict(cur)
    if trig in ("t1-y0", "t1-y1"):
        s["y0" if trig == "t1-y0" else "y1"] = int(val)
        if s["y0"] > s["y1"]:
            s["y0"], s["y1"] = s["y1"], s["y0"]
        s.update(level="year", year=None, month=None, acsc_week=None)
    elif trig == "t1-levels":
        s["levels"] = val or []
    elif trig == "t1-category":
        s["category"] = val
    elif trig == "t1-imp":
        s["imp"] = val
    elif trig == "t1-susp":
        s["inc_suspect"] = bool(val)
    elif trig == "t1-impchip":
        s["imp"] = None if s.get("imp") == 1 else 1
    elif trig == "t1-clear":
        s = {**DEFAULTS[1], "y0": s["y0"], "y1": s["y1"]}
    elif trig == "t1-back":
        if s.get("acsc_week"):
            s["acsc_week"] = None
        elif s["level"] == "items":
            s.update(level="month", month=None)
        elif s["level"] == "month":
            s.update(level="year", year=None, month=None)
    return s


def _click_state(cur, gid, pt):
    s = dict(cur)
    c = pt.get("customdata")
    if isinstance(c, list):
        c = c[0]
    if gid == "t1-g1":
        if s["level"] == "year":
            s.update(year=int(c), month=None, level="month", acsc_week=None)
        else:
            s.update(month=str(c), level="items", acsc_week=None)
    elif gid == "t1-g3":
        s["category"] = None if s.get("category") == c else c
    elif gid == "t1-g5":
        c = str(c)
        if len(c) == 7:  # แท่งเดือน -> เจาะลงเดือนนั้นในทุกกราฟ
            s.update(year=int(c[:4]), month=c, level="items", acsc_week=None)
        else:  # จุด/แท่งสัปดาห์ -> แผงรายละเอียด
            s.update(year=int(c[:4]), month=c[:7], level="items", acsc_week=c)
    return s


def _ytd_text():
    d = Q.ytd_compare()
    r = d[d["metric"] == "AFNC ข่าว AI"].iloc[0]
    a, b = int(r.y2025), int(r.y2026)
    ch = "คำนวณไม่ได้" if a == 0 else f"{(b - a) / a * 100:+.0f}%"
    return f"ข่าว AI ใน AFNC ม.ค.–ต.ค. ปี {be(2026)} เทียบ ปี {be(2025)}: {a} → {b} โพสต์ ({ch}) ฐานน้อย อ่านอย่างระวัง"


def render(s, theme):
    n_df = Q.k11(s)
    ai = Q.k12(s)
    k34 = Q.k13_14(s)
    acsc_rng = Q.q("SELECT MIN(week_start) a FROM acsc_week").iloc[0]
    acsc_empty = k34["cases"] is None
    n_ai = ai["mention"] + ai["media_evidence"]
    k11 = kpi("Deepfake ที่บันทึกทั่วโลก", fmt(n_df), "เหตุการณ์ · AIID", tone="a")
    k12 = kpi("ข่าวเท็จเกี่ยวกับ AI", fmt(n_ai), "โพสต์ · AFNC (ขั้นต่ำ)", tone="b",
              extra=f"กล่าวถึง {ai['mention']} · บ่งชี้สร้างสื่อ {ai['media_evidence']}")
    if acsc_empty:
        k13 = kpi("คดีที่แจ้ง", "—", f"ไม่มีข้อมูล ACSC ก่อน {date_th(acsc_rng['a'])}", tone="c")
        k14 = kpi("ความเสียหาย", "—", "บาท", tone="d")
    else:
        k13 = kpi("คดีที่แจ้ง", fmt(k34["cases"]), f"คดี · ACSC · {k34['weeks']} สัปดาห์", tone="c")
        k14 = kpi("ความเสียหาย", fmt(k34["loss"]), f"บาท · เฉลี่ย {fmt(k34['per_case'])} บาท/คดี", tone="d")

    top, low, total = Q.c14(s)
    if total == 0:
        cards = html.Div("ไม่มีข่าว AI ในชุดที่เลือก", className="empty")
    else:
        kids = [news_card("อันดับ 1 · เข้าชมสูงสุด", top.iloc[0], big=True),
                html.Div([news_card(f"อันดับ {i + 1}", top.iloc[i]) for i in range(1, len(top))], className="small-cards")]
        kids.append(html.Div(news_card("เข้าชมต่ำสุด", low.iloc[0]), className="low-card") if total >= 4 else
                    html.Div(f"มีข่าวในชุดนี้ {total} รายการ", className="empty low-card"))
        cards = html.Div(kids, className="cards-grid")

    order = sorted(Q.categories_ai())
    g1 = F.fig_c11_c12(s, Q.c11(s), Q.c12(s), theme)
    g3 = F.fig_c13(Q.c13(s), s, theme, order)
    week_df, month_df = Q.c15(s), Q.c15_month(s)
    g5 = F.fig_acsc(s, week_df, month_df, theme)

    items = []
    if (s["y0"], s["y1"]) != (DEFAULTS[1]["y0"], DEFAULTS[1]["y1"]):
        items.append(("range", f"{be(s['y0'])}–{be(s['y1'])}"))
    if s.get("year") is not None:
        items.append(("year", f"ปี {be(s['year'])}"))
    if s.get("month"):
        items.append(("month", month_label(s["month"])))
    if len(s["levels"]) < 2:
        items.append(("levels", " / ".join(LEVEL_TH[x] for x in s["levels"]) or "ไม่เลือกระดับ"))
    if s.get("category"):
        items.append(("category", s["category"]))
    if s.get("imp") is not None:
        items.append(("imp", "แอบอ้าง" if s["imp"] == 1 else "ไม่พบแอบอ้าง"))
    if not s["inc_suspect"]:
        items.append(("susp", "ไม่รวมสัปดาห์น่าสงสัย"))

    parts = ["ทั้งหมด"] + ([str(be(s["year"]))] if s.get("year") is not None else []) + \
            ([month_label(s["month"])] if s.get("month") else []) + \
            ([f"สัปดาห์ {date_th(s['acsc_week'])}"] if s.get("acsc_week") else [])

    detail = ""
    if s.get("acsc_week"):
        r = week_df[week_df["week_start"] == s["acsc_week"]]
        if len(r):
            r = r.iloc[0]
            body = [html.Span(f"สัปดาห์ {date_th(r['week_start'])} – {date_th(r['week_end'])}  ", className="bold")]
            if pd.isna(r["cases"]):
                body.append(html.Span("ไม่มีข้อมูล" if not r["acsc_reported"] else "ไม่รวม (ตัวเลขน่าสงสัย)"))
            else:
                body.append(html.Span(f"{fmt(r['cases'])} คดี · {fmt(r['loss_baht'])} บาท"
                                      f"{' (ปัดเป็นล้านบาท)' if r['loss_precision'] == 'rounded' else ''}  "))
            if isinstance(r["source_url"], str):
                body.append(html.A("ข่าวต้นทาง", href=r["source_url"], target="_blank", rel="noopener"))
            detail = html.Div(body)

    t1 = Q.t1(s)
    t1["date"] = t1["date"].map(date_th)
    t1["ai_level"] = t1["ai_level"].map(lambda x: (LEVEL_TH[x] + " · ต้องตรวจสอบ") if x in LEVEL_TH else "")
    t1["link"] = t1["url"].map(link_md)
    table = evidence_table("t1-tbl", t1[["date", "source", "title", "category", "ai_level", "reason", "evidence_snippet", "link"]], [
        ("date", "วันที่", ""), ("source", "แหล่ง", ""), ("title", "หัวข้อ (เลื่อนเมาส์ดูข้อความหลักฐาน)", ""),
        ("category", "หมวด", ""), ("ai_level", "ระดับ", ""), ("reason", "คำที่ตรง", ""), ("link", "ลิงก์", "md")],
        tooltip="evidence_snippet")

    find = [f"AIID บันทึก Deepfake {fmt(n_df)} เหตุการณ์ในช่วงที่เลือก",
            f"AFNC ตัดสินข่าวเท็จเกี่ยวกับ AI อย่างน้อย {n_ai} โพสต์"]
    if not acsc_empty:
        find.append(f"ACSC แถลง {fmt(k34['cases'])} คดี ความเสียหาย {fmt(k34['loss'])} บาท")
    find.append(_ytd_text())
    limit = ["ข่าว AI เป็นค่าขั้นต่ำ (เนื้อหาในไฟล์ถูกตัด) และทุกรายการยังต้องตรวจสอบ",
             "AIID นับเฉพาะเหตุการณ์ที่มีคนบันทึก ปีล่าสุดอาจต่ำเพราะบันทึกล่าช้า สรุปไม่ได้ว่า Deepfake ลดลง",
             "ไม่มีตัวแปรบอกว่าคดี ACSC เกี่ยวกับ AI และข้อมูลแต่ละชุดเชื่อมกันได้แค่ช่วงเวลา ไม่ใช่เหตุและผล",
             "ยอดเข้าชมสะสมถึงวันเก็บข้อมูล ไม่ใช่ความน่าเชื่อถือหรือความรุนแรง",
             "ความเสียหายช่วงหลังถูกปัดเป็นล้านบาท เดือนที่มีสัปดาห์ขาดจะมียอดรวมต่ำ"]
    return dict(
        controls=(s["y0"], s["y1"], s["levels"], s["category"], s["imp"], ["1"] if s["inc_suspect"] else []),
        chips=chips(items, "t1chip"), crumb=breadcrumb(parts), k=[k11, k12, k13, k14], cards=cards,
        g1=g1, g3=g3, g5=g5, detail=detail, table=table,
        impchip=("แอบอ้างหน่วยงาน/บุคคล ✓" if s.get("imp") == 1 else "เฉพาะที่แอบอ้างหน่วยงาน/บุคคล"),
        find=note_box("ข้อค้นพบ", find, "finding"), limit=note_box("ข้อจำกัดของข้อมูล", limit, "limit"))


def register(app, stores):
    graphs = ["t1-g1", "t1-g3", "t1-g5"]

    @app.callback(
        Output("store-tab1", "data"),
        Input("t1-y0", "value"), Input("t1-y1", "value"), Input("t1-levels", "value"), Input("t1-category", "value"),
        Input("t1-imp", "value"), Input("t1-susp", "value"), Input("t1-clear", "n_clicks"),
        Input("t1-back", "n_clicks"), Input("t1-impchip", "n_clicks"), Input({"t": "t1chip", "k": ALL}, "n_clicks"),
        *[Input(g, "clickData") for g in graphs], State("store-tab1", "data"), prevent_initial_call=True)
    def upd(*args):
        cur = args[-1]
        trig = ctx.triggered_id
        val = ctx.triggered[0]["value"] if ctx.triggered else None
        if trig is None:
            raise PreventUpdate
        free = ("t1-levels", "t1-susp", "t1-category", "t1-imp")
        if isinstance(trig, dict):
            if not val:
                raise PreventUpdate
            s = dict(cur)
            k = trig["k"]
            if k == "range":
                s.update(y0=DEFAULTS[1]["y0"], y1=DEFAULTS[1]["y1"], level="year", year=None, month=None, acsc_week=None)
            elif k == "year":
                s.update(year=None, month=None, level="year", acsc_week=None)
            elif k == "month":
                s.update(month=None, level="month", acsc_week=None)
            elif k == "levels":
                s["levels"] = list(DEFAULTS[1]["levels"])
            elif k in ("category", "imp"):
                s[k] = None
            elif k == "susp":
                s["inc_suspect"] = True
        elif trig in graphs:
            if not val or not val.get("points"):
                raise PreventUpdate
            s = _click_state(cur, trig, val["points"][0])
        else:
            if trig not in free and not val:
                raise PreventUpdate
            s = _update_state(cur, trig, val)
        if s == cur:
            raise PreventUpdate
        return s

    outs = [Output("t1-y0", "value"), Output("t1-y1", "value"), Output("t1-levels", "value"),
            Output("t1-category", "value"), Output("t1-imp", "value"), Output("t1-susp", "value"),
            Output("t1-chips", "children"), Output("t1-crumb", "children"),
            Output("t1-k11", "children"), Output("t1-k12", "children"), Output("t1-k13", "children"),
            Output("t1-k14", "children"), Output("t1-cards", "children"),
            Output("t1-g1", "figure"), Output("t1-g3", "figure"), Output("t1-impchip", "children"),
            Output("t1-g5", "figure"), Output("t1-detail", "children"), Output("t1-table", "children"),
            Output("t1-find", "children"), Output("t1-limit", "children")] + \
           [Output(g, "clickData") for g in graphs]

    @app.callback(*outs, Input("store-tab1", "data"), Input("store-theme", "data"))
    def rend(s, theme):
        r = render(s, theme)
        return (*r["controls"], r["chips"], r["crumb"], *r["k"], r["cards"], r["g1"], r["g3"], r["impchip"], r["g5"],
                r["detail"], r["table"], r["find"], r["limit"], None, None, None)

    @app.callback(Output("t1-dl", "data"), Input("t1-dl-btn", "n_clicks"), State("store-tab1", "data"),
                  prevent_initial_call=True)
    def dl(n, s):
        if not n:
            raise PreventUpdate
        return filtered_download("1", s)
