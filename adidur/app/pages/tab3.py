"""แท็บ 3 — เสรีภาพอินเทอร์เน็ต (FOTN + AFNC + EUvsDisinfo)
ปีและประเทศที่เลือกที่กราฟใดก็ได้ มีผลกับ KPI อันดับ แท่งเทียบ แท่งองค์ประกอบ เส้นไทย/AFNC กราฟ EU และแผนที่"""
from dash import html, dcc, Input, Output, State, ALL, ctx
from dash.exceptions import PreventUpdate

from .. import queries as Q, figures as F
from ..components import kpi, note_box, chips, chipbar, crumbbar, breadcrumb, graph, panel
from ..exports import filtered_download
from ..state import DEFAULTS, be


def layout():
    years = Q.fotn_years()
    return html.Section([
        html.H2("ไทยอยู่ตรงไหนในคะแนนเสรีภาพอินเทอร์เน็ต", className="question"),
        html.Details([
            html.Summary("ตัวกรอง"),
            html.Div([
                html.Label(["ปีข้อมูล", dcc.Dropdown(id="t3-fy", clearable=False,
                           options=[{"label": f"{be(y)} (รายงาน {be(y + 1)})", "value": y} for y in years])]),
                html.Label(["กลุ่มประเทศ", dcc.Checklist(id="t3-groups", options=[
                    {"label": " อาเซียน", "value": "ASEAN"}], className="check")]),
                html.Label(["เปรียบเทียบเพิ่ม", dcc.Checklist(id="t3-rus", options=[
                    {"label": " รัสเซีย", "value": "1"}], className="check")]),
            ], className="filters"),
        ], open=True, className="filter-box"),
        chipbar("t3"),
        crumbbar("t3-crumb", "t3-back"),
        html.Div([html.Div(id="t3-k1", className="kcell"), html.Div(id="t3-k2", className="kcell"),
                  html.Div(id="t3-k3", className="kcell"), html.Div(id="t3-k4", className="kcell")], className="kpis"),
        html.Div(id="t3-rank", className="rank-line"),
        html.Div([
            panel("เทียบประเทศในกลุ่ม", graph("t3-g1"), tag="แตะแท่งเพื่อเลือกประเทศ"),
            panel("คะแนนมาจากส่วนไหน", graph("t3-g2"), tag="แตะแท่งปีเพื่อเลือกปี"),
        ], className="two"),
        html.Div([
            panel("ไทย: คะแนนและคำตัดสิน AFNC", graph("t3-g3"), tag="ไทยเท่านั้น · เป็นบริบท ไม่ได้วัดความสัมพันธ์"),
            panel("EUvsDisinfo ต่อปี", graph("t3-g4"), tag="ไม่ผูกกับประเทศ"),
        ], className="two"),
        panel("แผนที่สถานะ (เสรี · เสรีบางส่วน · ไม่เสรี)", graph("t3-g5"), tag="แตะประเทศเพื่อเลือก", cls="wide"),
        html.Button("ดาวน์โหลด CSV", id="t3-dl-btn", n_clicks=0, className="btn small-btn"),
        dcc.Download(id="t3-dl"),
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
    c = pt.get("customdata") or pt.get("location")  # แผนที่ส่ง location (iso3) กลับมาแทน customdata
    if isinstance(c, list):
        c = c[0]
    if gid in ("t3-g1", "t3-g5"):
        s.update(iso3=str(c), level="country")
    elif gid == "t3-g2":
        if s["level"] == "group":
            s.update(iso3=str(c), level="country")
        else:
            s.update(fy=int(c), level="year")
    elif gid in ("t3-g3", "t3-g4"):
        if int(c) in Q.fotn_years():
            s["fy"] = int(c)
    return s


def render(s, theme):
    iso = s.get("iso3") or "THA"
    k = Q.k3(s["fy"], iso)
    groups = Q.groups_of(s)
    c31 = Q.c31(s)
    if len(k):
        r = k.iloc[0]
        k1 = kpi(f"คะแนน{r['name']}", f"{int(r['total_score'])}", "จาก 100 (สูง = เสรีมาก)", tone="a")
        k2 = kpi("สถานะ", r["status_th"], "Freedom House", tone="b")
        k3 = kpi("ปีข้อมูล", str(be(int(r["data_year"]))), "ปีที่ประเมิน (พ.ศ.)", tone="c")
        k4 = kpi("ปีรายงาน", str(be(int(r["report_edition"]))), "ปีที่ตีพิมพ์ (พ.ศ.)", tone="d")
    else:
        k1 = kpi("คะแนน", "—", "ไม่มีข้อมูลในปีนี้", tone="a"); k2 = kpi("สถานะ", "—", "", tone="b")
        k3 = kpi("ปีข้อมูล", str(be(s["fy"])), "", tone="c"); k4 = kpi("ปีรายงาน", str(be(s["fy"] + 1)), "", tone="d")
    gname = " + ".join(("อาเซียน" if g == "ASEAN" else g) for g in groups)
    row = c31[c31["iso3"] == iso]
    if len(row):
        rr = row.iloc[0]
        rank_txt = f"{rr['name']} อันดับ {int(rr['rank_in_group'])} จาก {int(rr['n_in_group'])} ประเทศ ({gname}) ปีข้อมูล {be(s['fy'])}"
    else:
        rank_txt = f"ประเทศที่เลือกไม่อยู่ในกลุ่ม ({gname}) ไม่คิดอันดับ"
    d32 = Q.c32(s)
    c33 = Q.c33()
    items = []
    if s["fy"] != DEFAULTS[3]["fy"]:
        items.append(("fy", f"ปีข้อมูล {be(s['fy'])}"))
    if s["groups"] != DEFAULTS[3]["groups"]:
        items.append(("groups", "กลุ่ม: " + (", ".join(s["groups"]) or "ไม่เลือก")))
    if s["add_rus"]:
        items.append(("rus", "+ รัสเซีย"))
    if s.get("iso3"):
        items.append(("iso3", f"ประเทศ {s['iso3']}"))
    parts = [f"{gname} {be(s['fy'])}"]
    if s["level"] in ("country", "year"):
        parts.append(str(d32["name"].iloc[0]) if len(d32) else str(s["iso3"]))
    if s["level"] == "year":
        parts.append(f"ปีข้อมูล {be(s['fy'])}")

    find = [rank_txt]
    ra = Q.rank_all(s["fy"])
    if len(ra):
        find.append(f"ไทย อันดับ {int(ra.iloc[0]['rnk'])} จาก {int(ra.iloc[0]['n'])} ประเทศที่มีข้อมูลปีนั้น")
    if len(c31):
        find.append(f"มัธยฐานของกลุ่มคือ {c31['total_score'].median():.0f} คะแนน")
    limit = ["คะแนนเป็นการประเมินของผู้เชี่ยวชาญ ไม่ใช่การนับเหตุการณ์ และห้ามรวมหลายปีมาจัดอันดับ",
             "ประเทศที่ไม่มีข้อมูลในปีใดคือไม่มีข้อมูล ไม่ใช่ 0",
             "ข้อมูลไม่ได้บอกว่าเสรีภาพสัมพันธ์กับปริมาณข่าวปลอม",
             "จำนวนคำตัดสิน AFNC ไม่ใช่ปริมาณข่าวปลอมในสังคม และ EUvsDisinfo เก็บเฉพาะฝั่งสนับสนุนรัสเซีย"]
    return dict(controls=(s["fy"], s["groups"], ["1"] if s["add_rus"] else []), chips=chips(items, "t3chip"),
                crumb=breadcrumb(parts), k=[k1, k2, k3, k4], rank=rank_txt,
                g1=F.fig_c31(c31, s, theme), g2=F.fig_c32(d32, s, theme), g3=F.fig_c33(c33, theme, s["fy"]),
                g4=F.fig_c34(Q.c34(), theme, s["fy"]), g5=F.fig_c35(Q.c35(s["fy"]), theme),
                find=note_box("ข้อค้นพบ", find, "finding"), limit=note_box("ข้อจำกัดของข้อมูล", limit, "limit"))


def register(app, stores):
    graphs = ["t3-g1", "t3-g2", "t3-g3", "t3-g4", "t3-g5"]

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
        Output("t3-g3", "figure"), Output("t3-g4", "figure"), Output("t3-g5", "figure"),
        Output("t3-find", "children"), Output("t3-limit", "children"),
        *[Output(g, "clickData") for g in graphs],
        Input("store-tab3", "data"), Input("store-theme", "data"))
    def rend(s, theme):
        r = render(s, theme)
        return (*r["controls"], r["chips"], r["crumb"], *r["k"], r["rank"], r["g1"], r["g2"], r["g3"], r["g4"], r["g5"],
                r["find"], r["limit"], None, None, None, None, None)

    @app.callback(Output("t3-dl", "data"), Input("t3-dl-btn", "n_clicks"), State("store-tab3", "data"),
                  prevent_initial_call=True)
    def dl(n, s):
        if not n:
            raise PreventUpdate
        return filtered_download("3", s)
