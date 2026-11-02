"""แท็บ 1 — AI และภัยออนไลน์ในไทย (AIID + AFNC + ACSC)"""
import pandas as pd
from dash import html, dcc, Input, Output, State, ALL, ctx, no_update
from dash.exceptions import PreventUpdate

from .. import queries as Q, figures as F
from ..components import chipbar, crumbbar, kpi, notice, note_box, chips, breadcrumb, graph, evidence_table, news_card, link_md, fmt
from ..state import DEFAULTS, be, month_label, date_th

LEVEL_TH = {"mention": "กล่าวถึง AI", "media_evidence": "มีคำบ่งชี้ว่าใช้ AI สร้างสื่อ"}
YEARS = list(range(2015, 2027))


def layout():
    return html.Section([
        html.H2("คำถามหลัก: เหตุการณ์ Deepfake ที่บันทึกทั่วโลก ข่าวเท็จที่เกี่ยวกับ AI ในไทย และคดีหลอกลวงออนไลน์ "
                "เปลี่ยนแปลงอย่างไรในช่วงเวลาเดียวกัน", className="question"),
        html.Div([
            html.Label(["ปีเริ่ม (พ.ศ.)", dcc.Dropdown(id="t1-y0", clearable=False,
                       options=[{"label": str(be(y)), "value": y} for y in YEARS])]),
            html.Label(["ปีสิ้นสุด (พ.ศ.)", dcc.Dropdown(id="t1-y1", clearable=False,
                       options=[{"label": str(be(y)), "value": y} for y in YEARS])]),
            html.Label(["ระดับข่าว AI", dcc.Checklist(id="t1-levels", options=[
                {"label": " กล่าวถึง AI", "value": "mention"},
                {"label": " มีคำบ่งชี้ว่าใช้ AI สร้างสื่อ", "value": "media_evidence"}], className="check")]),
            html.Label(["หมวดข่าว AI", dcc.Dropdown(id="t1-category", placeholder="ทุกหมวด",
                       options=[{"label": c, "value": c} for c in Q.categories_ai()])]),
            html.Label(["แอบอ้างหน่วยงาน/บุคคล", dcc.Dropdown(id="t1-imp", placeholder="ทั้งหมด", clearable=True,
                        options=[{"label": "เฉพาะที่พบคำว่าแอบอ้าง", "value": 1},
                                 {"label": "เฉพาะที่ไม่พบ", "value": 0}])]),
            html.Label(["ACSC สัปดาห์น่าสงสัย", dcc.Checklist(id="t1-susp", options=[
                {"label": " รวมสัปดาห์ที่ตัวเลขน่าสงสัย", "value": "1"}], className="check")]),
        ], className="filters"),
        chipbar("t1"),
        crumbbar("t1-crumb", "t1-back"),
        html.Div([html.Div(id="t1-k11", className="kcell"), html.Div(id="t1-k12", className="kcell"),
                  html.Div(id="t1-k13", className="kcell"), html.Div(id="t1-k14", className="kcell")], className="kpis"),
        html.H3("ข่าวเด่นจาก AFNC (ยอดเข้าชม ณ วันที่เก็บข้อมูล 1 พ.ย. 2569)"),
        html.Div(id="t1-cards", className="cards"),
        html.Div([
            html.Div([html.H3("Deepfake ใน AIID และข่าวเท็จเกี่ยวกับ AI ใน AFNC"), graph("t1-g1"),
                      html.Div(id="t1-n1"),
                      html.Div("แตะจุดบนเส้นเพื่อเจาะลงปี เดือน และรายการ", className="muted small")], className="panel"),
            html.Div([html.H3("ข่าว AI อยู่หมวดไหนมาก"), graph("t1-g3"),
                      html.Div([html.Button(id="t1-impchip", n_clicks=0, className="chip")], className="chiprow"),
                      html.Div(id="t1-n3")], className="panel"),
        ], className="two"),
        html.Div([
            html.H3("คดีหลอกลวงออนไลน์ (ACSC) · คดีต่อสัปดาห์และความเสียหาย"),
            crumbbar("t1-acrumb", "t1-acsc-back"),
            html.Div(id="t1-n5"),
            graph("t1-g5"), graph("t1-g6"),
            html.Div(id="t1-detail", className="detail"),
        ], className="panel wide"),
        html.Div(id="t1-info", className="detail"),
        html.Div([html.H3("ตารางหลักฐาน (กดลิงก์เพื่อเปิดต้นฉบับ)"), html.Div(id="t1-table")], className="panel wide"),
        html.Div([html.Div(id="t1-find"), html.Div(id="t1-limit")], className="two"),
    ], id="tab1-body")


def _update_state(cur, trig, val):
    s = dict(cur)
    k = trig if isinstance(trig, str) else None
    if k == "t1-y0" or k == "t1-y1":
        key = "y0" if k == "t1-y0" else "y1"
        s[key] = int(val)
        if s["y0"] > s["y1"]:
            s["y0"], s["y1"] = s["y1"], s["y0"]
        s.update(level="year", year=None, month=None)
    elif k == "t1-levels":
        s["levels"] = val or []
    elif k == "t1-category":
        s["category"] = val
    elif k == "t1-imp":
        s["imp"] = val
    elif k == "t1-susp":
        s["inc_suspect"] = bool(val)
    elif k == "t1-impchip":
        s["imp"] = None if s.get("imp") == 1 else 1
    elif k == "t1-clear":
        keep = {x: s[x] for x in ("y0", "y1")}
        s = {**DEFAULTS[1], **keep}
    elif k == "t1-back":
        if s["level"] == "items":
            s.update(level="month", month=None)
        elif s["level"] == "month":
            s.update(level="year", year=None, month=None)
    elif k == "t1-acsc-back":
        if s.get("acsc_week"):
            s["acsc_week"] = None
        elif s.get("acsc_month") or s["acsc_level"] == "week":
            s.update(acsc_month=None, acsc_level="month")
    return s


def _click_state(cur, gid, cd):
    s = dict(cur)
    pt = cd["points"][0]
    c = pt.get("customdata")
    if isinstance(c, list):
        c = c[0]
    if gid == "t1-g1":
        if s["level"] == "year":
            s.update(year=int(c), month=None, level="month")
        else:
            s.update(month=str(c), level="items")
    elif gid == "t1-g3":
        s["category"] = None if s.get("category") == c else c
    elif gid in ("t1-g5", "t1-g6"):
        if s["acsc_level"] == "month" and not s.get("acsc_month"):
            s.update(acsc_month=str(c), acsc_level="week", acsc_week=None)
        else:
            s["acsc_week"] = str(c)
    return s


def _ytd_text():
    d = Q.ytd_compare()
    out = []
    for r in d.itertuples():
        a, b = int(r.y2025), int(r.y2026)
        if a == 0:
            ch = "คำนวณไม่ได้"
        else:
            ch = f"{(b - a) / a * 100:+.1f}%"
        base = f" (ฐาน {a} → {b})" if a < 10 else f" ({a:,} → {b:,})"
        out.append(f"{r.metric} ปี 2569 เทียบช่วงเดียวกันของปี 2568: {ch}{base}")
    return out


def render(s, theme):
    # ---- KPI ----
    n_df = Q.k11(s)
    ai = Q.k12(s)
    k34 = Q.k13_14(s)
    acsc_rng = Q.q("SELECT MIN(week_start) a, MAX(week_end) b FROM acsc_week").iloc[0]
    acsc_empty = k34["cases"] is None
    alt = Q.k13_14(s, inc_suspect=not s["inc_suspect"]) if not acsc_empty else None
    k11 = kpi("เหตุการณ์ Deepfake ที่บันทึกทั่วโลก", fmt(n_df), "เหตุการณ์ · แหล่ง AIID")
    k12 = kpi("ข่าวเท็จที่เกี่ยวกับ AI (ขั้นต่ำ)", fmt(ai["mention"] + ai["media_evidence"]), "โพสต์ · แหล่ง AFNC",
              extra=f"กล่าวถึง AI {ai['mention']} · มีคำบ่งชี้ว่าใช้ AI สร้างสื่อ {ai['media_evidence']}")
    if acsc_empty:
        k13 = kpi("คดีที่แจ้ง (ACSC)", "ไม่มีข้อมูล", f"ไม่มีข้อมูล ACSC ในช่วงที่เลือก (ข้อมูลเริ่ม {date_th(acsc_rng['a'])})")
        k14 = kpi("ความเสียหาย (ACSC)", "ไม่มีข้อมูล", "บาท")
    else:
        diff_txt = ""
        if alt and alt["cases"] is not None:
            with_s, without_s = (k34, alt) if s["inc_suspect"] else (alt, k34)
            diff_txt = (f"ผลต่างเมื่อรวม/ไม่รวมสัปดาห์น่าสงสัย: {fmt(with_s['cases'] - without_s['cases'])} คดี · "
                        f"{fmt(with_s['loss'] - without_s['loss'])} บาท")
        k13 = kpi("คดีที่แจ้ง (ACSC)", fmt(k34["cases"]), f"คดี · {k34['weeks']} สัปดาห์ที่มีแถลง")
        k14 = kpi("ความเสียหายรวม · ต่อคดี", fmt(k34["loss"]), f"บาท · เฉลี่ย {fmt(k34['per_case'], 2)} บาท/คดี",
                  extra=diff_txt or None)

    # ---- cards ----
    top, low, total = Q.c14(s)
    if total == 0:
        cards = html.Div("ไม่มีข่าว AI ในชุดที่เลือก", className="empty")
    else:
        kids = [news_card("อันดับ 1 · ยอดเข้าชมสูงสุด", top.iloc[0], big=True)]
        small = [news_card(f"อันดับ {i + 1}", top.iloc[i]) for i in range(1, len(top))]
        kids.append(html.Div(small, className="small-cards"))
        if total >= 4:
            kids.append(html.Div(news_card("ยอดเข้าชมต่ำสุดในชุดนี้", low.iloc[0]), className="low-card"))
        else:
            kids.append(html.Div(f"มีข่าวในชุดนี้ {total} รายการ (ไม่แสดงการ์ดต่ำสุดซ้ำ)", className="empty low-card"))
        cards = html.Div(kids, className="cards-grid")

    # ---- charts ----
    g1 = F.fig_c11_c12(s, Q.c11(s), Q.c12(s), theme)
    notes1 = []
    if s.get("category") or s.get("imp") is not None or len(s["levels"]) < 2:
        notes1.append(notice("ตัวกรองหมวด ระดับ AI และแอบอ้าง ไม่มีผลกับเส้น Deepfake (AIID)"))
    c13df = Q.c13(s)
    g3 = F.fig_c13(c13df, s, theme)
    n3 = [notice("ตัวกรองหมวดใช้ไฮไลต์แท่ง ไม่ตัดหมวดอื่นออก · ตัวกรองนี้ไม่มีผลกับเส้น Deepfake และ ACSC")]
    week_df, month_df = Q.c15(s), Q.c15_month(s)
    g5 = F.fig_acsc_bar(s, week_df, month_df, theme)
    g6 = F.fig_acsc_loss(s, week_df, month_df, theme)
    n5 = [notice("ตัวกรองข่าว AI (ระดับ หมวด แอบอ้าง) ไม่มีผลกับ ACSC · ไม่มีตัวเลขใดอ้างว่าเป็นคดีหรือความเสียหายจาก AI"),
          html.Div("จุดกลวง = ตัวเลขถูกปัดเป็นล้านบาท · สีเตือน = สัปดาห์ที่ตัวเลขน่าสงสัย · ช่องว่าง = ไม่มีการแถลง (ไม่ใช่ 0)",
                   className="muted small")]
    if s["y1"] < 2025 or (s.get("year") is not None and s["year"] < 2025):
        n5.append(html.Div(f"ไม่มีข้อมูล ACSC ก่อน {date_th(acsc_rng['a'])}", className="empty"))

    # ---- chips ----
    items = []
    if (s["y0"], s["y1"]) != (DEFAULTS[1]["y0"], DEFAULTS[1]["y1"]):
        items.append(("range", f"ปี {be(s['y0'])}–{be(s['y1'])}"))
    if s.get("year") is not None:
        items.append(("year", f"ปี {be(s['year'])}"))
    if s.get("month"):
        items.append(("month", month_label(s["month"])))
    if len(s["levels"]) < 2:
        items.append(("levels", " / ".join(LEVEL_TH[x] for x in s["levels"]) or "ไม่เลือกระดับ"))
    if s.get("category"):
        items.append(("category", s["category"]))
    if s.get("imp") is not None:
        items.append(("imp", "แอบอ้างหน่วยงาน/บุคคล" if s["imp"] == 1 else "ไม่พบคำว่าแอบอ้าง"))
    if not s["inc_suspect"]:
        items.append(("susp", "ไม่รวมสัปดาห์น่าสงสัย"))
    chips_out = chips(items, "t1chip", "t1-clear")

    parts = ["ทั้งหมด"] + ([str(be(s["year"]))] if s.get("year") is not None else []) + \
            ([month_label(s["month"])] if s.get("month") else [])
    crumb = breadcrumb(parts, "t1-back")
    aparts = ["ทุกเดือน"] + ([month_label(s["acsc_month"])] if s.get("acsc_month") else []) + \
             ([f"สัปดาห์ {date_th(s['acsc_week'])}"] if s.get("acsc_week") else [])
    acrumb = breadcrumb(aparts, "t1-acsc-back")

    # ---- detail panels ----
    detail = html.Div("แตะแท่งเดือนเพื่อเจาะลงสัปดาห์ แล้วแตะแท่งสัปดาห์เพื่อดูรายละเอียดและลิงก์ข่าวต้นทาง", className="muted small")
    if s.get("acsc_week"):
        r = week_df[week_df["week_start"] == s["acsc_week"]]
        if len(r):
            r = r.iloc[0]
            body = [html.Div(f"สัปดาห์ {date_th(r['week_start'])} – {date_th(r['week_end'])}", className="bold")]
            if pd.isna(r["cases"]):
                body.append(html.Div("ไม่มีข้อมูล" if not r["acsc_reported"] else "ไม่รวม (ตัวเลขน่าสงสัย)"))
            else:
                body.append(html.Div(f"{fmt(r['cases'])} คดี · {fmt(r['loss_baht'])} บาท · ตัวเลขความเสียหาย: "
                                     f"{'ปัดเป็นล้านบาท' if r['loss_precision'] == 'rounded' else 'ตัวเลขจริง'}"))
            if isinstance(r["flag"], str):
                body.append(html.Div("หมายเหตุ: " + r["flag"], className="muted small"))
            if isinstance(r["source_url"], str):
                body.append(html.A("เปิดข่าวต้นทาง", href=r["source_url"], target="_blank", rel="noopener"))
            detail = html.Div(body)
    # info panel: ค่าของจุดที่เลือก
    info_lines = []
    if s.get("year") is not None:
        d1, d2 = Q.c11({**s, "level": "year", "y0": s["year"], "y1": s["year"]}), None
        dn = int(d1["n"].sum()) if len(d1) else 0
        info_lines.append(f"จุดที่เลือก ปี {be(s['year'])}: Deepfake {dn} เหตุการณ์ (AIID)")
    if s.get("month"):
        info_lines.append(f"เดือน {month_label(s['month'])}: Deepfake {n_df} เหตุการณ์ · ข่าว AI "
                          f"{ai['mention'] + ai['media_evidence']} โพสต์")
    info = html.Div([html.Div(x) for x in info_lines] or [html.Div("แตะจุดบนกราฟเพื่อดูค่าที่นี่ (ไม่ต้องพึ่งการเลื่อนเมาส์)",
                                                                  className="muted small")])

    # ---- table ----
    t1 = Q.t1(s)
    t1["date"] = t1["date"].map(date_th)
    t1["ai_level"] = t1["ai_level"].map(lambda x: LEVEL_TH.get(x, ""))
    t1["link"] = t1["url"].map(link_md)
    t1["review_status"] = t1["review_status"].fillna("")
    table = evidence_table("t1-tbl", t1[["date", "source", "title", "category", "ai_level", "reason", "evidence_snippet",
                                          "review_status", "link"]], [
        ("date", "วันที่", ""), ("source", "แหล่ง", ""), ("title", "หัวข้อ", ""), ("category", "หมวด/โดเมนความเสี่ยง", ""),
        ("ai_level", "ระดับ", ""), ("reason", "เหตุผลที่ถูกเลือก (คำที่ตรง)", ""),
        ("evidence_snippet", "ข้อความหลักฐาน", ""), ("review_status", "สถานะ", ""), ("link", "ลิงก์", "md")])

    # ---- summaries ----
    find = [f"AIID บันทึก Deepfake {fmt(n_df)} เหตุการณ์ในช่วงที่เลือก (นับเฉพาะเหตุการณ์ที่ถูกบันทึก)",
            f"AFNC ตัดสินข่าวเท็จที่เกี่ยวกับ AI อย่างน้อย {ai['mention'] + ai['media_evidence']} โพสต์ "
            f"(กล่าวถึง AI {ai['mention']} · มีคำบ่งชี้ว่าใช้ AI สร้างสื่อ {ai['media_evidence']})"]
    if not acsc_empty:
        find.append(f"ACSC แถลง {fmt(k34['cases'])} คดี ความเสียหาย {fmt(k34['loss'])} บาท "
                    f"(เฉลี่ย {fmt(k34['per_case'], 2)} บาทต่อคดี) ในช่วง {k34['weeks']} สัปดาห์ที่มีแถลง")
    find += _ytd_text()
    find.append("ACSC ไม่มีปีก่อนให้เทียบ จึงคำนวณการเปลี่ยนแปลงเทียบปีก่อนไม่ได้")
    limit = ["จำนวนข่าว AI เป็นค่าขั้นต่ำ เพราะเนื้อหาข่าวในไฟล์ถูกตัดความยาว และทุกรายการยังต้องตรวจสอบ",
             "AIID นับเฉพาะเหตุการณ์ที่เป็นข่าวและมีคนบันทึก ปีล่าสุดอาจต่ำเพราะบันทึกล่าช้า จึงสรุปไม่ได้ว่า Deepfake ลดลง",
             "ไม่มีตัวแปรใดบอกว่าคดี ACSC เกี่ยวกับ AI และตัวเลข ACSC รวบรวมจากข่าว ไม่ใช่ข้อมูลเปิดของตำรวจ",
             "ข้อมูลไม่ได้เชื่อมกันระดับรายการ จึงเทียบได้เฉพาะช่วงเวลา ไม่ใช่เหตุและผล",
             "ยอดเข้าชมเป็นยอดสะสมจนถึงวันที่เก็บข้อมูล ไม่ใช่ความน่าเชื่อถือหรือความรุนแรง",
             "ความเสียหายช่วงหลังถูกปัดเป็นล้านบาท เดือนที่มีสัปดาห์ขาดจะมียอดรวมต่ำ ควรดูบาทต่อคดี"]

    return dict(
        controls=(s["y0"], s["y1"], s["levels"], s["category"], s["imp"], ["1"] if s["inc_suspect"] else []),
        chips=chips_out, crumb=crumb, k=[k11, k12, k13, k14], cards=cards, g1=g1, n1=notes1, g3=g3, n3=n3,
        impchip=("แอบอ้างหน่วยงาน/บุคคล ✓" if s.get("imp") == 1 else "แสดงเฉพาะแอบอ้างหน่วยงาน/บุคคล"),
        g5=g5, g6=g6, n5=n5, acrumb=acrumb, detail=detail, info=info, table=table,
        find=note_box("ข้อค้นพบจากข้อมูล", find, "finding"), limit=note_box("ข้อจำกัด", limit, "limit"),
    )


def register(app, stores):
    graphs = ["t1-g1", "t1-g3", "t1-g5", "t1-g6"]

    @app.callback(
        Output("store-tab1", "data"),
        Input("t1-y0", "value"), Input("t1-y1", "value"), Input("t1-levels", "value"), Input("t1-category", "value"),
        Input("t1-imp", "value"), Input("t1-susp", "value"), Input("t1-clear", "n_clicks"),
        Input("t1-back", "n_clicks"), Input("t1-acsc-back", "n_clicks"), Input("t1-impchip", "n_clicks"),
        Input({"t": "t1chip", "k": ALL}, "n_clicks"),
        *[Input(g, "clickData") for g in graphs],
        State("store-tab1", "data"), prevent_initial_call=True)
    def upd(*args):
        cur = args[-1]
        trig = ctx.triggered_id
        if trig is None or ctx.triggered[0]["value"] in (None, 0, []) and trig not in (
                "t1-levels", "t1-susp", "t1-category", "t1-imp"):
            raise PreventUpdate
        if isinstance(trig, dict):
            s = dict(cur)
            k = trig["k"]
            if k == "range":
                s.update(y0=DEFAULTS[1]["y0"], y1=DEFAULTS[1]["y1"], level="year", year=None, month=None)
            elif k == "year":
                s.update(year=None, month=None, level="year")
            elif k == "month":
                s.update(month=None, level="month")
            elif k == "levels":
                s["levels"] = list(DEFAULTS[1]["levels"])
            elif k == "category":
                s["category"] = None
            elif k == "imp":
                s["imp"] = None
            elif k == "susp":
                s["inc_suspect"] = True
        elif trig in graphs:
            cd = ctx.triggered[0]["value"]
            if not cd or not cd.get("points"):
                raise PreventUpdate
            s = _click_state(cur, trig, cd)
        else:
            val = ctx.triggered[0]["value"]
            s = _update_state(cur, trig, val)
        if s == cur:
            raise PreventUpdate
        return s

    outs = [Output("t1-y0", "value"), Output("t1-y1", "value"), Output("t1-levels", "value"),
            Output("t1-category", "value"), Output("t1-imp", "value"), Output("t1-susp", "value"),
            Output("t1-chips", "children"), Output("t1-crumb", "children"),
            Output("t1-k11", "children"), Output("t1-k12", "children"), Output("t1-k13", "children"),
            Output("t1-k14", "children"), Output("t1-cards", "children"),
            Output("t1-g1", "figure"), Output("t1-n1", "children"), Output("t1-g3", "figure"),
            Output("t1-n3", "children"), Output("t1-impchip", "children"), Output("t1-g5", "figure"),
            Output("t1-g6", "figure"), Output("t1-n5", "children"), Output("t1-acrumb", "children"),
            Output("t1-detail", "children"), Output("t1-info", "children"), Output("t1-table", "children"),
            Output("t1-find", "children"), Output("t1-limit", "children")] + \
           [Output(g, "clickData") for g in graphs]

    @app.callback(*outs, Input("store-tab1", "data"), Input("store-theme", "data"))
    def rend(s, theme):
        r = render(s, theme)
        return (*r["controls"], r["chips"], r["crumb"], *r["k"], r["cards"], r["g1"], r["n1"], r["g3"], r["n3"],
                r["impchip"], r["g5"], r["g6"], r["n5"], r["acrumb"], r["detail"], r["info"], r["table"],
                r["find"], r["limit"], None, None, None, None)
