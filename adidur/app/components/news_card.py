"""news_card.py — คอมโพเนนต์การ์ดข่าวเด่น (1 ใหญ่ซ้าย + 2,3 เล็กขวาบน + ต่ำสุดขวาล่าง)"""
from dash import html
from app.state import format_date_be

def render_single_news_card(item, rank_label, is_large=False):
    if not item:
        return html.Div([
            html.Div(rank_label, className="news-rank-tag"),
            html.Div("ไม่มีข้อมูลข่าวในชุดนี้", className="news-empty-text")
        ], className=f"news-card {'news-card-large' if is_large else 'news-card-small'}")

    date_str = format_date_be(item.get('date'))
    view_count = item.get('view_count', 0)
    level_label = "มีคำบ่งชี้ว่าใช้ AI สร้างสื่อ · ต้องตรวจสอบ" if item.get('ai_level') == 'media_evidence' else "กล่าวถึง AI"
    level_class = "badge-fake" if item.get('ai_level') == 'media_evidence' else "badge-mention"

    return html.A([
        html.Div([
            html.Span(rank_label, className="news-rank-tag"),
            html.Span(f"เข้าชม: {view_count:,} ครั้ง", className="news-view-tag")
        ], className="news-card-header"),
        html.Div(item.get('title', '-'), className="news-card-title"),
        html.Div([
            html.Span(date_str, className="news-date"),
            html.Span(" · "),
            html.Span(item.get('category_th', '-'), className="news-category"),
        ], className="news-card-meta"),
        html.Div([
            html.Span(level_label, className=f"news-level-badge {level_class}")
        ], className="news-card-badges"),
        html.Div("เปิดข่าวต้นทาง ↗", className="news-card-link-text")
    ], href=item.get('url', '#'), target="_blank", rel="noopener noreferrer",
       className=f"news-card {'news-card-large' if is_large else 'news-card-small'}")

def render_featured_news_grid(cards_data):
    """
    cards_data: {'top1': dict, 'top2': dict, 'top3': dict, 'lowest': dict, 'total_items': int}
    """
    total = cards_data.get('total_items', 0)
    top1 = cards_data.get('top1')
    top2 = cards_data.get('top2')
    top3 = cards_data.get('top3')
    lowest = cards_data.get('lowest')

    if total == 0:
        return html.Div([
            html.Div("ข่าวเด่นจาก AFNC (ยอดเข้าชม ณ วันที่เก็บข้อมูล 1 พ.ย. 2569)", className="section-title"),
            html.Div("ไม่มีข่าวที่ตรงกับเงื่อนไขตัวกรองปัจจุบัน", className="news-no-items")
        ], className="featured-news-container")

    # Left column: Top 1 (Large)
    col_left = html.Div([
        render_single_news_card(top1, "อันดับ 1 ยอดเข้าชมสูงสุด", is_large=True)
    ], className="featured-news-col-left")

    # Right column: Top 2, Top 3, and Lowest
    right_children = []
    if total >= 2:
        right_children.append(render_single_news_card(top2, "อันดับ 2", is_large=False))
    if total >= 3:
        right_children.append(render_single_news_card(top3, "อันดับ 3", is_large=False))
    if total >= 4 and lowest:
        right_children.append(render_single_news_card(lowest, "ยอดเข้าชมต่ำสุดในชุดนี้", is_large=False))
    elif total < 4:
        right_children.append(html.Div(f"ชุดนี้มีข่าวทั้งหมด {total} รายการ (ไม่แสดงรายการซ้ำ)", className="news-sub-info"))

    col_right = html.Div(right_children, className="featured-news-col-right")

    return html.Div([
        html.Div([
            html.Span("ข่าวเด่นจาก AFNC ", className="section-title"),
            html.Span("(ยอดเข้าชม ณ วันที่เก็บข้อมูล: 1 พ.ย. 2569)", className="section-subtitle")
        ], className="featured-news-header-box"),
        html.Div([col_left, col_right], className="featured-news-grid")
    ], className="featured-news-container")
