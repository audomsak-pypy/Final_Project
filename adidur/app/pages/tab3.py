"""แท็บ 3 — เสรีภาพอินเทอร์เน็ต (FOTN + AFNC + EUvsDisinfo)"""
from dash import html, dcc, Input, Output, State, ALL, ctx
from dash.exceptions import PreventUpdate

from .. import queries as Q, figures as F
from ..components import chipbar, crumbbar, kpi, notice, note_box, chips, breadcrumb, graph, fmt
from ..state import DEFAULTS, be


def layout():
    years = Q.fotn_years()
    return html.Section([
        html.H2("คำถามหลัก: ไทยมีคะแนนเสรีภาพอินเทอร์เน็ตอยู่ตรงไหนเมื่อเทียบกับประเทศอื่น และในช่วงเดียวกัน "
                "AFNC เผยแพร่ผลตรวจข่าวจำนวนเท่าไร", className="question"),
        html.Div([
            html.Label(["ปีข้อมูล (พ.ศ.)", dcc.Dropdown(id="t3-fy", clearable=False,
                       options=[{"label": f"{be(y)} (รายงาน {be(y + 1)})", "value": y} for y in years])]),
            html.Label(["กลุ่มประเทศ", dcc.Checklist(id="t3-groups", options=[
                {"label": " อาเซียน (8 ประเทศที่มีข้อมูล)", "value": "ASEAN"}], className="check")]),
            html.Label(["เปรียบเทียบเพิ่ม", dcc.Checklist(id="t3-rus", options=[
                {"label": " รัสเซีย", "value": "1"}], className="check")]),
        ], className="filters"),
        html.Div("ตัวกรองประเทศและปีมีผลกับคะแนน FOTN เท่านั้น ไม่เปลี่ยนค่าฝั่ง AFNC และ EUvsDisinfo", className="no-effect"),
        chipbar("t3"),
        crumbbar("t3-crumb", "t3-back"),
        html.Div([html.Div(id="t3-k1", className="kcell"), html.Div(id="t3-k2", className="kcell"),
                  html.Div(id="t3-k3", className="kcell"), html.Div(id="t3-k4", className="kcell")], className="kpis"),
        html.Div(id="t3-rank", className="rank-line"),
        html.Div([
            html.Div([html.H3("เทียบประเทศในกลุ่มที่เลือก (ปีเดียว)"), graph("t3-g1"),
                      html.Div("แตะแท่งเพื่อเจาะลงประเทศ", className="muted small")], className="panel"),
            html.Div([html.H3("คะแนนมาจากส่วนไหน"), graph("t3-g2"), html.Div(id="t3-info", className="detail")],
                     className="panel"),
        ], className="two"),
        html.Div([html.H3("ไทยเท่านั้น · แสดงคู่กันเพื่อเป็นบริบท ไม่ได้วัดความสัมพันธ์"), graph("t3-g3"),
                  html.Div("ฝั่ง AFNC ไม่เปลี่ยนตามประเทศที่เลือก · ปีแรกของ AFNC ไม่ใช่ปีเต็ม", className="no-effect")],
                 className="panel wide"),
        html.Div([
            html.Div([html.H3("บริบท: EUvsDisinfo บันทึกการหักล้างต่อปี"), graph("t3-g4"),
                      html.Div("ไม่ผูกกับประเทศ · เก็บเฉพาะข้อมูลเท็จฝั่งสนับสนุนรัสเซีย · ตัวกรองด้านบนไม่มีผลกับกราฟนี้",
                               className="no-effect")], className="panel"),
            html.Div([html.H3("แผนที่สถานะ (ส่วนเสริม)"), graph("t3-g5"),
                      html.Div("เสรี / เสรีบางส่วน / ไม่เสรี ตามป้ายใน hover · แตะประเทศเพื่อเจาะลง", className="muted small")],
                     className="panel"),
        ], className="two"),
        html.Div([html.Div(id="t3-find"), html.Div(id="t3-limit")], className="two"),
    ], id="tab3-body")


def _update(cur, trig, val):
    s = dict(cur)
    if trig == "t3-fy":
        s["fy"] = int(val)
    elif trig == "t3-groups":
        s["groups"] = val or []
    elif trig == "t3-rus":
        s["add_rus"] = bool(val)
    elif trig == "t3-clear":
        s = dict(DEFAULTS[3])
    elif trig == "t3-back":
        if s["level"] == "year":
            s["level"] = "country"
        elif s["level"] == "country":
            s.update(level="group", iso3=None)
    return s


def _click(cur, gid, pt):
    s = dict(cur)
    c = pt.get("customdata")
    if isinstance(c, list):
        c = c[0]
    if gid in ("t3-g1", "t3-g5"):
        s.update(iso3=str(c), level="country")
    elif gid == "t3-g2":
        if s["level"] == "group":
            s.update(iso3=str(c), level="country")
        elif s["level"] == "country":
            s.update(fy=int(c), level="year")
    elif gid == "t3-g3":
        if int(c) in Q.fotn_years():
            s["fy"] = int(c)
    return s


def render(s, theme):
    k = Q.k3(s["fy"])
    groups = Q.groups_of(s)
    c31 = Q.c31(s)
    if len(k):
        r = k.iloc[0]
        k1 = kpi("คะแนนไทย", f"{int(r['total_score'])}", "จาก 100 (สูง = เสรีมาก)", source="Freedom House")
        k2 = kpi("สถานะ", r["status_th"], "ตามเกณฑ์ Freedom House")
        k3 = kpi("ปีข้อมูล", str(be(int(r["data_year"]))), "ปีที่การประเมินครอบคลุม (พ.ศ.)")
        k4 = kpi("ปีรายงาน", str(be(int(r["report_edition"]))), "ปีที่รายงานตีพิมพ์ (พ.ศ.)")
    else:
        k1 = kpi("คะแนนไทย", "ไม่มีข้อมูล", "ในปีที่เลือก"); k2 = kpi("สถานะ", "ไม่มีข้อมูล", "")
        k3 = kpi("ปีข้อมูล", str(be(s["fy"])), ""); k4 = kpi("ปีรายงาน", str(be(s["fy"] + 1)), "")
    rank_txt = ""
    th = c31[c31["iso3"] == "THA"]
    gname = " + ".join(("อาเซียน" if g == "ASEAN" else g) for g in groups)
    if len(th):
        rr = th.iloc[0]
        rank_txt = f"อันดับ {int(rr['rank_in_group'])} จาก {int(rr['n_in_group'])} ประเทศ (กลุ่ม: {gname}) ปีข้อมูล {be(s['fy'])}"
        ra = Q.rank_all(s["fy"])
        if len(ra):
            rank_txt += f" · ในทุกประเทศที่มีข้อมูลปีนั้น อันดับ {int(ra.iloc[0]['rnk'])} จาก {int(ra.iloc[0]['n'])} ประเทศ"
    else:
        rank_txt = f"ไทยไม่อยู่ในกลุ่มที่เลือก (กลุ่ม: {gname}) · ไม่คิดอันดับ"
    g1 = F.fig_c31(c31, s, theme)
    d32 = Q.c32(s)
    g2 = F.fig_c32(d32, s, theme)
    c33 = Q.c33()
    g3 = F.fig_c33(c33, theme)
    g4 = F.fig_c34(Q.c34(), theme)
    g5 = F.fig_c35(Q.c35(s["fy"]), theme)

    items = []
    if s["fy"] != DEFAULTS[3]["fy"]:
        items.append(("fy", f"ปีข้อมูล {be(s['fy'])}"))
    if s["groups"] != DEFAULTS[3]["groups"]:
        items.append(("groups", "กลุ่ม: " + (", ".join(s["groups"]) or "ไม่เลือก")))
    if s["add_rus"]:
        items.append(("rus", "+ รัสเซีย"))
    if s.get("iso3"):
        items.append(("iso3", f"ประเทศ {s['iso3']}"))
    crumb_parts = [gname + " " + str(be(s["fy"]))]
    if s["level"] in ("country", "year"):
        nm = d32["name"].iloc[0] if len(d32) else s["iso3"]
        crumb_parts.append(str(nm))
    if s["level"] == "year":
        crumb_parts.append(f"ปีข้อมูล {be(s['fy'])} (องค์ประกอบ)")
    info = html.Div(f"จุดที่เลือก: {crumb_parts[-1]}" + (f" · คะแนนรวม {int(d32.iloc[0][['obstacles_to_access','limits_on_content','violations_of_user_rights']].sum())}" if s["level"] == "year" and len(d32) else ""))

    find = []
    if rank_txt:
        find.append(rank_txt)
    if len(k):
        find.append(f"คะแนนไทย {int(k.iloc[0]['total_score'])} จาก 100 สถานะ {k.iloc[0]['status_th']} (ปีข้อมูล {be(s['fy'])})")
        if len(c31):
            find.append(f"มัธยฐานของกลุ่มที่เลือกคือ {c31['total_score'].median():.1f} คะแนน")
    a = c33.dropna()
    if len(a) >= 2:
        first, last = a.iloc[0], a.iloc[-1]
        find.append(f"ไทยปีข้อมูล {be(int(first['data_year']))}–{be(int(last['data_year']))}: คะแนน {int(first['total_score'])} → "
                    f"{int(last['total_score'])} ขณะที่คำตัดสิน AFNC {int(first['afnc_verdicts']):,} → {int(last['afnc_verdicts']):,} "
                    f"โพสต์ (แสดงคู่กันเป็นบริบท ไม่ได้บอกความสัมพันธ์)")
    limit = ["คะแนนเป็นการประเมินของผู้เชี่ยวชาญ ไม่ใช่การนับเหตุการณ์",
             "จำนวนประเทศในแต่ละปีไม่เท่ากัน ประเทศที่ไม่มีในปีใดคือไม่มีข้อมูล ไม่ใช่ 0 และห้ามรวมหลายปีมาจัดอันดับ",
             "ข้อมูลไม่ได้บอกว่าเสรีภาพสัมพันธ์กับปริมาณข่าวปลอม และไม่ได้บอกว่าประเทศเสรีน้อยมีข่าวปลอมมากหรือน้อยกว่า",
             "จำนวนคำตัดสินของ AFNC ไม่ใช่ปริมาณข่าวปลอมในสังคม ปีแรกของข้อมูลไม่ใช่ปีเต็ม",
             "EUvsDisinfo เก็บเฉพาะฝั่งสนับสนุนรัสเซียและไม่ผูกกับประเทศ จึงใช้เป็นบริบทเท่านั้น"]
    return dict(controls=(s["fy"], s["groups"], ["1"] if s["add_rus"] else []), chips=chips(items, "t3chip", "t3-clear"),
                crumb=breadcrumb(crumb_parts, "t3-back"), k=[k1, k2, k3, k4], rank=rank_txt, g1=g1, g2=g2, info=info,
                g3=g3, g4=g4, g5=g5, find=note_box("ข้อค้นพบจากข้อมูล", find, "finding"),
                limit=note_box("ข้อจำกัด", limit, "limit"))


def register(app, stores):
    graphs = ["t3-g1", "t3-g2", "t3-g3", "t3-g5"]

    @app.callback(
        Output("store-tab3", "data"),
        Input("t3-fy", "value"), Input("t3-groups", "value"), Input("t3-rus", "value"), Input("t3-clear", "n_clicks"),
        Input("t3-back", "n_clicks"), Input({"t": "t3chip", "k": ALL}, "n_clicks"),
        *[Input(g, "clickData") for g in graphs], State("store-tab3", "data"), prevent_initial_call=True)
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
            if k == "fy":
                s["fy"] = DEFAULTS[3]["fy"]
            elif k == "groups":
                s["groups"] = list(DEFAULTS[3]["groups"])
            elif k == "rus":
                s["add_rus"] = False
            elif k == "iso3":
                s.update(iso3=None, level="group")
        elif trig in graphs:
            if not val or not val.get("points"):
                raise PreventUpdate
            s = _click(cur, trig, val["points"][0])
        elif trig in ("t3-clear", "t3-back"):
            if not val:
                raise PreventUpdate
            s = _update(cur, trig, val)
        else:
            s = _update(cur, trig, val)
        if s == cur:
            raise PreventUpdate
        return s

    @app.callback(
        Output("t3-fy", "value"), Output("t3-groups", "value"), Output("t3-rus", "value"),
        Output("t3-chips", "children"), Output("t3-crumb", "children"), Output("t3-k1", "children"),
        Output("t3-k2", "children"), Output("t3-k3", "children"), Output("t3-k4", "children"),
        Output("t3-rank", "children"), Output("t3-g1", "figure"), Output("t3-g2", "figure"),
        Output("t3-info", "children"), Output("t3-g3", "figure"), Output("t3-g4", "figure"), Output("t3-g5", "figure"),
        Output("t3-find", "children"), Output("t3-limit", "children"),
        *[Output(g, "clickData") for g in graphs],
        Input("store-tab3", "data"), Input("store-theme", "data"))
    def rend(s, theme):
        r = render(s, theme)
        return (*r["controls"], r["chips"], r["crumb"], *r["k"], r["rank"], r["g1"], r["g2"], r["info"], r["g3"],
                r["g4"], r["g5"], r["find"], r["limit"], None, None, None, None)
