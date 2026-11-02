"""tab3.py — แท็บ 3: เสรีภาพอินเทอร์เน็ต (แยกส่วนตัวกรองคงที่และส่วนแสดงผลไดนามิก)"""
from dash import html, dcc
import app.queries as q
import app.figures as f
from app.state import to_be
from app.components.kpi_card import render_kpi_card
from app.components.breadcrumb import render_breadcrumb
from app.components.filter_bar import render_active_chips
from app.components.note_box import render_findings_and_limitations, render_why_and_definitions_section

def render_tab3_layout(con=None, initial_state=None):
    state = initial_state or {}
    fy = state.get('fy', 2024)

    question_banner = html.Div([
        html.Div("คำถามหลัก: ไทยมีคะแนนเสรีภาพอินเทอร์เน็ตอยู่ตรงไหนเมื่อเทียบกับประเทศอื่น และในช่วงเดียวกัน AFNC เผยแพร่ผลตรวจข่าวจำนวนเท่าไร",
                 className="question-text")
    ], className="question-banner")

    filter_panel = html.Div([
        html.Div([
            html.Div([
                html.Label("ปีข้อมูล (พ.ศ.) · ปีรายงาน = ปีข้อมูล + 1", className="filter-label"),
                dcc.Dropdown(
                    id='tab3-filter-fy',
                    options=[{'label': f"ปีข้อมูล {to_be(y)} (รายงานฉบับ {to_be(y)+1})", 'value': y}
                             for y in range(2024, 2010, -1)],
                    value=fy,
                    clearable=False
                )
            ], style={'flex': '1.5', 'minWidth': '240px'}),
            html.Div([
                html.Label("กลุ่มเปรียบเทียบ", className="filter-label"),
                dcc.Checklist(
                    id='tab3-filter-rus',
                    options=[{'label': ' เพิ่มรัสเซีย (RUS) เพื่อเปรียบเทียบ', 'value': 'add_rus'}],
                    value=[]
                )
            ], style={'flex': '1.5', 'minWidth': '220px', 'marginTop': '18px'}),
        ], className="filter-row"),
    ], className="filter-panel")

    dynamic_area = html.Div(id='tab3-dynamic-area')

    return html.Div([
        question_banner,
        filter_panel,
        dynamic_area,
        render_why_and_definitions_section()
    ])

def render_tab3_dynamic(con, state, is_dark=False):
    k3 = q.get_k3(con, state)
    df_c3_1 = q.get_c3_1(con, state)
    df_c3_2 = q.get_c3_2(con, state, level=state.get('level', 'group'))
    df_c3_3 = q.get_c3_3(con)
    df_c3_4 = q.get_c3_4(con)
    df_c3_5 = q.get_c3_5(con, fy=state.get('fy', 2024))

    fy = state.get('fy', 2024)
    iso3 = state.get('iso3', 'THA')
    add_rus = state.get('add_rus', False)
    level = state.get('level', 'group')

    chips = [
        {'label': f"ปีข้อมูล: {to_be(fy)} (รายงาน {to_be(fy)+1})", 'id': 'tab3-chip-fy'},
        {'label': "กลุ่ม: อาเซียน (8 ประเทศ)", 'id': 'tab3-chip-group'}
    ]
    if add_rus:
        chips.append({'label': "รวมรัสเซีย", 'id': 'tab3-chip-rus'})
    if level in ('country', 'year') and iso3:
        chips.append({'label': f"เจาะจงประเทศ: {iso3}", 'id': 'tab3-chip-iso'})

    chips_bar = render_active_chips(chips, clear_btn_id='tab3-btn-clear')

    bread_items = [("อาเซียน", level == 'group')]
    if level in ('country', 'year') and iso3:
        bread_items.append((f"ประเทศ {iso3}", level == 'country'))
    if level == 'year':
        bread_items.append((f"ปีข้อมูล {to_be(fy)} (3 องค์ประกอบ)", True))

    breadcrumb_bar = render_breadcrumb(bread_items, back_btn_id='tab3-btn-back', show_back=(level != 'group'))

    rank_in_group = "-"
    n_in_group = 8
    if not df_c3_1.empty:
        tha_row = df_c3_1[df_c3_1['iso3'] == 'THA']
        if not tha_row.empty:
            rank_in_group = tha_row['rank_in_group'].iloc[0]
            n_in_group = tha_row['n_in_group'].iloc[0]

    kpi_grid = html.Div([
        render_kpi_card("K3.1 คะแนนเสรีภาพของไทย", f"{k3['total_score']}", "คะแนน / 100",
                        f"อันดับ {rank_in_group} จาก {n_in_group} ประเทศในกลุ่ม", badge="Freedom House"),
        render_kpi_card("K3.2 สถานะเสรีภาพ", f"{k3['status_th']}", "",
                        "การประเมินโดยผู้เชี่ยวชาญ", badge="FOTN"),
        render_kpi_card("K3.3 ปีข้อมูลที่ประเมิน", f"พ.ศ. {to_be(k3['data_year'])}", "",
                        f"ครอบคลุม มิ.ย. {to_be(k3['data_year'])-1} – พ.ค. {to_be(k3['data_year'])}"),
        render_kpi_card("K3.4 ปีที่เผยแพร่รายงาน", f"พ.ศ. {to_be(k3['report_edition'])}", "",
                        "Freedom on the Net Edition"),
    ], className="kpi-grid")

    fig_c3_1 = f.make_c3_1_figure(df_c3_1, is_dark=is_dark)
    fig_c3_2 = f.make_c3_2_figure(df_c3_2, is_dark=is_dark, level=level)
    fig_c3_3 = f.make_c3_3_figure(df_c3_3, is_dark=is_dark)
    fig_c3_4 = f.make_c3_4_figure(df_c3_4, is_dark=is_dark)
    fig_c3_5 = f.make_c3_5_figure(df_c3_5, is_dark=is_dark)

    charts_row1 = html.Div([
        html.Div([
            html.Div("แตะแท่งประเทศเพื่อเจาะดูองค์ประกอบรายปี (C3.2) · สีส้มเข้มคือไทย", className="chart-disclaimer-pill"),
            dcc.Graph(id='tab3-graph-c3-1', figure=fig_c3_1, config={'responsive': True, 'displayModeBar': False})
        ], className="chart-card", style={'flex': '1'}),
        html.Div([
            html.Div("คะแนน 3 ส่วน: การเข้าถึง /25, การจำกัดเนื้อหา /35, การละเมิดสิทธิ /40", className="chart-disclaimer-pill"),
            dcc.Graph(id='tab3-graph-c3-2', figure=fig_c3_2, config={'responsive': True, 'displayModeBar': False})
        ], className="chart-card", style={'flex': '1.2'}),
    ], className="charts-grid-2")

    charts_row2 = html.Div([
        html.Div([
            html.Div("ตัวกรองประเทศไม่มีผลกับฝั่ง AFNC · ข้อมูลไทย 2562 มีเพียง 3 เดือนสุดท้าย", className="chart-disclaimer-pill"),
            dcc.Graph(id='tab3-graph-c3-3', figure=fig_c3_3, config={'responsive': True, 'displayModeBar': False})
        ], className="chart-card", style={'flex': '1.2'}),
        html.Div([
            html.Div("บริบทโลก: EUvsDisinfo การหักล้างรายปี (ไม่ผูกกับตัวกรองประเทศ)", className="chart-disclaimer-pill"),
            dcc.Graph(id='tab3-graph-c3-4', figure=fig_c3_4, config={'responsive': True, 'displayModeBar': False})
        ], className="chart-card", style={'flex': '1'}),
    ], className="charts-grid-2")

    map_section = html.Div([
        html.Div([
            dcc.Graph(id='tab3-graph-c3-5', figure=fig_c3_5, config={'responsive': True, 'displayModeBar': False})
        ], className="chart-card")
    ], style={'marginBottom': '20px'})

    findings = [
        f"1. ปีข้อมูลล่าสุด พ.ศ. 2567 (รายงานฉบับ 2568) ไทยได้คะแนนรวม 39 จาก 100 คะแนน จัดอยู่ในสถานะ 'ไม่เสรี'",
        f"2. ในกลุ่ม 8 ประเทศอาเซียนที่มีข้อมูล ไทยอยู่อันดับ 6 (ตามหลังฟิลิปปินส์ 61, มาเลเซีย 60, สิงคโปร์ 53, อินโดนีเซีย 48, กัมพูชา 42 และนำหน้าเวียดนาม 22, เมียนมา 9)",
        f"3. องค์ประกอบคะแนนของไทยที่ต่ำที่สุดเมื่อเทียบกับคะแนนเต็ม คือ 'การละเมิดสิทธิผู้ใช้' ได้ 8 จาก 40 คะแนน",
        f"4. ในช่วงปี พ.ศ. 2562–2567 คะแนนเสรีภาพของไทยค่อนข้างคงที่ (35–39 คะแนน) ในขณะที่จำนวนคำตัดสินของ AFNC เพิ่มขึ้นจาก 78 เรื่อง (ปี 2562 มี 3 เดือน) ขึ้นมาอยู่ที่ 2,400–2,600 เรื่องต่อปี"
    ]
    limitations = [
        "1. ห้ามสรุปความสัมพันธ์: ห้ามสรุปว่าประเทศที่มีเสรีภาพน้อยจะมีข่าวปลอมมากกว่าหรือน้อยกว่า หรือปริมาณข่าวส่งผลต่อคะแนนเสรีภาพ",
        "2. อันดับคิดในปีเดียวและบอกกลุ่มเสมอ เช่น 'อันดับ 6 จาก 8 ประเทศอาเซียน ปีข้อมูล 2567' ห้ามรวมคะแนนหลายปีมาจัดอันดับ",
        "3. ตัวกรองประเทศมีผลเฉพาะกับคะแนน FOTN เท่านั้น ไม่กระทบกับจำนวนคำตัดสินของ AFNC หรือ EUvsDisinfo",
        "4. คะแนน Freedom on the Net เป็นผลการประเมินเชิงคุณภาพโดยผู้เชี่ยวชาญ ไม่ใช่การตรวจนับคดีหรือเหตุการณ์จริง"
    ]
    findings_box = render_findings_and_limitations(
        html.Ul([html.Li(x) for x in findings]),
        html.Ul([html.Li(x) for x in limitations])
    )

    return html.Div([
        chips_bar,
        breadcrumb_bar,
        kpi_grid,
        charts_row1,
        charts_row2,
        map_section,
        findings_box
    ])
