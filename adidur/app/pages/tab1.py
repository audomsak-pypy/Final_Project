"""tab1.py — แท็บ 1: AI และภัยออนไลน์ในไทย (AIID + AFNC + ACSC)"""
from dash import html, dcc
import app.queries as q
import app.figures as f
from app.state import to_be, format_month_be
from app.components.kpi_card import render_kpi_card
from app.components.news_card import render_featured_news_grid
from app.components.breadcrumb import render_breadcrumb
from app.components.filter_bar import render_active_chips
from app.components.evidence_table import render_evidence_table_t1
from app.components.note_box import render_findings_and_limitations, render_why_and_definitions_section

def render_tab1_content(con, state, is_dark=False):
    # Queries
    k1_1 = q.get_k1_1(con, state)
    k1_2 = q.get_k1_2(con, state)
    k1_3_4 = q.get_k1_3_4(con, state)
    df_aiid = q.get_c1_1(con, state)
    df_afnc = q.get_c1_2(con, state)
    df_cat = q.get_c1_3(con, state)
    cards_data = q.get_c1_4(con, state)
    df_acsc = q.get_c1_5_6(con, state)
    df_t1 = q.get_t1(con, state)

    # Question Banner
    question_banner = html.Div([
        html.Div("คำถามหลัก: เหตุการณ์ Deepfake ที่บันทึกทั่วโลก และข่าวเท็จเกี่ยวกับ AI ในไทย มีแนวโน้มและสร้างความเสียหายอย่างไร",
                 className="question-text")
    ], className="question-banner")

    # Filter Controls
    y0 = state.get('y0', 2015)
    y1 = state.get('y1', 2026)
    year = state.get('year')
    month = state.get('month')
    cat = state.get('category')
    imp = state.get('imp')
    inc_suspect = state.get('inc_suspect', True)

    filter_panel = html.Div([
        html.Div([
            html.Div([
                html.Label("ช่วงปี (พ.ศ.)", className="filter-label"),
                dcc.RangeSlider(
                    id='tab1-filter-year-range',
                    min=2015, max=2026, step=1,
                    value=[y0, y1],
                    marks={y: f"{to_be(y)}" for y in range(2015, 2027, 2)},
                    tooltip={"placement": "bottom", "always_visible": False}
                )
            ], style={'flex': '2', 'minWidth': '260px'}),
            html.Div([
                html.Label("ระดับข่าว AI", className="filter-label"),
                dcc.Dropdown(
                    id='tab1-filter-levels',
                    options=[
                        {'label': 'มีคำบ่งชี้ว่าใช้ AI สร้างสื่อ (ต้องตรวจสอบ)', 'value': 'media_evidence'},
                        {'label': 'กล่าวถึง AI', 'value': 'mention'}
                    ],
                    value=state.get('levels') or ['mention', 'media_evidence'],
                    multi=True,
                    clearable=False
                )
            ], style={'flex': '1.5', 'minWidth': '220px'}),
            html.Div([
                html.Label("หมวดข่าว AFNC", className="filter-label"),
                dcc.Dropdown(
                    id='tab1-filter-category',
                    options=[
                        {'label': 'ทุกหมวด', 'value': 'ALL'},
                        {'label': 'นโยบายรัฐบาล / ข่าวสารราชการ', 'value': 'นโยบายรัฐบาล / ข่าวสารราชการ'},
                        {'label': 'ความสงบและความมั่นคง', 'value': 'ความสงบและความมั่นคง'},
                        {'label': 'ภัยพิบัติ', 'value': 'ภัยพิบัติ'},
                        {'label': 'ผลิตภัณฑ์สุขภาพ', 'value': 'ผลิตภัณฑ์สุขภาพ'},
                        {'label': 'อาชญากรรมออนไลน์', 'value': 'อาชญากรรมออนไลน์'}
                    ],
                    value=cat if cat else 'ALL',
                    clearable=False
                )
            ], style={'flex': '1.2', 'minWidth': '180px'}),
            html.Div([
                html.Label("แอบอ้างหน่วยงาน/บุคคล", className="filter-label"),
                dcc.Dropdown(
                    id='tab1-filter-imp',
                    options=[
                        {'label': 'ทั้งหมด', 'value': 'ALL'},
                        {'label': 'เฉพาะที่แอบอ้าง', 'value': 1},
                        {'label': 'ไม่แอบอ้าง', 'value': 0}
                    ],
                    value=imp if imp is not None else 'ALL',
                    clearable=False
                )
            ], style={'flex': '1', 'minWidth': '140px'}),
            html.Div([
                html.Label("สัปดาห์น่าสงสัย ACSC", className="filter-label"),
                dcc.Checklist(
                    id='tab1-filter-suspect',
                    options=[{'label': ' รวมสัปดาห์ 16–22 ส.ค. 2569', 'value': 'inc'}],
                    value=['inc'] if inc_suspect else []
                )
            ], style={'flex': '1.5', 'minWidth': '200px'}),
        ], className="filter-row"),
    ], className="filter-panel")

    # Active Chips
    chips = []
    if year:
        chips.append({'label': f"ปี: {to_be(year)}", 'id': 'chip-remove-year'})
    if month:
        chips.append({'label': f"เดือน: {format_month_be(month)}", 'id': 'chip-remove-month'})
    if cat:
        chips.append({'label': f"หมวด: {cat}", 'id': 'chip-remove-category'})
    if imp == 1:
        chips.append({'label': "แอบอ้างหน่วยงาน/บุคคล", 'id': 'chip-remove-imp'})
    if not inc_suspect:
        chips.append({'label': "ไม่รวมสัปดาห์น่าสงสัย", 'id': 'chip-remove-suspect'})

    chips_bar = render_active_chips(chips, clear_btn_id='tab1-btn-clear')

    # Breadcrumbs
    bread_items = [("ทั้งหมด", not year and not month)]
    if year:
        bread_items.append((f"พ.ศ. {to_be(year)}", not month))
    if month:
        bread_items.append((format_month_be(month), True))

    breadcrumb_bar = render_breadcrumb(bread_items, back_btn_id='tab1-btn-back', show_back=bool(year or month))

    # KPI Cards
    k1_sub = f"ช่วง พ.ศ. {to_be(y0)}–{to_be(y1)}"
    k2_sub = f"สื่อ AI: {k1_2['media_evidence']} · กล่าวถึง: {k1_2['mention']}"

    k3_val = f"{k1_3_4['cases']:,}" if k1_3_4['has_data'] else "ไม่มีข้อมูล"
    k3_sub = "ช่วง 9 พ.ย. 2568 – 24 ต.ค. 2569" if k1_3_4['has_data'] else "ไม่มีข้อมูล ACSC ในช่วงที่เลือก"

    k4_val = f"{k1_3_4['loss_baht']:,}" if k1_3_4['has_data'] else "ไม่มีข้อมูล"
    if k1_3_4['has_data']:
        lpc_text = f"{k1_3_4['loss_per_case']:,.2f} บาท/คดี"
        if inc_suspect:
            k4_sub = f"{lpc_text} (รวมสัปดาห์น่าสงสัย +{k1_3_4['diff_loss']:,} บ.)"
        else:
            k4_sub = f"{lpc_text} (ไม่รวมสัปดาห์น่าสงสัย)"
    else:
        k4_sub = "ไม่มีข้อมูล ACSC ในช่วงที่เลือก"

    kpi_grid = html.Div([
        render_kpi_card("K1.1 เหตุการณ์ Deepfake ทั่วโลก", f"{k1_1:,}", "เรื่อง", k1_sub, badge="AIID"),
        render_kpi_card("K1.2 ข่าวเท็จเกี่ยวกับ AI ในไทย", f"{k1_2['total']:,}", "โพสต์", k2_sub, badge="AFNC"),
        render_kpi_card("K1.3 จำนวนคดีแจ้งความออนไลน์", k3_val, "คดี" if k1_3_4['has_data'] else "", k3_sub, badge="ACSC"),
        render_kpi_card("K1.4 ความเสียหายรวม", k4_val, "บาท" if k1_3_4['has_data'] else "", k4_sub, badge="ACSC"),
    ], className="kpi-grid")

    # Featured News Cards (C1.4)
    news_grid = render_featured_news_grid(cards_data)

    # Charts Grid
    fig_c1_1_2 = f.make_c1_1_2_figure(df_aiid, df_afnc, is_dark=is_dark, state=state)
    fig_c1_3 = f.make_c1_3_figure(df_cat, is_dark=is_dark)
    fig_c1_5_6 = f.make_c1_5_6_figure(df_acsc, is_dark=is_dark, state=state)

    charts_row1 = html.Div([
        html.Div([
            dcc.Graph(id='tab1-graph-c1-1-2', figure=fig_c1_1_2, config={'responsive': True, 'displayModeBar': False})
        ], className="chart-card", style={'flex': '1.3'}),
        html.Div([
            html.Div("ตัวกรอง AI มีผลกับกราฟนี้", className="chart-disclaimer-pill"),
            dcc.Graph(id='tab1-graph-c1-3', figure=fig_c1_3, config={'responsive': True, 'displayModeBar': False})
        ], className="chart-card", style={'flex': '1'}),
    ], className="charts-grid-2")

    charts_row2 = html.Div([
        html.Div([
            html.Div("ตัวกรองข่าว AI (หมวด, ระดับ, แอบอ้าง) ไม่มีผลกับ ACSC · จุดกลวง = ปัดเศษล้านบาท · สีเตือน = น่าสงสัย",
                     className="chart-disclaimer-pill"),
            dcc.Graph(id='tab1-graph-c1-5-6', figure=fig_c1_5_6, config={'responsive': True, 'displayModeBar': False})
        ], className="chart-card")
    ], style={'marginBottom': '20px'})

    # Evidence Table (T1)
    table_section = html.Div([
        html.Div([
            html.H3("T1 ตารางหลักฐาน: ข่าว AFNC และเหตุการณ์ Deepfake ในช่วงที่เลือก", className="section-title"),
            html.Button("📥 ดาวน์โหลดผลการกรอง (CSV)", id="tab1-btn-download-csv", className="btn-link-sm",
                        style={'float': 'right', 'cursor': 'pointer'})
        ], style={'display': 'flex', 'justifyContent': 'space-between', 'alignItems': 'center', 'marginBottom': '10px'}),
        dcc.Download(id="tab1-download-dataframe-csv"),
        render_evidence_table_t1(df_t1)
    ], className="evidence-section")

    # Dynamic Summary Text (Findings & Limitations)
    diff_pct_aiid = "-35.1%"
    findings = [
        f"1. ในช่วงปี พ.ศ. {to_be(y0)}–{to_be(y1)} มีเหตุการณ์ Deepfake ทั่วโลกถูกบันทึกใน AIID รวม {k1_1:,} เรื่อง",
        f"2. ในไทย ศูนย์ต่อต้านข่าวปลอม (AFNC) ตัดสินข่าวเท็จที่เข้าเกณฑ์เกี่ยวกับ AI รวม {k1_2['total']:,} โพสต์ "
        f"(ระดับมีคำบ่งชี้ว่าใช้ AI สร้างสื่อ {k1_2['media_evidence']:,} โพสต์ และระดับกล่าวถึง AI {k1_2['mention']:,} โพสต์)",
        f"3. ข่าวเท็จ AI ส่วนใหญ่จัดอยู่ในหมวด 'นโยบายรัฐบาล/ข่าวสารราชการ' และ 'ความสงบและความมั่นคง'",
        f"4. สถิติคดีแจ้งความออนไลน์ (ACSC) ในช่วง 9 พ.ย. 2568 – 24 ต.ค. 2569 มีจำนวน {k1_3_4['cases']:,} คดี "
        f"ความเสียหายรวม {k1_3_4['loss_baht']:,} บาท เฉลี่ย {k1_3_4['loss_per_case']:,.2f} บาท/คดี"
    ]
    limitations = [
        "1. ห้ามสรุปความสัมพันธ์เชิงสาเหตุ: ตัวเลขคดี ACSC ไม่ได้เชื่อมโยงว่าเป็นคดีที่เกิดจาก AI หรือข่าวปลอม",
        "2. จำนวนข่าว AI ของ AFNC (56 โพสต์) เป็นค่าขั้นต่ำ เนื่องจากไฟล์ต้นฉบับตัดข้อความที่ 500 ตัวอักษร",
        "3. เหตุการณ์ Deepfake ปี 2569 ใน AIID ที่ดูเหมือนลดลง (126 เทียบกับ 194 ในช่วงเดียวกันของปี 2568) "
        "อาจเกิดจากความล่าช้าในการรวบรวมข้อมูลของฐานข้อมูล ห้ามสรุปว่าการใช้ Deepfake ทั่วโลกลดลง",
        "4. ความเสียหายของ ACSC ตั้งแต่ ส.ค. 2569 มีการปัดเศษเป็นหลักล้านบาท และสัปดาห์ 16–22 ส.ค. 2569 "
        "มีตัวเลขสูงผิดปกติถึง 79,311 คดี (สงสัยว่าเป็นยอดสะสม) จึงมีสวิตช์แยกสัปดาห์นี้ออก"
    ]
    findings_box = render_findings_and_limitations(
        html.Ul([html.Li(x) for x in findings]),
        html.Ul([html.Li(x) for x in limitations])
    )

    why_and_def = render_why_and_definitions_section()

    return html.Div([
        question_banner,
        filter_panel,
        chips_bar,
        breadcrumb_bar,
        kpi_grid,
        news_grid,
        charts_row1,
        charts_row2,
        table_section,
        findings_box,
        why_and_def
    ])
