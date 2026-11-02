"""breadcrumb.py — คอมโพเนนต์ breadcrumb และปุ่มย้อนระดับ"""
from dash import html

def render_breadcrumb(items, back_btn_id=None, show_back=False):
    """
    items: list of (label, is_active)
    """
    crumbs = []
    for i, (label, is_active) in enumerate(items):
        if i > 0:
            crumbs.append(html.Span(" › ", className="breadcrumb-separator"))
        if is_active:
            crumbs.append(html.Span(label, className="breadcrumb-item breadcrumb-active"))
        else:
            crumbs.append(html.Span(label, className="breadcrumb-item"))

    container = [html.Div(crumbs, className="breadcrumb-list")]
    if show_back and back_btn_id:
        container.append(
            html.Button("← ย้อนระดับ", id=back_btn_id, n_clicks=0, className="btn-back-level")
        )
    return html.Div(container, className="breadcrumb-bar")
