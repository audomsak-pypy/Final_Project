"""app.py — แดชบอร์ด Adidur ปรับปรุงใหม่: กราฟแสดงผลทันที เชื่อมโยงสมบูรณ์ (ตัดแท็บ 4 ออก)"""
import os
import sys
import sqlite3
import pandas as pd
import dash
from dash import html, dcc, Input, Output, State, callback_context
from dash.exceptions import PreventUpdate

from app.state import (
    DEFAULT_TAB1_STATE, DEFAULT_TAB2_STATE, DEFAULT_TAB3_STATE,
    state_to_url, url_to_state, to_be
)
import app.queries as q
import app.pages.landing as landing_page
import app.pages.tab1 as tab1_page
import app.pages.tab2 as tab2_page
import app.pages.tab3 as tab3_page

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "data", "adidur.db")

con_init = q.get_connection(DB_PATH)

app = dash.Dash(
    __name__,
    suppress_callback_exceptions=True,
    title="Adidur — จริงหรือเฟค",
    meta_tags=[{"name": "viewport", "content": "width=device-width, initial-scale=1"}]
)

app.layout = html.Div([
    dcc.Location(id='url', refresh=False),
    dcc.Store(id='store-active-tab', data='1'),
    dcc.Store(id='store-theme', data='light'),
    dcc.Store(id='store-tab1', data=DEFAULT_TAB1_STATE),
    dcc.Store(id='store-tab2', data=DEFAULT_TAB2_STATE),
    dcc.Store(id='store-tab3', data=DEFAULT_TAB3_STATE),

    html.Div([
        # Header with Navigation Bar (ตัดแท็บ 4 ออกตามคำขอ)
        html.Header([
            html.Div([
                html.Div([
                    html.Span("Adidur", className="brand-logo"),
                    html.Span(" — จริงหรือเฟค", style={'fontSize': '18px', 'fontWeight': '600', 'color': 'var(--ink)'})
                ]),
                html.Div("AI ข่าวปลอม และภัยออนไลน์: มองโลก เปรียบเทียบไทย", className="brand-meta")
            ], className="brand-row"),
            html.Nav([
                html.Button("1. AI และภัยออนไลน์ในไทย", id="nav-btn-tab1", n_clicks=0, className="nav-tab-item nav-tab-active"),
                html.Button("2. ประเด็นต่างประเทศกับไทย", id="nav-btn-tab2", n_clicks=0, className="nav-tab-item"),
                html.Button("3. เสรีภาพอินเทอร์เน็ต", id="nav-btn-tab3", n_clicks=0, className="nav-tab-item"),
                html.Button("หน้าแนะนำโครงงาน", id="nav-btn-landing", n_clicks=0, className="nav-tab-item"),
            ], className="nav-tabs-bar", id="nav-bar")
        ], className="app-header", id="main-header"),

        # Views: Tab 1 default visible, others hidden via CSS
        html.Main([
            html.Div(id='view-tab1', children=tab1_page.render_tab1_layout(con_init), style={'display': 'block'}),
            html.Div(id='view-tab2', children=tab2_page.render_tab2_layout(con_init), style={'display': 'none'}),
            html.Div(id='view-tab3', children=tab3_page.render_tab3_layout(con_init), style={'display': 'none'}),
            html.Div(id='view-landing', children=landing_page.layout(), style={'display': 'none'}),
        ])
    ], className="app-container")
])

con_init.close()

# -------------------------------------------------------------------------
# Theme clientside callback
# -------------------------------------------------------------------------
app.clientside_callback(
    """
    function(href) {
        if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) {
            return 'dark';
        }
        return 'light';
    }
    """,
    Output('store-theme', 'data'),
    Input('url', 'href')
)

# -------------------------------------------------------------------------
# Tab Navigation Callback
# -------------------------------------------------------------------------
@app.callback(
    [Output('store-active-tab', 'data'),
     Output('url', 'search'),
     Output('view-tab1', 'style'),
     Output('view-tab2', 'style'),
     Output('view-tab3', 'style'),
     Output('view-landing', 'style'),
     Output('nav-btn-tab1', 'className'),
     Output('nav-btn-tab2', 'className'),
     Output('nav-btn-tab3', 'className'),
     Output('nav-btn-landing', 'className')],
    [Input('nav-btn-tab1', 'n_clicks'),
     Input('nav-btn-tab2', 'n_clicks'),
     Input('nav-btn-tab3', 'n_clicks'),
     Input('nav-btn-landing', 'n_clicks'),
     Input('url', 'search')],
    [State('store-active-tab', 'data')]
)
def switch_active_tab(n1, n2, n3, n0, search_query, current_tab):
    ctx = callback_context
    tab = current_tab or '1'
    search_out = dash.no_update

    if ctx.triggered:
        trig_id = ctx.triggered[0]['prop_id'].split('.')[0]
        if trig_id == 'nav-btn-tab1':
            tab = '1'
            search_out = '?tab=1'
        elif trig_id == 'nav-btn-tab2':
            tab = '2'
            search_out = '?tab=2'
        elif trig_id == 'nav-btn-tab3':
            tab = '3'
            search_out = '?tab=3'
        elif trig_id == 'nav-btn-landing':
            tab = 'landing'
            search_out = ''
        elif trig_id == 'url' and search_query:
            if 'tab=1' in search_query: tab = '1'
            elif 'tab=2' in search_query: tab = '2'
            elif 'tab=3' in search_query: tab = '3'
            elif search_query == '': tab = '1'

    s_none = {'display': 'none'}
    s_block = {'display': 'block'}

    st_1 = s_block if tab == '1' else s_none
    st_2 = s_block if tab == '2' else s_none
    st_3 = s_block if tab == '3' else s_none
    st_landing = s_block if tab == 'landing' else s_none

    c_base = "nav-tab-item"
    c_act = "nav-tab-item nav-tab-active"

    cl_1 = c_act if tab == '1' else c_base
    cl_2 = c_act if tab == '2' else c_base
    cl_3 = c_act if tab == '3' else c_base
    cl_0 = c_act if tab == 'landing' else c_base

    return tab, search_out, st_1, st_2, st_3, st_landing, cl_1, cl_2, cl_3, cl_0

# -------------------------------------------------------------------------
# TAB 1 Reactive Updates (Direct Figure & Component Outputs)
# -------------------------------------------------------------------------
@app.callback(
    [Output('store-tab1', 'data'),
     Output('tab1-chips-container', 'children'),
     Output('tab1-breadcrumb-container', 'children'),
     Output('tab1-kpis-container', 'children'),
     Output('tab1-news-container', 'children'),
     Output('tab1-graph-c1-1-2', 'figure'),
     Output('tab1-graph-c1-3', 'figure'),
     Output('tab1-graph-c1-5-6', 'figure'),
     Output('tab1-table-container', 'children'),
     Output('tab1-findings-container', 'children')],
    [Input('tab1-filter-year-range', 'value'),
     Input('tab1-filter-levels', 'value'),
     Input('tab1-filter-category', 'value'),
     Input('tab1-filter-imp', 'value'),
     Input('tab1-filter-suspect', 'value'),
     Input('tab1-btn-clear', 'n_clicks'),
     Input('tab1-btn-back', 'n_clicks'),
     Input('tab1-graph-c1-1-2', 'clickData'),
     Input('tab1-graph-c1-3', 'clickData'),
     Input('tab1-graph-c1-5-6', 'clickData'),
     Input('store-theme', 'data')],
    [State('store-tab1', 'data')]
)
def update_tab1(year_range, levels, category, imp, suspect, n_clear, n_back,
                click_c1_1_2, click_c1_3, click_c1_5_6, theme_data, current_state):
    state = dict(current_state or DEFAULT_TAB1_STATE)
    ctx = callback_context

    if ctx.triggered:
        trig_id = ctx.triggered[0]['prop_id'].split('.')[0]
        if trig_id == 'tab1-btn-clear':
            state = dict(DEFAULT_TAB1_STATE)
        elif trig_id == 'tab1-btn-back':
            if state.get('month'):
                state['month'] = None
                state['level'] = 'month'
            elif state.get('year'):
                state['year'] = None
                state['level'] = 'year'
        elif trig_id == 'tab1-filter-year-range' and year_range:
            state['y0'], state['y1'] = year_range[0], year_range[1]
        elif trig_id == 'tab1-filter-levels':
            state['levels'] = levels or ['mention', 'media_evidence']
        elif trig_id == 'tab1-filter-category':
            state['category'] = None if category == 'ALL' else category
        elif trig_id == 'tab1-filter-imp':
            state['imp'] = None if imp == 'ALL' else imp
        elif trig_id == 'tab1-filter-suspect':
            state['inc_suspect'] = bool('inc' in (suspect or []))
        elif trig_id == 'tab1-graph-c1-1-2' and click_c1_1_2:
            pt = click_c1_1_2['points'][0]
            cdata = pt.get('customdata')
            if cdata:
                cdata_str = str(cdata)
                if len(cdata_str) == 4 and cdata_str.isdigit():
                    state['year'] = int(cdata_str)
                    state['level'] = 'month'
                elif '-' in cdata_str and len(cdata_str) == 7:
                    state['month'] = cdata_str
                    state['level'] = 'items'
        elif trig_id == 'tab1-graph-c1-3' and click_c1_3:
            pt = click_c1_3['points'][0]
            cdata = pt.get('customdata') or pt.get('y')
            if cdata:
                state['category'] = cdata
        elif trig_id == 'tab1-graph-c1-5-6' and click_c1_5_6:
            pt = click_c1_5_6['points'][0]
            cdata = pt.get('customdata')
            if cdata and str(cdata).startswith('202'):
                state['month'] = str(cdata)[:7]
                state['level'] = 'items'

    con = q.get_connection(DB_PATH)
    is_dark = (theme_data == 'dark')
    b = tab1_page.get_tab1_bundle(con, state, is_dark=is_dark)
    con.close()

    return (
        state,
        b['chips'],
        b['breadcrumb'],
        b['kpis'],
        b['news'],
        b['fig_c1_1_2'],
        b['fig_c1_3'],
        b['fig_c1_5_6'],
        b['table'],
        b['findings']
    )

# -------------------------------------------------------------------------
# TAB 2 Reactive Updates
# -------------------------------------------------------------------------
@app.callback(
    [Output('store-tab2', 'data'),
     Output('tab2-chips-container', 'children'),
     Output('tab2-breadcrumb-container', 'children'),
     Output('tab2-kpis-container', 'children'),
     Output('tab2-graph-c2-1', 'figure'),
     Output('tab2-graph-c2-2', 'figure'),
     Output('tab2-graph-c2-3', 'figure'),
     Output('tab2-graph-c2-4', 'figure'),
     Output('tab2-graph-c2-5', 'figure'),
     Output('tab2-table-container', 'children'),
     Output('tab2-findings-container', 'children')],
    [Input('tab2-filter-year-range', 'value'),
     Input('tab2-filter-theme', 'value'),
     Input('tab2-btn-clear', 'n_clicks'),
     Input('tab2-btn-back', 'n_clicks'),
     Input('tab2-graph-c2-1', 'clickData'),
     Input('tab2-graph-c2-2', 'clickData'),
     Input('store-theme', 'data')],
    [State('store-tab2', 'data')]
)
def update_tab2(year_range, theme, n_clear, n_back, click_c2_1, click_c2_2, theme_data, current_state):
    state = dict(current_state or DEFAULT_TAB2_STATE)
    ctx = callback_context

    if ctx.triggered:
        trig_id = ctx.triggered[0]['prop_id'].split('.')[0]
        if trig_id == 'tab2-btn-clear':
            state = dict(DEFAULT_TAB2_STATE)
        elif trig_id == 'tab2-btn-back':
            state['year'] = None
            state['level'] = 'year'
        elif trig_id == 'tab2-filter-year-range' and year_range:
            state['y0'], state['y1'] = year_range[0], year_range[1]
        elif trig_id == 'tab2-filter-theme':
            state['theme'] = theme
        elif trig_id in ('tab2-graph-c2-1', 'tab2-graph-c2-2'):
            click_data = click_c2_1 if trig_id == 'tab2-graph-c2-1' else click_c2_2
            if click_data:
                x_val = click_data['points'][0].get('x')
                if x_val and 'พ.ศ.' in str(x_val):
                    be_yr = int(str(x_val).replace('พ.ศ.', '').strip())
                    state['year'] = be_yr - 543
                    state['level'] = 'year'

    con = q.get_connection(DB_PATH)
    is_dark = (theme_data == 'dark')
    b = tab2_page.get_tab2_bundle(con, state, is_dark=is_dark)
    con.close()

    return (
        state,
        b['chips'],
        b['breadcrumb'],
        b['kpis'],
        b['fig_c2_1'],
        b['fig_c2_2'],
        b['fig_c2_3'],
        b['fig_c2_4'],
        b['fig_c2_5'],
        b['table'],
        b['findings']
    )

# -------------------------------------------------------------------------
# TAB 3 Reactive Updates
# -------------------------------------------------------------------------
@app.callback(
    [Output('store-tab3', 'data'),
     Output('tab3-chips-container', 'children'),
     Output('tab3-breadcrumb-container', 'children'),
     Output('tab3-kpis-container', 'children'),
     Output('tab3-graph-c3-1', 'figure'),
     Output('tab3-graph-c3-2', 'figure'),
     Output('tab3-graph-c3-3', 'figure'),
     Output('tab3-graph-c3-4', 'figure'),
     Output('tab3-graph-c3-5', 'figure'),
     Output('tab3-findings-container', 'children')],
    [Input('tab3-filter-fy', 'value'),
     Input('tab3-filter-rus', 'value'),
     Input('tab3-btn-clear', 'n_clicks'),
     Input('tab3-btn-back', 'n_clicks'),
     Input('tab3-graph-c3-1', 'clickData'),
     Input('tab3-graph-c3-5', 'clickData'),
     Input('store-theme', 'data')],
    [State('store-tab3', 'data')]
)
def update_tab3(fy, rus, n_clear, n_back, click_c3_1, click_c3_5, theme_data, current_state):
    state = dict(current_state or DEFAULT_TAB3_STATE)
    ctx = callback_context

    if ctx.triggered:
        trig_id = ctx.triggered[0]['prop_id'].split('.')[0]
        if trig_id == 'tab3-btn-clear':
            state = dict(DEFAULT_TAB3_STATE)
        elif trig_id == 'tab3-btn-back':
            if state.get('level') == 'year':
                state['level'] = 'country'
            else:
                state['level'] = 'group'
                state['iso3'] = 'THA'
        elif trig_id == 'tab3-filter-fy':
            state['fy'] = fy
        elif trig_id == 'tab3-filter-rus':
            state['add_rus'] = bool('add_rus' in (rus or []))
        elif trig_id in ('tab3-graph-c3-1', 'tab3-graph-c3-5'):
            cdata = click_c3_1 if trig_id == 'tab3-graph-c3-1' else click_c3_5
            if cdata:
                iso = cdata['points'][0].get('customdata') or cdata['points'][0].get('location')
                if iso:
                    state['iso3'] = str(iso)
                    state['level'] = 'country'

    con = q.get_connection(DB_PATH)
    is_dark = (theme_data == 'dark')
    b = tab3_page.get_tab3_bundle(con, state, is_dark=is_dark)
    con.close()

    return (
        state,
        b['chips'],
        b['breadcrumb'],
        b['kpis'],
        b['fig_c3_1'],
        b['fig_c3_2'],
        b['fig_c3_3'],
        b['fig_c3_4'],
        b['fig_c3_5'],
        b['findings']
    )

# -------------------------------------------------------------------------
# Downloads Callbacks (Tab 1 & Tab 2 CSV)
# -------------------------------------------------------------------------
@app.callback(
    Output("tab1-download-dataframe-csv", "data"),
    Input("tab1-btn-download-csv", "n_clicks"),
    State("store-tab1", "data"),
    prevent_initial_call=True
)
def download_tab1_csv(n_clicks, state):
    con = q.get_connection(DB_PATH)
    df = q.get_t1(con, state or DEFAULT_TAB1_STATE)
    con.close()
    csv_str = "\ufeff" + df.to_csv(index=False)
    y0 = state.get('y0', 2015)
    y1 = state.get('y1', 2026)
    filename = f"adidur_tab1_{to_be(y0)}_{to_be(y1)}_filtered.csv"
    return dict(content=csv_str, filename=filename)

@app.callback(
    Output("tab2-download-dataframe-csv", "data"),
    Input("tab2-btn-download-csv", "n_clicks"),
    State("store-tab2", "data"),
    prevent_initial_call=True
)
def download_tab2_csv(n_clicks, state):
    con = q.get_connection(DB_PATH)
    df = q.get_t2(con, state or DEFAULT_TAB2_STATE)
    con.close()
    csv_str = "\ufeff" + df.to_csv(index=False)
    theme = state.get('theme', 'theme')
    filename = f"adidur_tab2_{theme}_filtered.csv"
    return dict(content=csv_str, filename=filename)

if __name__ == '__main__':
    app.run(debug=False, host='127.0.0.1', port=8050)
