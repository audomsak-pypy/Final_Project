"""แท็บ 2 — ประเด็นข้อมูลบิดเบือนต่างประเทศกับไทย (EUvsDisinfo + AFNC + AIID)"""
from dash import html, dcc, Input, Output, State, ALL, ctx
from dash.exceptions import PreventUpdate

from .. import queries as Q, figures as F
from ..components import chipbar, crumbbar, kpi, notice, note_box, chips, breadcrumb, graph, evidence_table, link_md, fmt
from ..state import DEFAULTS, be, month_label, date_th

YEARS = list(range(2019, 2027))
BY_CATEGORY = ("health", "finance", "politics")
EU_LAST_YEAR = 2023  # ถึง 1 ส.ค. 2566 (ข้อเท็จจริงของชุดข้อมูล อ่านจากฐานข้อมูลตอนรันด้วย)


def _eu_max_year():
    return int(Q.q("SELECT MAX(year) y FROM eu_debunk")["y"][0])


def _af_min_year():
    return int(Q.q("SELECT MIN(year) y FROM afnc_item")["y"][0])


def layout():
    th = Q.themes()
    return html.Section([
        html.H2("คำถามหลัก: ประเด็นใดปรากฏร่วมกันใน EUvsDisinfo กับข่าวเท็จของ AFNC และประเด็นใดมีสัดส่วนต่างกัน",
                className="question"),
        html.Div([
            html.Label(["ปีเริ่ม (พ.ศ.)", dcc.Dropdown(id="t2-y0", clearable=False,
                       options=[{"label": str(be(y)), "value": y} for y in YEARS])]),
            html.Label(["ปีสิ้นสุด (พ.ศ.)", dcc.Dropdown(id="t2-y1", clearable=False,
                       options=[{"label": str(be(y)), "value": y} for y in YEARS])]),
            html.Label(["ประเด็น (ตั้งเอง)", dcc.Dropdown(id="t2-theme", clearable=False,
                       options=[{"label": r.theme_th, "value": r.theme_id} for r in th.itertuples()])]),
            html.Label(["หมวดข่าวเท็จ AFNC", dcc.Dropdown(id="t2-cat", placeholder="ทุกหมวด")]),
        ], className="filters"),
        html.Div(id="t2-badges", className="badges"),
        chipbar("t2"),
        crumbbar("t2-crumb", "t2-back"),
        html.Div([html.Div(id="t2-k1", className="kcell"), html.Div(id="t2-k2", className="kcell"),
                  html.Div(id="t2-k3", className="kcell")], className="kpis three"),
        html.Div([
            html.Div([html.H3("EUvsDisinfo: สัดส่วนประเด็นต่อปี"), graph("t2-g1")], className="panel"),
            html.Div([html.H3("AFNC: สัดส่วนประเด็นในข่าวเท็จต่อปี"), graph("t2-g2"),
                      html.Div("แถวที่ติดป้าย (จัดตามหมวด) ใช้หมวดทางการของ AFNC ส่วน EU ใช้ keyword จึงวัดคนละวิธี",
                               className="no-effect")], className="panel"),
        ], className="two"),
        html.Div("สเกลสีเดียวกัน 0–100% ของเรื่องทั้งหมดในปีนั้นของแหล่งเดียวกัน · 1 เรื่องอยู่ได้หลายประเด็น "
                 "ผลรวมอาจเกิน 100% · วิธีจัดกลุ่มต่างกัน ในประเด็นสุขภาพ การเงิน การเมือง", className="muted small"),
        html.Div([
            html.Div([html.H3("สัดส่วนของประเด็นที่เลือก 2 แหล่ง"), graph("t2-g3"), html.Div(id="t2-n3")], className="panel"),
            html.Div([html.H3("ข่าวเท็จ AFNC แต่ละปีตามหมวด"), graph("t2-g4"), html.Div(id="t2-n4")], className="panel"),
        ], className="two"),
        html.Div([html.H3("บริบท: AIID บันทึกเหตุการณ์หมวด Misinformation (แกนแยก)"), graph("t2-g5"),
                  html.Div(id="t2-info", className="detail")], className="panel wide"),
        html.Div([html.H3("ตารางหลักฐานในประเด็นและช่วงที่เลือก"),
                  html.Div("วางรายการในประเด็นเดียวกันคู่กัน ไม่ใช่การจับคู่ข่าวต่อข่าว", className="no-effect"),
                  html.Div([html.Div(id="t2-tafnc", className="col"), html.Div(id="t2-teu", className="col")],
                           className="two")], className="panel wide"),
        html.Div([html.Div(id="t2-find"), html.Div(id="t2-limit")], className="two"),
    ], id="tab2-body")


def _update(cur, trig, val):
    s = dict(cur)
    if trig in ("t2-y0", "t2-y1"):
        key = "y0" if trig == "t2-y0" else "y1"
        s[key] = int(val)
        if s["y0"] > s["y1"]:
            s["y0"], s["y1"] = s["y1"], s["y0"]
        s.update(level="year", year=None, month=None)
    elif trig == "t2-theme":
        s["theme"] = val
    elif trig == "t2-cat":
        s["afnc_category"] = val
    elif trig == "t2-clear":
        s = dict(DEFAULTS[2])
    elif trig == "t2-back":
        if s["level"] == "month" and s.get("month"):
            s["month"] = None
        elif s["level"] == "month":
            s.update(level="year", year=None)
        elif s.get("year") is not None:
            s["year"] = None
    return s


def _click(cur, gid, pt):
    s = dict(cur)
    c = pt.get("customdata")
    if gid in ("t2-g1", "t2-g2"):
        tid, y = c
        s.update(theme=tid, year=int(y), level="year", month=None)
    elif gid == "t2-g3" or gid == "t2-g5":
        s.update(year=int(c[0] if isinstance(c, list) else c))
    elif gid == "t2-g4":
        x, cat = c
        if s["level"] == "year":
            s.update(year=int(x), level="month", month=None)
        else:
            s["month"] = str(x)
        s["afnc_category"] = cat
    return s


def render(s, theme):
    years = list(range(s["y0"], s["y1"] + 1))
    eu_max, af_min = _eu_max_year(), _af_min_year()
    no_eu = {y for y in years if y > eu_max}
    no_af = {y for y in years if y < af_min}
    th = Q.themes()
    tmap = dict(zip(th["theme_id"], th["theme_th"]))
    cats = Q.q("SELECT DISTINCT category_th FROM afnc_item WHERE item_type='Verdict' ORDER BY 1")["category_th"].tolist()
    badges = []
    if s["y0"] <= af_min:
        badges.append(html.Span(f"AFNC ปี {be(af_min)} ไม่ใช่ปีเต็ม (เริ่มข้อมูลปลายปี)", className="badge"))
    if s["y1"] >= eu_max:
        badges.append(html.Span(f"EUvsDisinfo มีถึง 1 ส.ค. {be(eu_max)} (ปี {be(eu_max)} ไม่เต็มปี)", className="badge"))
    if no_eu:
        badges.append(html.Span(f"ปี {', '.join(str(be(y)) for y in sorted(no_eu))} ฝั่ง EU ไม่มีข้อมูล (ไม่ใช่ 0)",
                                className="badge"))
    badges.append(html.Span("ใช้คำว่า \"ประเด็นที่ปรากฏร่วมกัน\" ไม่ได้บอกว่าประเด็นข้ามมาจากต่างประเทศ", className="badge muted-b"))

    eu_df, af_df = Q.c21(s["y0"], s["y1"]), Q.c22(s["y0"], s["y1"])
    g1 = F.fig_heatmap(eu_df, years, th, theme, "EUvsDisinfo · % ของการหักล้างในปีนั้น", no_data_years=no_eu,
                       highlight=s["theme"])
    g2 = F.fig_heatmap(af_df, years, th, theme, "AFNC · % ของข่าวเท็จในปีนั้น", no_data_years=no_af, highlight=s["theme"],
                       category_themes=BY_CATEGORY)
    g3 = F.fig_c23(eu_df, af_df, years, s["theme"], tmap[s["theme"]], theme, no_eu, no_af, s["theme"] in BY_CATEGORY)
    n3 = [notice("ช่วงที่ EU ไม่มีข้อมูล เส้นขาด ไม่ใช่ 0 · 1 เรื่องอยู่ได้หลายประเด็น ผลรวมอาจเกิน 100%")]
    if s["theme"] in BY_CATEGORY:
        n3.append(html.Div("วิธีจัดกลุ่มต่างกัน: AFNC จัดตามหมวดทางการ EU จัดตาม keyword", className="no-effect"))
    c24df = Q.c24(s)
    g4 = F.fig_c24(c24df, s, theme)
    n4 = [notice("ตัวกรองประเด็นและ EU ไม่มีผลกับกราฟนี้ (แสดงข่าวเท็จ AFNC ทุกหมวด)")]
    g5 = F.fig_c25(Q.c25(s["y0"], s["y1"]), years, theme)

    k_eu, k_af, k_ai = Q.k2(s)
    kk1 = kpi("EUvsDisinfo", fmt(k_eu), "การหักล้าง (ไม่ใช่จำนวนบทความ)", extra="ไม่มีข้อมูล" if (
        s.get("year") is not None and s["year"] > eu_max) else None)
    kk2 = kpi("AFNC ข่าวเท็จ", fmt(k_af), "ข่าว (ปลอม + บิดเบือน)")
    kk3 = kpi("AIID Misinformation", fmt(k_ai), "เหตุการณ์ (นับแยก ไม่รวมกับสองใบแรก)")

    items = []
    if (s["y0"], s["y1"]) != (DEFAULTS[2]["y0"], DEFAULTS[2]["y1"]):
        items.append(("range", f"ปี {be(s['y0'])}–{be(s['y1'])}"))
    if s.get("year") is not None:
        items.append(("year", f"ปี {be(s['year'])}"))
    if s.get("month"):
        items.append(("month", month_label(s["month"])))
    if s["theme"] != DEFAULTS[2]["theme"]:
        items.append(("theme", tmap[s["theme"]]))
    if s.get("afnc_category"):
        items.append(("cat", s["afnc_category"]))
    crumb = breadcrumb(["ทั้งหมด"] + ([str(be(s["year"]))] if s.get("year") is not None else []) +
                       ([month_label(s["month"])] if s.get("month") else []), "t2-back")

    af, eu = Q.t2(s)
    af2, eu2 = af.copy(), eu.copy()
    for d in (af2, eu2):
        d["date"] = d["date"].map(date_th)
        d["link"] = d["url"].map(link_md)
    cols = [("date", "วันที่", ""), ("headline", "หัวข้อ / keyword", ""), ("matched_by", "วิธีจับคู่", ""),
            ("matched_terms", "คำที่ตรง", ""), ("link", "ลิงก์", "md")]
    tafnc = [html.H4(f"AFNC · ข่าวเท็จ {len(af):,} รายการ"), evidence_table("t2-tbl-af", af2[[c[0] for c in cols]], cols)]
    teu = [html.H4(f"EUvsDisinfo · การหักล้าง {len(eu):,} รายการ"), evidence_table("t2-tbl-eu", eu2[[c[0] for c in cols]], cols)]
    if len(eu) == 0 and s.get("year") is not None and s["year"] > eu_max:
        teu.append(html.Div("ไม่มีข้อมูล EUvsDisinfo ในปีนี้", className="empty"))

    # สรุป
    eu_den, af_den = Q.denominators(s["y0"], s["y1"])
    eu_tot, af_tot = sum(eu_den.values()), sum(af_den.values())
    def share(df, tot):
        g = df.groupby("theme_id")["n"].sum()
        return {t: (100 * g.get(t, 0) / tot if tot else None) for t in tmap}
    sh_eu, sh_af = share(eu_df, eu_tot), share(af_df, af_tot)
    top_eu = max((t for t in tmap if sh_eu[t] is not None), key=lambda t: sh_eu[t], default=None)
    top_af = max((t for t in tmap if sh_af[t] is not None), key=lambda t: sh_af[t], default=None)
    sel = s["theme"]
    find = []
    if top_eu:
        find.append(f"ช่วง {be(s['y0'])}–{be(s['y1'])}: ประเด็นที่ EU มีสัดส่วนสูงสุดคือ {tmap[top_eu]} ({sh_eu[top_eu]:.1f}% ของ "
                    f"{fmt(eu_tot)} การหักล้าง)")
    if top_af:
        find.append(f"ประเด็นที่ AFNC มีสัดส่วนสูงสุดคือ {tmap[top_af]} ({sh_af[top_af]:.1f}% ของ {fmt(af_tot)} ข่าวเท็จ)"
                    + (" · จัดตามหมวด ต่างวิธีกับฝั่ง EU" if top_af in BY_CATEGORY else ""))
    se, sa = sh_eu.get(sel), sh_af.get(sel)
    ne = int(eu_df[eu_df["theme_id"] == sel]["n"].sum()); na = int(af_df[af_df["theme_id"] == sel]["n"].sum())
    find.append(f"ประเด็น {tmap[sel]}: EU {fmt(ne)} เรื่อง ({'คำนวณไม่ได้' if se is None else f'{se:.1f}%'}) · "
                f"AFNC {fmt(na)} ข่าว ({'คำนวณไม่ได้' if sa is None else f'{sa:.1f}%'})"
                + (f" · ฐานน้อยกว่า 10 แสดงจำนวนคู่กับ %" if min(ne, na) < 10 else ""))
    find.append("1 เรื่องอยู่ได้หลายประเด็น ผลรวมของสัดส่วนจึงเกิน 100% ได้")
    limit = ["เทียบได้ตรงกว่าในประเด็นที่ใช้คำค้นทั้งสองฝั่ง ส่วนสุขภาพ การเงิน การเมือง วิธีจัดกลุ่มสองฝั่งต่างกัน",
             "EUvsDisinfo เก็บเฉพาะข้อมูลเท็จฝั่งสนับสนุนรัสเซีย และมีข้อมูลถึงกลางปี " + str(be(eu_max)),
             "ข่าวสงครามใน AFNC ปีหลังส่วนใหญ่เป็นเรื่องอื่น จึงแยกประเด็นความขัดแย้งอื่นต่างหากจากยูเครน และผลขึ้นกับคำค้น",
             "ไม่มีตัวเชื่อมระดับรายการ ตารางหลักฐานจึงเป็นการวางคู่ ไม่ใช่การจับคู่ข่าวต่อข่าว",
             "ภาษาหรือโดเมนของบทความไม่ใช้อนุมานประเทศต้นทางของข้อมูลบิดเบือน",
             "จำนวนข่าวที่ AFNC เผยแพร่ไม่ใช่ปริมาณข่าวปลอมในสังคม"]
    info = html.Div(f"จุดที่เลือก: {('ปี ' + str(be(s['year']))) if s.get('year') is not None else 'ทั้งช่วง'} · "
                    f"ประเด็น {tmap[sel]} · EU {fmt(ne)} เรื่อง · AFNC {fmt(na)} ข่าว")
    return dict(controls=(s["y0"], s["y1"], s["theme"], s.get("afnc_category")),
                catopts=[{"label": c, "value": c} for c in cats], badges=badges,
                chips=chips(items, "t2chip", "t2-clear"), crumb=crumb, k=[kk1, kk2, kk3], g1=g1, g2=g2, g3=g3, n3=n3,
                g4=g4, n4=n4, g5=g5, info=info, tafnc=tafnc, teu=teu,
                find=note_box("ข้อค้นพบจากข้อมูล", find, "finding"), limit=note_box("ข้อจำกัด", limit, "limit"))


def register(app, stores):
    graphs = ["t2-g1", "t2-g2", "t2-g3", "t2-g4", "t2-g5"]

    @app.callback(
        Output("store-tab2", "data"),
        Input("t2-y0", "value"), Input("t2-y1", "value"), Input("t2-theme", "value"), Input("t2-cat", "value"),
        Input("t2-clear", "n_clicks"), Input("t2-back", "n_clicks"), Input({"t": "t2chip", "k": ALL}, "n_clicks"),
        *[Input(g, "clickData") for g in graphs], State("store-tab2", "data"), prevent_initial_call=True)
    def upd(*args):
        cur = args[-1]
        trig = ctx.triggered_id
        val = ctx.triggered[0]["value"] if ctx.triggered else None
        if trig is None:
            raise PreventUpdate
        if isinstance(trig, dict):
            if not val:
                raise PreventUpdate
            s = dict(cur)
            k = trig["k"]
            if k == "range":
                s.update(y0=DEFAULTS[2]["y0"], y1=DEFAULTS[2]["y1"], level="year", year=None, month=None)
            elif k == "year":
                s.update(year=None, month=None, level="year")
            elif k == "month":
                s.update(month=None)
            elif k == "theme":
                s["theme"] = DEFAULTS[2]["theme"]
            elif k == "cat":
                s["afnc_category"] = None
        elif trig in graphs:
            if not val or not val.get("points"):
                raise PreventUpdate
            s = _click(cur, trig, val["points"][0])
        elif trig in ("t2-clear", "t2-back"):
            if not val:
                raise PreventUpdate
            s = _update(cur, trig, val)
        else:
            s = _update(cur, trig, val)
        if s == cur:
            raise PreventUpdate
        return s

    @app.callback(
        Output("t2-y0", "value"), Output("t2-y1", "value"), Output("t2-theme", "value"), Output("t2-cat", "value"),
        Output("t2-cat", "options"), Output("t2-badges", "children"), Output("t2-chips", "children"),
        Output("t2-crumb", "children"), Output("t2-k1", "children"), Output("t2-k2", "children"),
        Output("t2-k3", "children"), Output("t2-g1", "figure"), Output("t2-g2", "figure"), Output("t2-g3", "figure"),
        Output("t2-n3", "children"), Output("t2-g4", "figure"), Output("t2-n4", "children"), Output("t2-g5", "figure"),
        Output("t2-info", "children"), Output("t2-tafnc", "children"), Output("t2-teu", "children"),
        Output("t2-find", "children"), Output("t2-limit", "children"),
        *[Output(g, "clickData") for g in graphs],
        Input("store-tab2", "data"), Input("store-theme", "data"))
    def rend(s, theme):
        r = render(s, theme)
        return (*r["controls"], r["catopts"], r["badges"], r["chips"], r["crumb"], *r["k"], r["g1"], r["g2"], r["g3"],
                r["n3"], r["g4"], r["n4"], r["g5"], r["info"], r["tafnc"], r["teu"], r["find"], r["limit"],
                None, None, None, None, None)
