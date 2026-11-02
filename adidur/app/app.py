"""Adidur — จริงหรือเฟค : สร้าง Dash app, ฟอนต์, dcc.Location, dcc.Store 4 ก้อน + theme"""
import os
from dash import Dash, html, dcc, Input, Output, State, no_update, clientside_callback
from dash.exceptions import PreventUpdate

from .state import DEFAULTS, parse_tab, from_query, to_query
from .pages import landing, tab1, tab2, tab3

FONTS = ("https://fonts.googleapis.com/css2?family=Noto+Sans+Thai:wght@700;800&family=Sarabun:wght@400;500;700"
         "&display=swap")

app = Dash(__name__, title="Adidur — จริงหรือเฟค", suppress_callback_exceptions=True,
           external_stylesheets=[FONTS],
           meta_tags=[{"name": "viewport", "content": "width=device-width, initial-scale=1"}])
server = app.server
app.index_string = app.index_string.replace("<html>", '<html lang="th">')

TABS = [("1", "AI และภัยออนไลน์"), ("2", "ประเด็นต่างประเทศ"), ("3", "เสรีภาพอินเทอร์เน็ต")]

app.layout = html.Div([
    dcc.Location(id="url", refresh=False),
    dcc.Store(id="store-tab1", data=DEFAULTS[1]), dcc.Store(id="store-tab2", data=DEFAULTS[2]),
    dcc.Store(id="store-tab3", data=DEFAULTS[3]),
    dcc.Store(id="store-theme", data="light"), dcc.Store(id="resize-dummy"),
    html.Header([
        dcc.Link("Adidur", href="?", className="brand", refresh=False),
        html.Nav([dcc.Link(n, href=f"?tab={k}", id=f"nav-{k}", className="navtab", refresh=False)
                  for k, n in TABS], className="tabs"),
    ], className="topbar"),
    html.Main([
        html.Div(landing.landing(), id="page-landing"),
        html.Div(tab1.layout(), id="page-1", className="page"),
        html.Div(tab2.layout(), id="page-2", className="page"),
        html.Div(tab3.layout(), id="page-3", className="page"),
    ], className="main"),
    html.Div(landing.footer_sections(), id="page-foot"),
    html.Footer("Adidur — จริงหรือเฟค · ข้อมูลทุกชุดเป็นของผู้จัดทำต้นทาง · ปีแสดงเป็น พ.ศ.", className="footer"),
], id="root")


# ---------- แสดง/ซ่อนหน้าตาม URL ----------
@app.callback(
    [Output("page-landing", "style")] + [Output(f"page-{k}", "style") for k, _ in TABS] + [Output("page-foot", "style")] +
    [Output(f"nav-{k}", "className") for k, _ in TABS],
    Input("url", "search"))
def show_page(search):
    tab = parse_tab(search)
    styles = [{"display": "block"} if tab == "landing" else {"display": "none"}]
    styles += [{"display": "block"} if tab == k else {"display": "none"} for k, _ in TABS]
    styles.append({"display": "block"} if tab == "landing" else {"display": "none"})
    classes = ["navtab active" if tab == k else "navtab" for k, _ in TABS]
    return styles + classes


# ---------- URL -> store (เปิดลิงก์แล้วได้สถานะเดิม) ----------
@app.callback(
    Output("store-tab1", "data", allow_duplicate=True), Output("store-tab2", "data", allow_duplicate=True),
    Output("store-tab3", "data", allow_duplicate=True),
    Input("url", "search"),
    State("store-tab1", "data"), State("store-tab2", "data"), State("store-tab3", "data"),
    prevent_initial_call="initial_duplicate")
def url_to_store(search, s1, s2, s3):
    tab = parse_tab(search)
    cur = {"1": s1, "2": s2, "3": s3}
    if tab not in cur:
        raise PreventUpdate
    new = from_query(int(tab), search, cur[tab])
    if new == cur[tab]:
        raise PreventUpdate
    out = [no_update, no_update, no_update]
    out[int(tab) - 1] = new
    return out


# ---------- store -> URL (แชร์ลิงก์ได้) ----------
@app.callback(
    Output("url", "search"), Input("store-tab1", "data"), Input("store-tab2", "data"), Input("store-tab3", "data"),
    State("url", "search"), prevent_initial_call=True)
def store_to_url(s1, s2, s3, search):
    tab = parse_tab(search)
    cur = {"1": s1, "2": s2, "3": s3}
    if tab not in cur:
        raise PreventUpdate
    q = to_query(int(tab), cur[tab])
    if q == (search or ""):
        raise PreventUpdate
    return q


# ---------- theme: อ่าน prefers-color-scheme ----------
clientside_callback(
    "function(_p){return window.dash_clientside.adidur.initTheme();}",
    Output("store-theme", "data"), Input("url", "pathname"))

clientside_callback(
    "function(_s){setTimeout(function(){window.dispatchEvent(new Event('resize'));},120);return Date.now();}",
    Output("resize-dummy", "data"), Input("url", "search"))

for mod in (tab1, tab2, tab3):
    mod.register(app, None)


if __name__ == "__main__":
    app.run(debug=False, host="127.0.0.1", port=int(os.environ.get("PORT", 8050)))
