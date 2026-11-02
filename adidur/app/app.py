"""app.py — เมนแอปพลิเคชัน Dash สำหรับ Adidur จริงหรือเฟค"""
import os
import sys
import sqlite3
import pandas as pd
import dash
from dash import html, dcc, Input, Output, State, callback_context
from dash.exceptions import PreventUpdate

from app.state import (
    DEFAULT_TAB1_STATE, DEFAULT_TAB2_STATE, DEFAULT_TAB3_STATE, DEFAULT_TAB4_STATE,
    state_to_url, url_to_state, to_be
)
import app.queries as q
import app.pages.landing as landing_page
import app.pages.tab1 as tab1_page
import app.pages.tab2 as tab2_page
import app.pages.tab3 as tab3_page
import app.pages.tab4 as tab4_page

# Paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "data", "adidur.db")
RAW_DIR = os.path.join(BASE_DIR, "data", "raw")

app = dash.Dash(
    __name__,
    suppress_callback_exceptions=True,
    title="Adidur — จริงหรือเฟค",
    meta_tags=[{"name": "viewport", "content": "width=device-width, initial-scale=1"}]
)

app.layout = html.Div([
    dcc.Location(id='url', refresh=False),
    dcc.Store(id='store-theme', data='light'),
    dcc.Store(id='store-tab1', data=DEFAULT_TAB1_STATE),
    dcc.Store(id='store-tab2', data=DEFAULT_TAB2_STATE),
    dcc.Store(id='store-tab3', data=DEFAULT_TAB3_STATE),
    dcc.Store(id='store-tab4', data=DEFAULT_TAB4_STATE),

    html.Div([
        html.Header([
            html.Div([
                dcc.Link([
                    html.Span("Adidur", className="brand-logo"),
                    html.Span(" — จริงหรือเฟค", style={'fontSize': '18px', 'fontWeight': '600', 'color': 'var(--ink)'})
                ], href="/", style={'textDecoration': 'none'}),
                html.Div("AI ข่าวปลอม และภัยออนไลน์: มองโลก เปรียบเทียบไทย", className="brand-meta")
            ], className="brand-row"),
            html.Nav([
                dcc.Link("หน้าเปิด", href="/", className="nav-tab-item", id="nav-landing"),
                dcc.Link("1. AI และภัยออนไลน์ในไทย", href="/?tab=1", className="nav-tab-item", id="nav-tab1"),
                dcc.Link("2. ประเด็นต่างประเทศกับไทย", href="/?tab=2", className="nav-tab-item", id="nav-tab2"),
                dcc.Link("3. เสรีภาพอินเทอร์เน็ต", href="/?tab=3", className="nav-tab-item", id="nav-tab3"),
                dcc.Link("4. แหล่งข้อมูลและดาวน์โหลด", href="/?tab=4", className="nav-tab-item", id="nav-tab4"),
            ], className="nav-tabs-bar", id="nav-bar")
        ], className="app-header", id="main-header"),

        html.Main(id='page-content')
    ], className="app-container")
])

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
# Page Router & Active Tab highlight
# -------------------------------------------------------------------------
@app.callback(
    [Output('page-content', 'children'),
     Output('main-header', 'style'),
     Output('nav-tab1', 'className'),
     Output('nav-tab2', 'className'),
     Output('nav-tab3', 'className'),
     Output('nav-tab4', 'className')],
    [Input('url', 'search'),
     Input('url', 'pathname')],
    [State('store-tab1', 'data'),
     State('store-tab2', 'data'),
     State('store-tab3', 'data'),
     State('store-theme', 'data')]
)
def render_page(search_query, pathname, s1, s2, s3, theme_data):
    is_dark = (theme_data == 'dark')
    con = q.get_connection(DB_PATH)

    # Determine tab from query
    tab = None
    if search_query:
        if 'tab=1' in search_query:
            tab = '1'
        elif 'tab=2' in search_query:
            tab = '2'
        elif 'tab=3' in search_query:
            tab = '3'
        elif 'tab=4' in search_query:
            tab = '4'

    c_base = "nav-tab-item"
    c1, c2, c3, c4 = c_base, c_base, c_base, c_base

    if tab == '1':
        c1 += " nav-tab-active"
        # Parse query state if present
        current_state = url_to_state(search_query, s1 or DEFAULT_TAB1_STATE)
        content = html.Div(id='tab1-wrapper', children=tab1_page.render_tab1_content(con, current_state, is_dark))
        header_style = {'display': 'block'}
    elif tab == '2':
        c2 += " nav-tab-active"
        current_state = url_to_state(search_query, s2 or DEFAULT_TAB2_STATE)
        content = html.Div(id='tab2-wrapper', children=tab2_page.render_tab2_content(con, current_state, is_dark))
        header_style = {'display': 'block'}
    elif tab == '3':
        c3 += " nav-tab-active"
        current_state = url_to_state(search_query, s3 or DEFAULT_TAB3_STATE)
        content = html.Div(id='tab3-wrapper', children=tab3_page.render_tab3_content(con, current_state, is_dark))
        header_style = {'display': 'block'}
    elif tab == '4':
        c4 += " nav-tab-active"
        content = html.Div(id='tab4-wrapper', children=tab4_page.render_tab4_content(con))
        header_style = {'display': 'block'}
    else:
        content = landing_page.layout()
        header_style = {'display': 'none'}

    con.close()
    return content, header_style, c1, c2, c3, c4

# -------------------------------------------------------------------------
# TAB 1 Interaction Callback (Filters, Drill down, Breadcrumbs, URL sync)
# -------------------------------------------------------------------------
@app.callback(
    Output('store-tab1', 'data'),
    [Input('tab1-filter-year-range', 'value'),
     Input('tab1-filter-levels', 'value'),
     Input('tab1-filter-category', 'value'),
     Input('tab1-filter-imp', 'value'),
     Input('tab1-filter-suspect', 'value'),
     Input('tab1-btn-clear', 'n_clicks'),
     Input('tab1-btn-back', 'n_clicks'),
     Input('tab1-graph-c1-1-2', 'clickData'),
     Input('tab1-graph-c1-3', 'clickData'),
     Input('tab1-graph-c1-5-6', 'clickData')],
    [State('store-tab1', 'data')]
)
def update_tab1_state(year_range, levels, category, imp, suspect, n_clear, n_back,
                      click_c1_1_2, click_c1_3, click_c1_5_6, current_state):
    ctx = callback_context
    if not ctx.triggered:
        raise PreventUpdate

    state = dict(current_state or DEFAULT_TAB1_STATE)
    trig_id = ctx.triggered[0]['prop_id'].split('.')[0]

    if trig_id == 'tab1-btn-clear':
        return dict(DEFAULT_TAB1_STATE)

    if trig_id == 'tab1-btn-back':
        # Drill up
        if state.get('month'):
            state['month'] = None
            state['level'] = 'month'
        elif state.get('year'):
            state['year'] = None
            state['level'] = 'year'
        return state

    if trig_id == 'tab1-filter-year-range' and year_range:
        state['y0'] = year_range[0]
        state['y1'] = year_range[1]
    elif trig_id == 'tab1-filter-levels':
        state['levels'] = levels or ['mention', 'media_evidence']
    elif trig_id == 'tab1-filter-category':
        state['category'] = None if category == 'ALL' else category
    elif trig_id == 'tab1-filter-imp':
        state['imp'] = None if imp == 'ALL' else imp
    elif trig_id == 'tab1-filter-suspect':
        state['inc_suspect'] = bool('inc' in (suspect or []))

    # Graph Clicks -> Drill down
    if trig_id == 'tab1-graph-c1-1-2' and click_c1_1_2:
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

    if trig_id == 'tab1-graph-c1-3' and click_c1_3:
        pt = click_c1_3['points'][0]
        cdata = pt.get('customdata') or pt.get('y')
        if cdata:
            state['category'] = cdata

    if trig_id == 'tab1-graph-c1-5-6' and click_c1_5_6:
        pt = click_c1_5_6['points'][0]
        cdata = pt.get('customdata')
        if cdata and str(cdata).startswith('202'):
            state['month'] = str(cdata)[:7]
            state['level'] = 'items'

    return state

# -------------------------------------------------------------------------
# TAB 2 Interaction Callback
# -------------------------------------------------------------------------
@app.callback(
    Output('store-tab2', 'data'),
    [Input('tab2-filter-year-range', 'value'),
     Input('tab2-filter-theme', 'value'),
     Input('tab2-btn-clear', 'n_clicks'),
     Input('tab2-btn-back', 'n_clicks'),
     Input('tab2-graph-c2-1', 'clickData'),
     Input('tab2-graph-c2-2', 'clickData')],
    [State('store-tab2', 'data')]
)
def update_tab2_state(year_range, theme, n_clear, n_back, click_c2_1, click_c2_2, current_state):
    ctx = callback_context
    if not ctx.triggered:
        raise PreventUpdate

    state = dict(current_state or DEFAULT_TAB2_STATE)
    trig_id = ctx.triggered[0]['prop_id'].split('.')[0]

    if trig_id == 'tab2-btn-clear':
        return dict(DEFAULT_TAB2_STATE)

    if trig_id == 'tab2-btn-back':
        state['year'] = None
        state['level'] = 'year'
        return state

    if trig_id == 'tab2-filter-year-range' and year_range:
        state['y0'] = year_range[0]
        state['y1'] = year_range[1]
    elif trig_id == 'tab2-filter-theme':
        state['theme'] = theme

    # Heatmap clicks -> select year
    if trig_id in ('tab2-graph-c2-1', 'tab2-graph-c2-2'):
        click_data = click_c2_1 if trig_id == 'tab2-graph-c2-1' else click_c2_2
        if click_data:
            x_val = click_data['points'][0].get('x')
            if x_val and 'พ.ศ.' in str(x_val):
                be_yr = int(str(x_val).replace('พ.ศ.', '').strip())
                state['year'] = be_yr - 543
                state['level'] = 'year'

    return state

# -------------------------------------------------------------------------
# TAB 3 Interaction Callback
# -------------------------------------------------------------------------
@app.callback(
    Output('store-tab3', 'data'),
    [Input('tab3-filter-fy', 'value'),
     Input('tab3-filter-rus', 'value'),
     Input('tab3-btn-clear', 'n_clicks'),
     Input('tab3-btn-back', 'n_clicks'),
     Input('tab3-graph-c3-1', 'clickData'),
     Input('tab3-graph-c3-5', 'clickData')],
    [State('store-tab3', 'data')]
)
def update_tab3_state(fy, rus, n_clear, n_back, click_c3_1, click_c3_5, current_state):
    ctx = callback_context
    if not ctx.triggered:
        raise PreventUpdate

    state = dict(current_state or DEFAULT_TAB3_STATE)
    trig_id = ctx.triggered[0]['prop_id'].split('.')[0]

    if trig_id == 'tab3-btn-clear':
        return dict(DEFAULT_TAB3_STATE)

    if trig_id == 'tab3-btn-back':
        if state.get('level') == 'year':
            state['level'] = 'country'
        else:
            state['level'] = 'group'
            state['iso3'] = 'THA'
        return state

    if trig_id == 'tab3-filter-fy':
        state['fy'] = fy
    elif trig_id == 'tab3-filter-rus':
        state['add_rus'] = bool('add_rus' in (rus or []))

    # C3.1 / C3.5 click on country -> drill down into country
    if trig_id in ('tab3-graph-c3-1', 'tab3-graph-c3-5'):
        cdata = click_c3_1 if trig_id == 'tab3-graph-c3-1' else click_c3_5
        if cdata:
            iso = cdata['points'][0].get('customdata') or cdata['points'][0].get('location')
            if iso:
                state['iso3'] = str(iso)
                state['level'] = 'country'

    return state

# -------------------------------------------------------------------------
# Downloads Callbacks
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

@app.callback(
    Output("download-raw-files", "data"),
    [Input("btn-dl-raw-aiid", "n_clicks"),
     Input("btn-dl-raw-fotn", "n_clicks"),
     Input("btn-dl-raw-eu", "n_clicks"),
     Input("btn-dl-raw-thai", "n_clicks")],
    prevent_initial_call=True
)
def download_raw(n1, n2, n3, n4):
    ctx = callback_context
    if not ctx.triggered:
        raise PreventUpdate
    tid = ctx.triggered[0]['prop_id'].split('.')[0]
    file_map = {
        'btn-dl-raw-aiid': 'AIID_Excel_Export-20261026.xlsx',
        'btn-dl-raw-fotn': 'freedom_on_the_net_scores.csv',
        'btn-dl-raw-eu': 'euvsdisinfo_base.csv',
        'btn-dl-raw-thai': 'thai-disinfo-scam-dataset.xlsx',
    }
    fname = file_map.get(tid)
    if fname:
        fpath = os.path.join(RAW_DIR, fname)
        if os.path.exists(fpath):
            return dcc.send_file(fpath)
    raise PreventUpdate

@app.callback(
    Output("download-prep-files", "data"),
    [Input(f"btn-dl-prep-{t}", "n_clicks") for t in
     ['aiid', 'afnc', 'aimatch', 'acsc', 'wp', 'eu', 'fotn', 'theme']],
    prevent_initial_call=True
)
def download_prepared(b1, b2, b3, b4, b5, b6, b7, b8):
    ctx = callback_context
    if not ctx.triggered:
        raise PreventUpdate
    tid = ctx.triggered[0]['prop_id'].split('.')[0]
    t_map = {
        'btn-dl-prep-aiid': 'aiid_incident',
        'btn-dl-prep-afnc': 'afnc_item',
        'btn-dl-prep-aimatch': 'afnc_ai_match',
        'btn-dl-prep-acsc': 'acsc_week',
        'btn-dl-prep-wp': 'weekly_panel',
        'btn-dl-prep-eu': 'eu_debunk',
        'btn-dl-prep-fotn': 'fotn_score',
        'btn-dl-prep-theme': 'theme',
    }
    table = t_map.get(tid)
    if table:
        con = q.get_connection(DB_PATH)
        df = q.get_table_data(con, table)
        con.close()
        csv_str = "\ufeff" + df.to_csv(index=False)
        return dict(content=csv_str, filename=f"adidur_prep_{table}.csv")
    raise PreventUpdate

@app.callback(
    Output("download-filtered-files", "data"),
    [Input("btn-dl-filtered-t1", "n_clicks"),
     Input("btn-dl-filtered-t2", "n_clicks"),
     Input("btn-dl-filtered-t3", "n_clicks")],
    [State("store-tab1", "data"),
     State("store-tab2", "data"),
     State("store-tab3", "data")],
    prevent_initial_call=True
)
def download_filtered(n1, n2, n3, s1, s2, s3):
    ctx = callback_context
    if not ctx.triggered:
        raise PreventUpdate
    tid = ctx.triggered[0]['prop_id'].split('.')[0]
    con = q.get_connection(DB_PATH)
    if tid == 'btn-dl-filtered-t1':
        df = q.get_t1(con, s1 or DEFAULT_TAB1_STATE)
        fname = "adidur_tab1_filtered.csv"
    elif tid == 'btn-dl-filtered-t2':
        df = q.get_t2(con, s2 or DEFAULT_TAB2_STATE)
        fname = "adidur_tab2_filtered.csv"
    else:
        df = q.get_c3_1(con, s3 or DEFAULT_TAB3_STATE)
        fname = "adidur_tab3_filtered.csv"
    con.close()
    csv_str = "\ufeff" + df.to_csv(index=False)
    return dict(content=csv_str, filename=fname)

if __name__ == '__main__':
    app.run(debug=True, host='127.0.0.1', port=8050)
