"""kpi_card.py — คอมโพเนนต์การ์ด KPI"""
from dash import html

def render_kpi_card(title, value_text, unit_text, sub_text=None, badge=None):
    children = [
        html.Div([
            html.Span(title, className="kpi-title"),
            html.Span(badge, className="kpi-badge") if badge else None
        ], className="kpi-header"),
        html.Div([
            html.Span(value_text, className="kpi-value"),
            html.Span(f" {unit_text}", className="kpi-unit")
        ], className="kpi-body"),
    ]
    if sub_text:
        children.append(html.Div(sub_text, className="kpi-sub"))
    return html.Div(children, className="kpi-card")
