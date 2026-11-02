"""evidence_table.py — คอมโพเนนต์ตารางหลักฐาน (T1 และ T2) พร้อมลิงก์เปิดแท็บใหม่"""
from dash import html
from app.state import format_date_be

def render_evidence_table_t1(df, max_rows=30):
    if df.empty:
        return html.Div("ไม่พบรายการหลักฐานตามเงื่อนไขที่เลือก", className="table-empty-box")

    rows = []
    for _, r in df.head(max_rows).iterrows():
        source = r.get('source', '')
        date_str = format_date_be(r.get('date', ''))
        title = r.get('title', '')
        category = r.get('category', '')
        reason = r.get('reason', '')
        snippet = r.get('evidence_snippet', '')
        url = r.get('url', '#')

        badge_class = "badge-afnc" if source == 'AFNC' else "badge-aiid"

        rows.append(html.Tr([
            html.Td(html.Span(source, className=f"source-badge {badge_class}")),
            html.Td(date_str, className="tabular-num text-nowrap"),
            html.Td(html.A(title, href=url, target="_blank", rel="noopener noreferrer", className="evidence-link")),
            html.Td(category),
            html.Td(html.Span(reason, className="reason-text")),
            html.Td(snippet, className="snippet-text"),
            html.Td(html.Span("ต้องตรวจสอบ", className="badge-warning")),
            html.Td(html.A("เปิดดู ↗", href=url, target="_blank", rel="noopener noreferrer", className="btn-link-sm"))
        ]))

    count_note = f"แสดง {min(len(df), max_rows):,} จากทั้งหมด {len(df):,} รายการ"

    return html.Div([
        html.Div(count_note, className="table-count-note"),
        html.Div([
            html.Table([
                html.Thead(html.Tr([
                    html.Th("แหล่งที่มา"),
                    html.Th("วันที่ (พ.ศ.)"),
                    html.Th("หัวข้อ / เหตุการณ์"),
                    html.Th("หมวด / ขอบเขต"),
                    html.Th("คำที่ตรวจพบ"),
                    html.Th("ข้อความหลักฐาน"),
                    html.Th("สถานะ"),
                    html.Th("ลิงก์")
                ])),
                html.Tbody(rows)
            ], className="evidence-table")
        ], className="table-responsive-box")
    ], className="evidence-section")

def render_evidence_table_t2(df, max_rows=30):
    if df.empty:
        return html.Div("ไม่พบรายการหลักฐานในประเด็นนี้", className="table-empty-box")

    rows = []
    for _, r in df.head(max_rows).iterrows():
        source = r.get('source', '')
        date_str = format_date_be(r.get('date', ''))
        headline = r.get('headline', '')
        matched_by = r.get('matched_by', '')
        matched_terms = r.get('matched_terms', '')
        url = r.get('url', '#')

        badge_class = "badge-afnc" if source == 'AFNC' else "badge-eu"

        rows.append(html.Tr([
            html.Td(html.Span(source, className=f"source-badge {badge_class}")),
            html.Td(date_str, className="tabular-num text-nowrap"),
            html.Td(html.A(headline, href=url, target="_blank", rel="noopener noreferrer", className="evidence-link")),
            html.Td(matched_by),
            html.Td(html.Span(matched_terms, className="reason-text")),
            html.Td(html.A("เปิดดู ↗", href=url, target="_blank", rel="noopener noreferrer", className="btn-link-sm"))
        ]))

    count_note = f"แสดง {min(len(df), max_rows):,} จากทั้งหมด {len(df):,} รายการ · หมายเหตุ: ไม่ใช่การจับคู่ข่าวต่อข่าว"

    return html.Div([
        html.Div(count_note, className="table-count-note"),
        html.Div([
            html.Table([
                html.Thead(html.Tr([
                    html.Th("แหล่งที่มา"),
                    html.Th("วันที่ (พ.ศ.)"),
                    html.Th("หัวข้อข่าว / หัวข้อการหักล้าง"),
                    html.Th("วิธีจับคู่"),
                    html.Th("คำที่ตรง"),
                    html.Th("ลิงก์")
                ])),
                html.Tbody(rows)
            ], className="evidence-table")
        ], className="table-responsive-box")
    ], className="evidence-section")
