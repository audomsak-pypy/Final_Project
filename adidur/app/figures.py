"""กราฟ Plotly + template สว่าง/มืด จาก token เดียวกับ style.css"""
import math
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from .state import be, month_label, TH_MONTHS

TOKENS = {
    "light": dict(bg="#FFF8EC", surface="#FFFDF7", ink="#1C0F08", muted="#6B5244", line="#E8D6BF",
                  accent="#B8300E", accent2="#D9700C", glow="#F7C33C",
                  fake="#B42318", distorted="#9E5205", real="#2E6B5C", warn="#B42318"),
    "dark": dict(bg="#120A06", surface="#1E120C", ink="#FBEFD9", muted="#C9B09A", line="#3B2719",
                 accent="#F2643A", accent2="#F5A23A", glow="#FCD25A",
                 fake="#F0614A", distorted="#F2A040", real="#6FC2AA", warn="#F0614A"),
}
SCALE = ["#FFF4D6", "#FCD97A", "#F5A23A", "#DD5A1A", "#A81F0C", "#4A0A04"]
COLORSCALE = [[i / 5, c] for i, c in enumerate(SCALE)]
CAT_COLORS = ["#B8300E", "#D9700C", "#F7C33C", "#2E6B5C", "#6B5244", "#8E3B8E", "#3B6EA8", "#A81F0C",
              "#7A9E2E", "#C77DA5", "#4A0A04", "#999999"]
FONT = '"Sarabun","Leelawadee UI",Tahoma,sans-serif'


def tok(theme):
    return TOKENS["dark" if theme == "dark" else "light"]


def base_layout(theme, height=360, **kw):
    t = tok(theme)
    lay = dict(
        height=height, margin=dict(l=48, r=16, t=36, b=40), paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)", font=dict(family=FONT, color=t["ink"], size=13),
        clickmode="event+select", hovermode="closest", legend=dict(orientation="h", y=-0.2),
        xaxis=dict(gridcolor=t["line"], zerolinecolor=t["line"], linecolor=t["line"], color=t["muted"]),
        yaxis=dict(gridcolor=t["line"], zerolinecolor=t["line"], linecolor=t["line"], color=t["muted"]),
    )
    lay.update(kw)
    return lay


def empty_fig(theme, msg, height=240):
    t = tok(theme)
    fig = go.Figure()
    fig.update_layout(**base_layout(theme, height, xaxis=dict(visible=False), yaxis=dict(visible=False)),
                      annotations=[dict(text=msg, showarrow=False, font=dict(size=15, color=t["muted"]),
                                        xref="paper", yref="paper", x=0.5, y=0.5)])
    return fig


def _tlabel(v, level):
    return month_label(v) if level == "month" else str(be(v))


def _axis(values, level):
    return [_tlabel(v, level) for v in values]


def time_axis_values(s):
    if s["level"] == "year":
        return list(range(s["y0"], s["y1"] + 1))
    return [f"{s['year']}-{m:02d}" for m in range(1, 13)]


def fig_c11_c12(s, df_aiid, df_afnc, theme):
    """เส้นบน Deepfake (AIID) / เส้นล่างข่าว AI (AFNC) แกน x ร่วม"""
    t = tok(theme)
    xs = time_axis_values(s)
    lvl = "year" if s["level"] == "year" else "month"
    labels = _axis(xs, lvl)
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.12,
                        subplot_titles=("Deepfake ที่บันทึกใน AIID (เหตุการณ์)",
                                        "ข่าวเท็จที่เกี่ยวกับ AI ใน AFNC (โพสต์)"))
    a = dict(zip(df_aiid["t"], df_aiid["n"]))
    fig.add_trace(go.Scatter(x=labels, y=[a.get(x, 0) for x in xs], mode="lines+markers", name="Deepfake (AIID)",
                             customdata=xs, line=dict(color=t["accent"], width=3),
                             hovertemplate="%{x}: %{y} เหตุการณ์<extra></extra>"), 1, 1)
    names = {"mention": "กล่าวถึง AI", "media_evidence": "มีคำบ่งชี้ว่าใช้ AI สร้างสื่อ"}
    cols = {"mention": t["accent2"], "media_evidence": t["fake"]}
    for lv in ("mention", "media_evidence"):
        sub = df_afnc[df_afnc["ai_level"] == lv]
        d = dict(zip(sub["t"], sub["n"]))
        ys = []
        for x in xs:
            yr = x if lvl == "year" else int(str(x)[:4])
            ys.append(0 if yr >= 2019 else None)
            if x in d:
                ys[-1] = d[x]
        fig.add_trace(go.Scatter(x=labels, y=ys, mode="lines+markers", name=names[lv], customdata=xs,
                                 line=dict(color=cols[lv], width=3, dash="solid" if lv == "mention" else "dash"),
                                 hovertemplate="%{x}: %{y} โพสต์<extra></extra>"), 2, 1)
    fig.update_layout(**base_layout(theme, 520))
    for r in (1, 2):
        fig.update_xaxes(gridcolor=t["line"], color=t["muted"], row=r, col=1, type="category")
        fig.update_yaxes(gridcolor=t["line"], color=t["muted"], rangemode="tozero", row=r, col=1)
    fig.update_annotations(font=dict(size=13, color=t["ink"]))
    return fig


def fig_c13(df, s, theme):
    t = tok(theme)
    if df.empty:
        return empty_fig(theme, "ไม่มีข่าว AI ในชุดที่เลือก")
    df = df.sort_values("n")
    colors = [t["accent"] if c == s.get("category") else t["accent2"] for c in df["category_th"]]
    fig = go.Figure(go.Bar(x=df["n"], y=df["category_th"], orientation="h", marker_color=colors,
                           customdata=df["category_th"], text=df["n"], textposition="outside",
                           hovertemplate="%{y}: %{x} โพสต์<extra></extra>"))
    fig.update_layout(**base_layout(theme, max(240, 60 + 44 * len(df)), margin=dict(l=150, r=30, t=16, b=36)))
    return fig


def fig_acsc_bar(s, week_df, month_df, theme):
    """C1.5 คดีต่อสัปดาห์ (หรือรายเดือน)"""
    t = tok(theme)
    if s["acsc_level"] == "month" and not s.get("acsc_month"):
        d = month_df
        x = [month_label(m) for m in d["month"]]
        fig = go.Figure(go.Bar(x=x, y=d["cases"], customdata=d["month"], marker_color=t["accent2"],
                               hovertemplate="%{x}: %{y:,.0f} คดี<extra></extra>"))
        fig.update_layout(**base_layout(theme, 300, xaxis=dict(type="category", color=t["muted"], gridcolor=t["line"]),
                                        yaxis=dict(title="คดี (รวมต่อเดือน)", gridcolor=t["line"], color=t["muted"])))
        return fig
    d = week_df
    x = [f"{int(r.week_start[8:]) } {TH_MONTHS[int(r.week_start[5:7]) - 1]}" for r in d.itertuples()]
    colors = [t["warn"] if f == "suspect" else t["accent2"] for f in d["flag_type"]]
    fig = go.Figure(go.Bar(x=x, y=d["cases"], customdata=d["week_start"], marker_color=colors,
                           hovertemplate="สัปดาห์ %{x}: %{y:,.0f} คดี<extra></extra>"))
    for r in d[d["acsc_reported"].fillna(0) == 0].itertuples():
        lbl = f"{int(r.week_start[8:])} {TH_MONTHS[int(r.week_start[5:7]) - 1]}"
        fig.add_annotation(x=lbl, y=0, text="ไม่มีแถลง", showarrow=False, yshift=14, textangle=-90,
                           font=dict(color=t["muted"], size=11))
    excl = d[(d["flag_type"] == "suspect") & d["cases"].isna()]
    for r in excl.itertuples():
        lbl = f"{int(r.week_start[8:])} {TH_MONTHS[int(r.week_start[5:7]) - 1]}"
        fig.add_annotation(x=lbl, y=0, text="ไม่รวม (น่าสงสัย)", showarrow=False, yshift=40, textangle=-90,
                           font=dict(color=t["warn"], size=11))
    fig.update_layout(**base_layout(theme, 300, xaxis=dict(type="category", tickangle=-60, color=t["muted"],
                                                          gridcolor=t["line"]),
                                    yaxis=dict(title="คดี", gridcolor=t["line"], color=t["muted"])))
    return fig


def fig_acsc_loss(s, week_df, month_df, theme):
    """C1.6 ความเสียหาย: จุดกลวง = ปัดเลข, สีเตือน = น่าสงสัย"""
    t = tok(theme)
    if s["acsc_level"] == "month" and not s.get("acsc_month"):
        d = month_df
        x = [month_label(m) for m in d["month"]]
        sym = ["circle-open" if r else "circle" for r in d["any_rounded"]]
        fig = go.Figure(go.Scatter(x=x, y=d["loss_baht"], mode="lines+markers", customdata=d["month"],
                                   marker=dict(size=10, symbol=sym, line=dict(width=2, color=t["accent"]),
                                               color=t["accent"]), line=dict(color=t["accent"]),
                                   hovertemplate="%{x}: %{y:,.0f} บาท<extra></extra>"))
        fig.update_layout(**base_layout(theme, 280, xaxis=dict(type="category", color=t["muted"], gridcolor=t["line"]),
                                        yaxis=dict(title="บาท (รวมต่อเดือน)", gridcolor=t["line"], color=t["muted"])))
        return fig
    d = week_df
    x = [f"{int(r.week_start[8:])} {TH_MONTHS[int(r.week_start[5:7]) - 1]}" for r in d.itertuples()]
    sym = ["circle-open" if p == "rounded" else "circle" for p in d["loss_precision"]]
    col = [t["warn"] if f == "suspect" else t["accent"] for f in d["flag_type"]]
    fig = go.Figure(go.Scatter(x=x, y=d["loss_baht"], mode="lines+markers", customdata=d["week_start"],
                               connectgaps=False, line=dict(color=t["accent"]),
                               marker=dict(size=10, symbol=sym, color=col, line=dict(width=2, color=col)),
                               hovertemplate="สัปดาห์ %{x}: %{y:,.0f} บาท<extra></extra>"))
    fig.update_layout(**base_layout(theme, 280, xaxis=dict(type="category", tickangle=-60, color=t["muted"],
                                                          gridcolor=t["line"]),
                                    yaxis=dict(title="บาท", gridcolor=t["line"], color=t["muted"])))
    return fig


def _text_color(frac):
    return "#FFFFFF" if frac >= 0.45 else "#1C0F08"


def fig_heatmap(df, years, themes_df, theme, title, no_data_years=(), denominators=None, highlight=None,
                category_themes=()):
    """Heatmap ปี × ประเด็น สเกลเดียวกัน 0–100%; ปีไม่มีข้อมูล = ช่องเทา + ข้อความ 'ไม่มีข้อมูล'"""
    t = tok(theme)
    ids = themes_df["theme_id"].tolist()
    names = []
    for i, n in zip(ids, themes_df["theme_th"]):
        names.append(n + (" (จัดตามหมวด)" if i in category_themes else ""))
    z, text = [], []
    lookup = {(r.year, r.theme_id): (r.pct, r.n) for r in df.itertuples()}
    for tid in ids:
        row, trow = [], []
        for y in years:
            if y in no_data_years:
                row.append(None); trow.append("ไม่มีข้อมูล")
            else:
                pct, n = lookup.get((y, tid), (0.0, 0))
                row.append(pct); trow.append(f"{pct:.1f}%")
        z.append(row); text.append(trow)
    xl = [str(be(y)) for y in years]
    fig = go.Figure(go.Heatmap(z=z, x=xl, y=names, zmin=0, zmax=100, colorscale=COLORSCALE, xgap=2, ygap=2,
                               colorbar=dict(title="% ของปี", ticksuffix="%", len=0.9, thickness=12),
                               hoverongaps=False,
                               customdata=[[[tid, y] for y in years] for tid in ids],
                               hovertemplate="%{y} · ปี %{x}<br>%{z:.1f}%<extra></extra>"))
    for i, tid in enumerate(ids):
        for j, y in enumerate(years):
            v = z[i][j]
            color = t["muted"] if v is None else _text_color(v / 100 if v else 0)
            if v is not None and v < 40:
                color = "#1C0F08"
            fig.add_annotation(x=j, y=i, text=text[i][j], showarrow=False,
                               font=dict(size=12, color=color))
    if highlight in ids:
        i = ids.index(highlight)
        fig.add_shape(type="rect", x0=-0.5, x1=len(years) - 0.5, y0=i - 0.5, y1=i + 0.5, line=dict(color=t["accent"], width=3))
    fig.update_layout(**base_layout(theme, 70 + 52 * len(ids), margin=dict(l=210, r=10, t=30, b=40), title=dict(
        text=title, font=dict(size=14), x=0),
        xaxis=dict(type="category", side="bottom", color=t["muted"]),
        yaxis=dict(autorange="reversed", color=t["ink"])))
    return fig


def fig_c23(eu_df, af_df, years, theme_id, theme_name, theme, no_eu, no_af, by_category):
    t = tok(theme)
    xl = [str(be(y)) for y in years]
    eu = {r.year: r.pct for r in eu_df[eu_df["theme_id"] == theme_id].itertuples()}
    af = {r.year: r.pct for r in af_df[af_df["theme_id"] == theme_id].itertuples()}
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=xl, y=[None if y in no_eu else eu.get(y, 0.0) for y in years], mode="lines+markers",
                             name="EUvsDisinfo (การหักล้าง)", customdata=years, line=dict(color=t["accent"], width=3),
                             hovertemplate="EU ปี %{x}: %{y:.1f}%<extra></extra>"))
    fig.add_trace(go.Scatter(x=xl, y=[None if y in no_af else af.get(y, 0.0) for y in years], mode="lines+markers",
                             name="AFNC (ข่าวเท็จ)" + (" · จัดตามหมวด" if by_category else ""), customdata=years,
                             line=dict(color=t["accent2"], width=3, dash="dash"),
                             hovertemplate="AFNC ปี %{x}: %{y:.1f}%<extra></extra>"))
    fig.update_layout(**base_layout(theme, 320, xaxis=dict(type="category", color=t["muted"], gridcolor=t["line"]),
                                    yaxis=dict(title="% ของเรื่องทั้งหมดในปีนั้น", range=[0, 100], ticksuffix="%",
                                               gridcolor=t["line"], color=t["muted"]),
                                    title=dict(text=theme_name, font=dict(size=14), x=0)))
    return fig


def fig_c24(df, s, theme):
    t = tok(theme)
    if df.empty:
        return empty_fig(theme, "ไม่มีข่าวเท็จในช่วงที่เลือก")
    cats = sorted(df["category_th"].unique())
    lvl = "year" if s["level"] == "year" else "month"
    xs = time_axis_values(s)
    fig = go.Figure()
    for i, c in enumerate(cats):
        sub = dict(zip(df[df["category_th"] == c]["t"], df[df["category_th"] == c]["n"]))
        fig.add_trace(go.Bar(x=_axis(xs, lvl), y=[sub.get(x, 0) for x in xs], name=c, customdata=[[x, c] for x in xs],
                             marker_color=CAT_COLORS[i % len(CAT_COLORS)],
                             hovertemplate=c + " · %{x}: %{y} ข่าว<extra></extra>"))
    fig.update_layout(**base_layout(theme, 380, barmode="stack",
                                    xaxis=dict(type="category", color=t["muted"], gridcolor=t["line"]),
                                    yaxis=dict(title="ข่าวเท็จ (โพสต์)", gridcolor=t["line"], color=t["muted"]),
                                    legend=dict(orientation="h", y=-0.25, font=dict(size=11))))
    return fig


def fig_c25(df, years, theme):
    t = tok(theme)
    d = dict(zip(df["year"], df["n"]))
    fig = go.Figure(go.Scatter(x=[str(be(y)) for y in years], y=[d.get(y, 0) for y in years], mode="lines+markers",
                               customdata=years, line=dict(color=t["accent"], width=3),
                               hovertemplate="ปี %{x}: %{y} เหตุการณ์<extra></extra>"))
    fig.update_layout(**base_layout(theme, 260, xaxis=dict(type="category", color=t["muted"], gridcolor=t["line"]),
                                    yaxis=dict(title="เหตุการณ์ (AIID)", rangemode="tozero", gridcolor=t["line"],
                                               color=t["muted"])))
    return fig


# ---------- แท็บ 3 ----------
def fig_c31(df, s, theme):
    t = tok(theme)
    if df.empty:
        return empty_fig(theme, "ไม่มีข้อมูลประเทศในปีที่เลือก")
    d = df.sort_values("total_score")
    colors = [t["accent"] if i == "THA" else t["muted"] for i in d["iso3"]]
    med = float(df["total_score"].median())
    fig = go.Figure(go.Bar(x=d["total_score"], y=d["name"], orientation="h", marker_color=colors, customdata=d["iso3"],
                           text=d["total_score"], textposition="outside",
                           hovertemplate="%{y}: %{x} คะแนน<extra></extra>"))
    fig.add_vline(x=med, line_dash="dot", line_color=t["accent2"], annotation_text=f"มัธยฐานกลุ่ม {med:.1f}",
                  annotation_font_color=t["muted"])
    fig.update_layout(**base_layout(theme, max(260, 70 + 40 * len(d)), margin=dict(l=110, r=40, t=24, b=40),
                                    xaxis=dict(range=[0, 105], title="คะแนนรวม (0–100 สูง = เสรีมาก)", gridcolor=t["line"],
                                               color=t["muted"])))
    return fig


def fig_c32(df, s, theme):
    t = tok(theme)
    if df.empty:
        return empty_fig(theme, "ไม่มีข้อมูล")
    if s["level"] == "group":
        xs = df["name"].tolist(); cd = df["iso3"].tolist()
    else:
        xs = [f"{be(y)} (รายงาน {be(r)})" for y, r in zip(df["data_year"], df["report_edition"])]
        cd = df["data_year"].tolist()
    fig = go.Figure()
    for col, name, mx, c in (("obstacles_to_access", "การเข้าถึง (เต็ม 25)", 25, t["accent2"]),
                             ("limits_on_content", "การจำกัดเนื้อหา (เต็ม 35)", 35, t["accent"]),
                             ("violations_of_user_rights", "การละเมิดสิทธิผู้ใช้ (เต็ม 40)", 40, "#4A0A04" if theme != "dark" else "#FCD25A")):
        fig.add_trace(go.Bar(x=xs, y=df[col], name=name, customdata=cd, marker_color=c,
                             hovertemplate=name + ": %{y}<extra></extra>"))
    fig.update_layout(**base_layout(theme, 380, barmode="stack",
                                    xaxis=dict(type="category", color=t["muted"], gridcolor=t["line"]),
                                    yaxis=dict(title="คะแนนรวม (3 องค์ประกอบ)", gridcolor=t["line"], color=t["muted"])))
    return fig


def fig_c33(df, theme):
    t = tok(theme)
    xl = [f"{be(y)}" for y in df["data_year"]]
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.14,
                        subplot_titles=("คะแนนเสรีภาพอินเทอร์เน็ตของไทย (0–100)", "คำตัดสินที่ AFNC เผยแพร่ (โพสต์)"))
    fig.add_trace(go.Scatter(x=xl, y=df["total_score"], mode="lines+markers", name="คะแนนไทย", customdata=df["data_year"],
                             line=dict(color=t["accent"], width=3),
                             hovertemplate="ปีข้อมูล %{x}: %{y} คะแนน<extra></extra>"), 1, 1)
    fig.add_trace(go.Scatter(x=xl, y=df["afnc_verdicts"], mode="lines+markers", name="คำตัดสิน AFNC",
                             customdata=df["data_year"], line=dict(color=t["accent2"], width=3, dash="dash"),
                             hovertemplate="ปี %{x}: %{y:,} คำตัดสิน<extra></extra>"), 2, 1)
    fig.update_layout(**base_layout(theme, 430))
    fig.update_xaxes(type="category", gridcolor=t["line"], color=t["muted"])
    fig.update_yaxes(gridcolor=t["line"], color=t["muted"])
    fig.update_yaxes(range=[0, 100], row=1, col=1)
    fig.update_annotations(font=dict(size=13, color=t["ink"]))
    return fig


def fig_c34(df, theme):
    t = tok(theme)
    fig = go.Figure(go.Bar(x=[str(be(y)) for y in df["year"]], y=df["debunks"], marker_color=t["accent2"],
                           hovertemplate="ปี %{x}: %{y:,} การหักล้าง<extra></extra>"))
    fig.update_layout(**base_layout(theme, 260, clickmode="none",
                                    xaxis=dict(type="category", color=t["muted"], gridcolor=t["line"]),
                                    yaxis=dict(title="การหักล้าง", gridcolor=t["line"], color=t["muted"])))
    return fig


def fig_c35(df, theme):
    t = tok(theme)
    if df.empty:
        return empty_fig(theme, "ไม่มีข้อมูล")
    scale = [[0, t["real"]], [0.33, t["real"]], [0.34, t["distorted"]], [0.66, t["distorted"]], [0.67, t["fake"]],
             [1, t["fake"]]]
    fig = go.Figure(go.Choropleth(locations=df["iso3"], z=df["status_code"], locationmode="ISO-3", text=df["name"],
                                  customdata=df["iso3"], colorscale=scale, zmin=1, zmax=3, showscale=False,
                                  marker_line_color=t["line"],
                                  hovertemplate="%{text}<br>สถานะ: " + df["status_th"] + "<extra></extra>"))
    fig.update_layout(**base_layout(theme, 340, margin=dict(l=0, r=0, t=0, b=0)),
                      geo=dict(bgcolor="rgba(0,0,0,0)", showframe=False, showcountries=True, countrycolor=t["line"],
                               landcolor=t["surface"], projection_type="natural earth"))
    return fig
