"""filter_bar.py — คอมโพเนนต์แถบตัวกรอง ชิปตัวกรอง และปุ่มล้างตัวกรอง"""
from dash import html, dcc

def render_active_chips(chips, clear_btn_id=None):
    """
    chips: list of dict {'label': str, 'id': str or dict}
    """
    chip_elements = []
    for c in chips:
        chip_elements.append(
            html.Span([
                html.Span(c['label']),
                html.Button("✕", id=c['id'], n_clicks=0, className="chip-remove-btn") if 'id' in c else None
            ], className="active-chip")
        )

    if not chip_elements:
        chip_elements.append(html.Span("ไม่มีตัวกรองเพิ่มเติม (แสดงทั้งหมด)", className="chip-none-text"))

    bar_items = [html.Div(chip_elements, className="chips-wrapper")]
    if clear_btn_id:
        bar_items.append(
            html.Button("ล้างตัวกรอง", id=clear_btn_id, n_clicks=0, className="btn-clear-filters")
        )
    return html.Div(bar_items, className="chips-bar")
