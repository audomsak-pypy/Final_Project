"""tab2.py — แท็บ 2: ประเด็นข้อมูลบิดเบือนต่างประเทศกับไทย (EUvsDisinfo + AFNC + AIID)"""
from dash import html, dcc
import app.queries as q
import app.figures as f
from app.state import to_be
from app.components.kpi_card import render_kpi_card
from app.components.breadcrumb import render_breadcrumb
from app.components.filter_bar import render_active_chips
from app.components.evidence_table import render_evidence_table_t2
from app.components.note_box import render_findings_and_limitations, render_why_and_definitions_section

THEMES_OPTIONS = [
    {'label': 'โควิด-19', 'value': 'covid'},
    {'label': 'สงครามยูเครน', 'value': 'ukraine'},
    {'label': 'สงครามและความขัดแย้งอื่น', 'value': 'other_conflict'},
    {'label': 'สุขภาพ (จัดตามหมวด)', 'value': 'health'},
    {'label': 'การเงินและเศรษฐกิจ (จัดตามหมวด)', 'value': 'finance'},
    {'label': 'การเมือง การเลือกตั้ง และนโยบายรัฐ (จัดตามหมวด)', 'value': 'politics'},
    {'label': 'ทฤษฎีสมคบคิด', 'value': 'conspiracy'},
]

THEME_TH_DICT = {
    'covid': 'โควิด-19',
    'ukraine': 'สงครามยูเครน',
    'other_conflict': 'สงครามและความขัดแย้งอื่น',
    'health': 'สุขภาพ',
    'finance': 'การเงินและเศรษฐกิจ',
    'politics': 'การเมือง การเลือกตั้ง และนโยบายรัฐ',
    'conspiracy': 'ทฤษฎีสมคบคิด'
}

def render_tab2_content(con, state, is_dark=False):
    # Queries
    k2 = q.get_k2(con, state)
    df_c2_1 = q.get_c2_1(con, state)
    df_c2_2 = q.get_c2_2(con, state)
    theme = state.get('theme', 'covid')
    df_c2_3 = q.get_c2_3(con, state)
    df_c2_4 = q.get_c2_4(con, state)
    df_c2_5 = q.get_c2_5(con, state)
    df_t2 = q.get_t2(con, state)

    # Question Banner
    question_banner = html.Div([
        html.Div("คำถามหลัก: ประเด็นใดปรากฏร่วมกัน และประเด็นใดมีสัดส่วนต่างกัน ระหว่าง EUvsDisinfo กับข่าวเท็จของ AFNC",
                 className="question-text")
    ], className="question-banner")

    # Filter Controls
    y0 = state.get('y0', 2020)
    y1 = state.get('y1', 2022)
    year = state.get('year')

    filter_panel = html.Div([
        html.Div([
            html.Div([
                html.Label("ช่วงปี (พ.ศ.) · ค่าเริ่มต้น 2563–2565", className="filter-label"),
                dcc.RangeSlider(
                    id='tab2-filter-year-range',
                    min=2019, max=2026, step=1,
                    value=[y0, y1],
                    marks={y: f"{to_be(y)}" for y in range(2019, 2027)},
                    tooltip={"placement": "bottom", "always_visible": False}
                )
            ], style={'flex': '2', 'minWidth': '260px'}),
            html.Div([
                html.Label("ประเด็นที่สนใจ", className="filter-label"),
                dcc.Dropdown(
                    id='tab2-filter-theme',
                    options=THEMES_OPTIONS,
                    value=theme,
                    clearable=False
                )
            ], style={'flex': '1.5', 'minWidth': '220px'}),
        ], className="filter-row"),
        html.Div("หมายเหตุ: ข้อมูล EUvsDisinfo มีถึง 1 ส.ค. 2566 · ปี 2567+ ฝั่ง EU จะไม่มีข้อมูล · 1 เรื่องอยู่ได้หลายประเด็น ผลรวมอาจเกิน 100%",
                 style={'fontSize': '12px', 'color': 'var(--muted)', 'marginTop': '8px'})
    ], className="filter-panel")

    # Active Chips
    chips = []
    if y0 != 2020 or y1 != 2022:
        chips.append({'label': f"ช่วงปี: พ.ศ. {to_be(y0)}–{to_be(y1)}", 'id': 'tab2-chip-year-range'})
    if year:
        chips.append({'label': f"ปีเจาะจง: พ.ศ. {to_be(year)}", 'id': 'tab2-chip-year'})
    chips.append({'label': f"ประเด็น: {THEME_TH_DICT.get(theme, theme)}", 'id': 'tab2-chip-theme'})

    chips_bar = render_active_chips(chips, clear_btn_id='tab2-btn-clear')

    # Breadcrumbs
    bread_items = [("ช่วงปีทั้งหมดที่เลือก", not year)]
    if year:
        bread_items.append((f"พ.ศ. {to_be(year)}", True))

    breadcrumb_bar = render_breadcrumb(bread_items, back_btn_id='tab2-btn-back', show_back=bool(year))

    # KPI Cards
    kpi_grid = html.Div([
        render_kpi_card("K2.1 EUvsDisinfo การหักล้าง", f"{k2['eu_debunks']:,}", "เรื่อง",
                        f"ช่วง พ.ศ. {to_be(y0)}–{to_be(y1)}", badge="EU"),
        render_kpi_card("K2.2 AFNC ข่าวเท็จ (ปลอม+บิดเบือน)", f"{k2['afnc_false']:,}", "ข่าว",
                        f"ช่วง พ.ศ. {to_be(y0)}–{to_be(y1)}", badge="AFNC"),
        render_kpi_card("K2.3 AIID Misinformation (บริบทโลก)", f"{k2['aiid_misinfo']:,}", "เหตุการณ์",
                        f"ช่วง พ.ศ. {to_be(y0)}–{to_be(y1)}", badge="AIID"),
    ], className="kpi-grid", style={'gridTemplateColumns': 'repeat(3, 1fr)'})

    # Heatmaps C2.1 & C2.2
    fig_c2_1 = f.make_c2_1_figure(df_c2_1, is_dark=is_dark)
    fig_c2_2 = f.make_c2_2_figure(df_c2_2, is_dark=is_dark)

    heatmaps_row = html.Div([
        html.Div([
            html.Div("สเกลสีร่วมกัน 0–100% · แตะช่องเพื่อเลือกปีหรือประเด็น", className="chart-disclaimer-pill"),
            dcc.Graph(id='tab2-graph-c2-1', figure=fig_c2_1, config={'responsive': True, 'displayModeBar': False})
        ], className="chart-card", style={'flex': '1'}),
        html.Div([
            html.Div("แถวที่มี (จัดตามหมวด) ใช้วิธีจัดกลุ่มต่างจาก EU · ผลรวมอาจเกิน 100%", className="chart-disclaimer-pill"),
            dcc.Graph(id='tab2-graph-c2-2', figure=fig_c2_2, config={'responsive': True, 'displayModeBar': False})
        ], className="chart-card", style={'flex': '1'}),
    ], className="charts-grid-2")

    # Trend C2.3 & C2.4
    fig_c2_3 = f.make_c2_3_figure(df_c2_3, theme_th=THEME_TH_DICT.get(theme, theme), is_dark=is_dark)
    fig_c2_4 = f.make_c2_4_figure(df_c2_4, is_dark=is_dark)
    fig_c2_5 = f.make_c2_5_figure(df_c2_5, is_dark=is_dark)

    trends_row = html.Div([
        html.Div([
            dcc.Graph(id='tab2-graph-c2-3', figure=fig_c2_3, config={'responsive': True, 'displayModeBar': False})
        ], className="chart-card", style={'flex': '1.2'}),
        html.Div([
            dcc.Graph(id='tab2-graph-c2-4', figure=fig_c2_4, config={'responsive': True, 'displayModeBar': False})
        ], className="chart-card", style={'flex': '1'}),
    ], className="charts-grid-2")

    context_row = html.Div([
        html.Div([
            dcc.Graph(id='tab2-graph-c2-5', figure=fig_c2_5, config={'responsive': True, 'displayModeBar': False})
        ], className="chart-card")
    ], style={'marginBottom': '20px'})

    # Evidence Table (T2)
    table_section = html.Div([
        html.Div([
            html.H3(f"T2 ตารางรายการหลักฐานในประเด็น: {THEME_TH_DICT.get(theme, theme)}", className="section-title"),
            html.Button("📥 ดาวน์โหลดผลการกรอง (CSV)", id="tab2-btn-download-csv", className="btn-link-sm",
                        style={'float': 'right', 'cursor': 'pointer'})
        ], style={'display': 'flex', 'justifyContent': 'space-between', 'alignItems': 'center', 'marginBottom': '10px'}),
        dcc.Download(id="tab2-download-dataframe-csv"),
        render_evidence_table_t2(df_t2)
    ], className="evidence-section")

    # Dynamic Summary Text (Findings & Limitations)
    findings = [
        f"1. ในช่วงเริ่มต้น พ.ศ. 2563–2565 ประเด็นโควิด-19 ปรากฏร่วมกันทั้งสองแหล่ง "
        f"(EUvsDisinfo พบ 629 เรื่อง คิดเป็น 13.0% และ AFNC พบ 657 ข่าว คิดเป็น 18.5%)",
        f"2. ประเด็นสงครามยูเครนเป็นประเด็นหลักใน EUvsDisinfo (1,671 เรื่อง, 34.7%) "
        f"แต่แทบไม่ปรากฏในข่าวเท็จของ AFNC ในไทย (พบเพียง 1 ข่าว)",
        f"3. ข่าวเท็จในไทยเกือบครึ่งหนึ่งกระจุกตัวอยู่ในหมวด 'สุขภาพ' (1,739 ข่าว, 48.9%) "
        f"ในขณะที่ฝั่ง EU ประเด็นสุขภาพมีสัดส่วนเพียง 8.7%"
    ]
    limitations = [
        "1. ห้ามสรุปว่าประเด็นแพร่หรือข้ามมาจากต่างประเทศ: แดชบอร์ดนี้แสดงเฉพาะประเด็นที่ปรากฏร่วมกัน ไม่ได้วัดการแพร่กระจาย",
        "2. วิธีจัดกลุ่มต่างกัน: ในประเด็นสุขภาพ การเงิน และการเมือง ฝั่ง AFNC จัดตามหมวดทางการ ส่วน EU จัดตาม keyword",
        "3. ผลรวมสัดส่วนของแต่ละปีอาจเกิน 100% เนื่องจาก 1 ข่าวหรือ 1 การหักล้างสามารถเข้าได้หลายประเด็น",
        "4. ข้อมูล EUvsDisinfo มีถึงเพียง 1 ส.ค. 2566 ปีหลังจากนั้นจึงไม่มีข้อมูล ไม่ใช่มีค่าเป็น 0"
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
        heatmaps_row,
        trends_row,
        context_row,
        table_section,
        findings_box,
        why_and_def
    ])
