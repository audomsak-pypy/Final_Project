"""องค์ประกอบ UI ที่ใช้ร่วมกัน: kpi card, news card, chips, breadcrumb, evidence table, note box"""
from dash import html, dcc, dash_table

from ..state import date_th


def fmt(n, d=0):
    if n is None:
        return "คำนวณไม่ได้"
    return f"{n:,.{d}f}"


def kpi(label, value, unit, source=None, extra=None, cid=None, tone="a"):
    return html.Div([
        html.Div(label, className="kpi-label"),
        html.Div(value, className="kpi-value"),
        html.Div(unit, className="kpi-unit"),
        html.Div(source, className="kpi-source") if source else None,
        html.Div(extra, className="kpi-extra") if extra else None,
    ], className=f"kpi tone-{tone}", **({"id": cid} if cid else {}))


def notice(text):
    """ป้าย 'ตัวกรองนี้ไม่มีผลกับกราฟนี้'"""
    return html.Div(text, className="no-effect")


def note_box(title, items, kind="finding"):
    """ข้อค้นพบแสดงตรง ๆ; ข้อจำกัดพับเก็บไว้ให้กดอ่าน เพื่อลดข้อความบนหน้า"""
    if kind == "limit":
        return html.Details([html.Summary(title), html.Ul([html.Li(i) for i in items])], className="note-box limit")
    return html.Div([html.H4(title), html.Ul([html.Li(i) for i in items])], className=f"note-box {kind}")


def panel(title, *children, tag=None, cls=""):
    head = [html.H3(title)] + ([html.Span(tag, className="tag")] if tag else [])
    return html.Div([html.Div(head, className="panel-head"), *children], className=f"panel {cls}".strip())


def chips(items, chip_type, clear_id=None):
    """items: [(key, label)] ; กดชิปเพื่อลบทีละตัว (ปุ่มล้างอยู่ใน chipbar แบบ static)"""
    kids = [html.Button(f"{label}  ×", id={"t": chip_type, "k": key}, n_clicks=0, className="chip") for key, label in items]
    return kids or [html.Span("ยังไม่ได้ใช้ตัวกรอง", className="muted")]


def chipbar(prefix):
    return html.Div([html.Div(id=f"{prefix}-chips", className="chips"),
                     html.Button("ล้างตัวกรอง", id=f"{prefix}-clear", n_clicks=0, className="btn-link")], className="chipbar")


def breadcrumb(parts, back_id=None):
    return html.Span(" › ".join(parts), className="crumb")


def crumbbar(crumb_id, back_id):
    return html.Div([html.Div(id=crumb_id), html.Button("ย้อนระดับ", id=back_id, n_clicks=0, className="btn-small")],
                    className="crumbs")


def graph(gid, height=None, config=None):
    return dcc.Graph(id=gid, config={"displaylogo": False, "responsive": True, **(config or {})},
                     style={"height": f"{height}px"} if height else {}, className="graph")


def link_md(url, text="เปิดต้นฉบับ"):
    return f"[{text}]({url})" if url and str(url) != "nan" else ""


def evidence_table(tid, df, columns, tooltip=None):
    """columns: [(id, ชื่อ, presentation)]"""
    cols = [{"name": n, "id": i, **({"presentation": "markdown"} if p == "md" else {})} for i, n, p in columns]
    recs = df.to_dict("records")
    tips = [{c["id"]: {"value": str(r.get(tooltip) or ""), "type": "text"} for c in cols if c["id"] == "title"}
            for r in recs] if tooltip else []
    return dash_table.DataTable(
        id=tid, columns=cols, data=recs, page_size=8, sort_action="native",
        tooltip_data=tips, tooltip_delay=0, tooltip_duration=None,
        markdown_options={"link_target": "_blank"},
        style_table={"overflowX": "auto"},
        style_cell={"fontFamily": "inherit", "textAlign": "left", "padding": "8px 10px", "maxWidth": "340px",
                    "whiteSpace": "normal", "height": "auto", "backgroundColor": "var(--surface)",
                    "color": "var(--ink)", "border": "1px solid var(--line)", "fontVariantNumeric": "tabular-nums"},
        style_header={"backgroundColor": "var(--bg)", "color": "var(--ink)", "fontWeight": "700",
                      "border": "1px solid var(--line)"},
        css=[{"selector": ".dash-table-container .dash-spreadsheet-container .dash-spreadsheet-inner a",
              "rule": "color: var(--accent) !important;"}],
    )


def news_card(rank_label, row, big=False, level_names=None):
    ln = level_names or {"mention": "กล่าวถึง AI", "media_evidence": "มีคำบ่งชี้ว่าใช้ AI สร้างสื่อ · ต้องตรวจสอบ"}
    return html.A([
        html.Div(rank_label, className="rank"),
        html.Div(row["title"], className="news-title"),
        html.Div(f"{date_th(row['date'])} · {row['category_th']}", className="muted small"),
        html.Span("ข่าวเท็จ", className="status fake"),
        html.Span(ln.get(row["ai_level"], ""), className="chip-static"),
        html.Div(f"ยอดเข้าชม {int(row['view_count']):,} ครั้ง", className="views"),
        html.Div("เปิดข่าวต้นทาง", className="open"),
    ], href=row["url"], target="_blank", rel="noopener", className="news-card" + (" big" if big else ""))
