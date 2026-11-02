"""แท็บ 2 — ประเด็นข้อมูลบิดเบือนต่างประเทศกับไทย (EUvsDisinfo + AFNC + AIID)
ประเด็นและปีที่เลือกที่กราฟใดก็ได้ มีผลกับเฮตแมป เส้น แท่งซ้อน กราฟ AIID KPI และตารางหลักฐาน"""
from dash import html, dcc, Input, Output, State, ALL, ctx
from dash.exceptions import PreventUpdate

from .. import queries as Q, figures as F
from ..components import (kpi, note_box, chips, chipbar, crumbbar, breadcrumb, graph, evidence_table, link_md, fmt,
                         panel)
from ..exports import filtered_download
from ..state import DEFAULTS, be, month_label, date_th

YEARS = list(range(2019, 2027))
BY_CATEGORY = ("health", "finance", "politics")


def _eu_max_year():
    return int(Q.q("SELECT MAX(year) y FROM eu_debunk")["y"][0])


def _af_min_year():
    return int(Q.q("SELECT MIN(year) y FROM afnc_item")["y"][0])


def layout():
    th = Q.themes()
    return html.Section([
        html.H2("ประเด็นไหนปรากฏร่วมกันใน EUvsDisinfo และข่าวเท็จ AFNC", className="question"),
        html.Details([
            html.Summary("ตัวกรอง"),
            html.Div([
                html.Label(["ปีเริ่ม", dcc.Dropdown(id="t2-y0", clearable=False,
                           options=[{"label": str(be(y)), "value": y} for y in YEARS])]),
                html.Label(["ปีสิ้นสุด", dcc.Dropdown(id="t2-y1", clearable=False,
                           options=[{"label": str(be(y)), "value": y} for y in YEARS])]),
                html.Label(["ประเด็น", dcc.Dropdown(id="t2-theme", clearable=False,
                           options=[{"label": r.theme_th, "value": r.theme_id} for r in th.itertuples()])]),
                html.Label(["หมวดข่าวเท็จ AFNC", dcc.Dropdown(id="t2-cat", placeholder="ทุกหมวด")]),
            ], className="filters"),
        ], open=True, className="filter-box"),
        html.Div(id="t2-badges", className="badges"),
        chipbar("t2"),
        crumbbar("t2-crumb", "t2-back"),
        html.Div([html.Div(id="t2-k1", className="kcell"), html.Div(id="t2-k2", className="kcell"),
                  html.Div(id="t2-k3", className="kcell")], className="kpis three"),
        html.Div([
            panel("EUvsDisinfo · สัดส่วนประเด็น", graph("t2-g1"), tag="แตะช่องเพื่อเลือกประเด็นและปี"),
            panel("AFNC · สัดส่วนประเด็นในข่าวเท็จ", graph("t2-g2"), tag="* จัดตามหมวด ต่างวิธีกับ EU"),
        ], className="two"),
        html.Div("สีเดียวกัน 0–100% ของเรื่องทั้งหมดในปีนั้น · 1 เรื่องอยู่ได้หลายประเด็น ผลรวมอาจเกิน 100%",
                 className="foot-note"),
        html.Div([
            panel("ประเด็นที่เลือก 2 แหล่ง", graph("t2-g3"), tag="แตะจุดเพื่อเลือกปี"),
            html.Div([html.Div(id="t2-t4", className="panel-head"), graph("t2-g4")], className="panel"),
        ], className="two"),
        panel("บริบท: AIID Misinformation", graph("t2-g5"), tag="หน่วยเป็นเหตุการณ์ · แกนแยก", cls="wide"),
        html.Div([
            panel("AFNC · ข่าวเท็จในประเด็นนี้", html.Div(id="t2-tafnc")),
            panel("EUvsDisinfo · การหักล้างในประเด็นนี้", html.Div(id="t2-teu"),
                  tag="วางคู่กัน ไม่ใช่การจับคู่ข่าวต่อข่าว"),
        ], className="two"),
        html.Button("ดาวน์โหลด CSV", id="t2-dl-btn", n_clicks=0, className="btn small-btn"),
        dcc.Download(id="t2-dl"),
        html.Div([html.Div(id="t2-find"), html.Div(id="t2-limit")], className="two"),
    ], id="tab2-body")


def _update(cur, trig, val):
    s = dict(cur)
    if trig in ("t2-y0", "t2-y1"):
        s["y0" if trig == "t2-y0" else "y1"] = int(val)
        if s["y0"] > s["y1"]:
            s["y0"], s["y1"] = s["y1"], s["y0"]
        s.update(level="year", year=None, month=None)
    elif trig == "t2-theme":
        s["theme"] = val
    elif trig == "t2-cat":
        s["afnc_category"] = val
    elif trig == "t2-clear":
        s = {**DEFAULTS[2], "y0": s["y0"], "y1": s["y1"]}
    elif trig == "t2-back":
        if s.get("month"):
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
        # เฮตแมปไม่ส่ง customdata กลับมา ใช้ป้ายแกน (ชื่อประเด็น, ปี พ.ศ.) แปลงกลับ
        th = Q.themes()
        ids = dict(zip(th["theme_th"], th["theme_id"]))
        tid = ids.get(str(pt.get("y", "")).rstrip(" *"))
        if tid is None or pt.get("x") is None:
            return s
        s.update(theme=tid, year=int(pt["x"]) - 543, level="year", month=None)
    elif gid in ("t2-g3", "t2-g5"):
        s.update(year=int(c[0] if isinstance(c, list) else c), level="year", month=None)
    elif gid == "t2-g4":
        x, cat = c
        if s["level"] == "year":
            s.update(year=int(x), level="month", month=None)
        else:
            s["month"] = str(x)
        s["afnc_category"] = None if s.get("afnc_category") == cat else cat
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
        badges.append(html.Span(f"AFNC ปี {be(af_min)} ไม่ใช่ปีเต็ม", className="badge"))
    if s["y1"] >= eu_max:
        badges.append(html.Span(f"EUvsDisinfo มีถึง 1 ส.ค. {be(eu_max)}", className="badge"))
    if no_eu:
        badges.append(html.Span("ปีหลังจากนั้นฝั่ง EU ไม่มีข้อมูล (ไม่ใช่ 0)", className="badge"))

    sel_year = s.get("year") if s["level"] == "year" or s.get("year") is not None else None
    eu_df, af_df = Q.c21(s["y0"], s["y1"]), Q.c22(s["y0"], s["y1"])
    g1 = F.fig_heatmap(eu_df, years, th, theme, "", no_data_years=no_eu, highlight=s["theme"], sel_year=sel_year)
    g2 = F.fig_heatmap(af_df, years, th, theme, "", no_data_years=no_af, highlight=s["theme"], sel_year=sel_year,
                       category_themes=BY_CATEGORY)
    g3 = F.fig_c23(eu_df, af_df, years, s["theme"], tmap[s["theme"]], theme, no_eu, no_af, s["theme"] in BY_CATEGORY,
                   sel_year)
    order = sorted(cats)
    c24 = Q.c24(s)
    g4 = F.fig_c24(c24, s, theme, order, tmap[s["theme"]])
    g5 = F.fig_c25(Q.c25(s["y0"], s["y1"]), years, theme, sel_year)
    t4 = [html.H3(f"AFNC · {tmap[s['theme']]} แยกหมวด"), html.Span("แตะแท่งเพื่อเจาะลง/เลือกหมวด", className="tag")]

    k_eu, k_af, k_ai = Q.k2(s)
    kk1 = kpi("EUvsDisinfo", fmt(k_eu), "การหักล้าง", tone="a")
    kk2 = kpi("AFNC ข่าวเท็จ", fmt(k_af), "ข่าว (ปลอม + บิดเบือน)", tone="c")
    kk3 = kpi("AIID Misinformation", fmt(k_ai), "เหตุการณ์ (นับแยก)", tone="e")

    items = []
    if (s["y0"], s["y1"]) != (DEFAULTS[2]["y0"], DEFAULTS[2]["y1"]):
        items.append(("range", f"{be(s['y0'])}–{be(s['y1'])}"))
    if s.get("year") is not None:
        items.append(("year", f"ปี {be(s['year'])}"))
    if s.get("month"):
        items.append(("month", month_label(s["month"])))
    if s["theme"] != DEFAULTS[2]["theme"]:
        items.append(("theme", tmap[s["theme"]]))
    if s.get("afnc_category"):
        items.append(("cat", s["afnc_category"]))
    crumb = breadcrumb(["ทั้งหมด"] + ([str(be(s["year"]))] if s.get("year") is not None else []) +
                       ([month_label(s["month"])] if s.get("month") else []))

    af, eu = Q.t2(s)
    for d in (af, eu):
        d["date"] = d["date"].map(date_th)
        d["link"] = d["url"].map(link_md)
    cols = [("date", "วันที่", ""), ("headline", "หัวข้อ / keyword", ""), ("matched_terms", "คำที่ตรง", ""),
            ("link", "ลิงก์", "md")]
    tafnc = [html.Div(f"{len(af):,} รายการ", className="count"), evidence_table("t2-tbl-af", af[[c[0] for c in cols]], cols)]
    teu = [html.Div(f"{len(eu):,} รายการ", className="count"), evidence_table("t2-tbl-eu", eu[[c[0] for c in cols]], cols)]

    eu_den, af_den = Q.denominators(s["y0"], s["y1"])
    eu_tot, af_tot = sum(eu_den.values()), sum(af_den.values())

    def share(df, tot):
        g = df.groupby("theme_id")["n"].sum()
        return {t: (100 * g.get(t, 0) / tot if tot else None) for t in tmap}
    sh_eu, sh_af = share(eu_df, eu_tot), share(af_df, af_tot)
    top_eu = max((t for t in tmap if sh_eu[t] is not None), key=lambda t: sh_eu[t], default=None)
    top_af = max((t for t in tmap if sh_af[t] is not None), key=lambda t: sh_af[t], default=None)
    sel = s["theme"]
    ne = int(eu_df[eu_df["theme_id"] == sel]["n"].sum()); na = int(af_df[af_df["theme_id"] == sel]["n"].sum())
    find = []
    if top_eu:
        find.append(f"EU: ประเด็นสูงสุดคือ {tmap[top_eu]} ({sh_eu[top_eu]:.0f}%)")
    if top_af:
        find.append(f"AFNC: ประเด็นสูงสุดคือ {tmap[top_af]} ({sh_af[top_af]:.0f}%)"
                    + (" · จัดตามหมวด" if top_af in BY_CATEGORY else ""))
    find.append(f"{tmap[sel]}: EU {fmt(ne)} เรื่อง · AFNC {fmt(na)} ข่าว")
    limit = ["สุขภาพ การเงิน การเมือง: AFNC จัดตามหมวดทางการ EU จัดตาม keyword จึงวัดคนละวิธี",
             "EUvsDisinfo เก็บเฉพาะฝั่งสนับสนุนรัสเซียและมีข้อมูลถึงกลางปี " + str(be(eu_max)),
             "ข่าวสงครามใน AFNC ปีหลังส่วนใหญ่เป็นเรื่องอื่น จึงแยกประเด็นความขัดแย้งอื่นจากยูเครน",
             "ไม่มีตัวเชื่อมระดับรายการ ใช้ภาษา/โดเมนอนุมานประเทศต้นทางไม่ได้",
             "จำนวนข่าวที่ AFNC เผยแพร่ไม่ใช่ปริมาณข่าวปลอมในสังคม"]
    return dict(controls=(s["y0"], s["y1"], s["theme"], s.get("afnc_category")),
                catopts=[{"label": c, "value": c} for c in cats], badges=badges, chips=chips(items, "t2chip"),
                crumb=crumb, k=[kk1, kk2, kk3], g1=g1, g2=g2, g3=g3, t4=t4, g4=g4, g5=g5, tafnc=tafnc, teu=teu,
                find=note_box("ข้อค้นพบ", find, "finding"), limit=note_box("ข้อจำกัดของข้อมูล", limit, "limit"))


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
        Output("t2-t4", "children"), Output("t2-g4", "figure"), Output("t2-g5", "figure"),
        Output("t2-tafnc", "children"), Output("t2-teu", "children"),
        Output("t2-find", "children"), Output("t2-limit", "children"),
        *[Output(g, "clickData") for g in graphs],
        Input("store-tab2", "data"), Input("store-theme", "data"))
    def rend(s, theme):
        r = render(s, theme)
        return (*r["controls"], r["catopts"], r["badges"], r["chips"], r["crumb"], *r["k"], r["g1"], r["g2"], r["g3"],
                r["t4"], r["g4"], r["g5"], r["tafnc"], r["teu"], r["find"], r["limit"], None, None, None, None, None)

    @app.callback(Output("t2-dl", "data"), Input("t2-dl-btn", "n_clicks"), State("store-tab2", "data"),
                  prevent_initial_call=True)
    def dl(n, s):
        if not n:
            raise PreventUpdate
        return filtered_download("2", s)
