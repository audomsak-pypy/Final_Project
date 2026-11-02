"""Adidur Dash application. URL is the canonical serialized per-tab state."""
from pathlib import Path
import copy,json,os,time
from urllib.parse import quote
from dash import Dash,html,dcc,Input,Output,State,ALL,ctx,no_update
from dash.exceptions import PreventUpdate
from flask import request,send_file,Response,abort
from app import queries as q
from app.state import defaults,decode,encode,sanitize,up,be,display_date
from app.components.common import action,footer
from app.pages import landing,tab1,tab2,tab3,tab4

if not q.DB.exists():
    from scripts.build_db import build
    build()
app=Dash(__name__,title='Adidur — จริงหรือเฟค',assets_folder=str(Path(__file__).parent/'assets'),suppress_callback_exceptions=True,update_title='กำลังอ่านข้อมูล…')
server=app.server
app.index_string='''<!DOCTYPE html><html lang="th"><head>{%metas%}<title>{%title%}</title>{%favicon%}{%css%}</head><body><a class="skip" href="#page">ข้ามไปเนื้อหา</a>{%app_entry%}<footer>{%config%}{%scripts%}{%renderer%}</footer></body></html>'''
app.layout=html.Div([dcc.Location(id='url',refresh=False),*[dcc.Store(id=f'tab{t}',data=s) for t,s in defaults().items()],dcc.Store(id='theme',data=False),dcc.Interval(id='theme-init',interval=500,max_intervals=1),html.Header([action('Adidur','tab','0',className='brand'),html.Span('จริงหรือเฟค',className='brand-sub'),html.Nav([action(label,'tab',str(t),className='nav-tab',**{'data-tab':str(t)}) for t,label in enumerate(['AI และภัยออนไลน์','ประเด็นต่างประเทศกับไทย','เสรีภาพอินเทอร์เน็ต','แหล่งข้อมูล'],1)],**{'aria-label':'แท็บ Dashboard'})]),html.Main(id='page',tabIndex=-1),html.Div(id='timing',className='timing')])
app.clientside_callback('''function(n) { const mq=window.matchMedia('(prefers-color-scheme: dark)'); document.documentElement.dataset.theme=mq.matches?'dark':'light'; if (!window.adidurThemeListener) { mq.addEventListener('change', function(e) { document.documentElement.dataset.theme=e.matches?'dark':'light'; window.dash_clientside.set_props('theme',{data:e.matches}); });window.adidurThemeListener=true;} return mq.matches;}''',Output('theme','data'),Input('theme-init','n_intervals'))
app.clientside_callback('''function(search) { let tab=new URLSearchParams(search).get('tab') || '0';document.querySelectorAll('[data-tab]').forEach(function(el){el.classList.toggle('active',el.dataset.tab===tab);el.setAttribute('aria-current',el.dataset.tab===tab?'page':'false');}); return window.dash_clientside.no_update;}''',Output('theme-init','disabled'),Input('url','search'))

@app.callback(Output('page','children'),*[Output(f'tab{t}','data') for t in ('1','2','3','4')],Output('timing','children'),Input('url','search'),Input('theme','data'))
def render(search,dark):
    started=time.perf_counter();tab,states=decode(search)
    if tab=='0':page=landing.render()
    else:
        mod={'1':tab1,'2':tab2,'3':tab3,'4':tab4}[tab]
        page=[mod.render(states[tab],states,bool(dark)),html.Div([html.H3('จุดที่เลือก'),html.P(states[tab].get('detail') or 'แตะจุดในกราฟเพื่อดูค่าที่นี่ หรือใช้ตัวกรองผ่านคีย์บอร์ด')],className='point-detail'),footer()]
    return (page,*[states[t] for t in ('1','2','3','4')],f'ประมวลผลฝั่งเซิร์ฟเวอร์ {(time.perf_counter()-started)*1000:.0f} ms')

@app.callback(Output('url','search'),Input({'type':'action','kind':ALL,'value':ALL},'n_clicks'),Input({'type':'graph','code':ALL},'clickData'),State({'type':'field','key':ALL},'value'),State({'type':'field','key':ALL},'id'),State('url','search'),prevent_initial_call=True)
def navigate(clicks,points,values,ids,search):
    triggered=ctx.triggered_id
    if not triggered or not ctx.triggered or not ctx.triggered[0].get('value'):raise PreventUpdate
    tab,states=decode(search)
    if triggered['type']=='action':
        kind=triggered['kind'];v=triggered['value']
        if kind=='tab':return encode(v,states)
        if tab=='0':raise PreventUpdate
        s=states[tab]
        if kind=='apply':
            for key,value in zip(ids,values):s[key['key']]=value
            if tab in ('1','2'):
                s['level']='items' if s.get('month') else 'month' if s.get('year') else 'year'
                if s.get('acsc_month'):s['month']=s['acsc_month'];s['year']=int(s['month'][:4]);s['acsc_level']='week'
            if tab=='3' and s.get('iso3'):s['level']='country'
            s['page']=0
        elif kind=='reset':states[tab]=defaults()[tab]
        elif kind=='up':states[tab]=up(tab,s)
        elif kind=='clear':
            s[v]=None;s['page']=0
            if v=='year':s['month']=None;s['level']='year'
            if v=='month':s['level']='month' if s.get('year') else 'year'
            if v=='acsc_month':s['acsc_week']=None;s['acsc_level']='month';s['month']=None
        elif kind.startswith('page-'):s['page']=int(v)
        elif kind=='select':s['selected']=int(v);s['page']=0
        elif kind=='imp':s['imp']=None if s.get('imp')==1 else 1;s['page']=0
    else:
        if tab not in ('1','2','3'):raise PreventUpdate
        point=ctx.triggered[0]['value']['points'][0];code=triggered['code'];s=states[tab];custom=point.get('customdata',[])
        # Compact filter state + selected-point text only, never a news dataset in browser storage.
        s['detail']=f"{code}: {point.get('x','')} · {point.get('y','')}"+(f' · จำนวน {custom[2]} / ตัวหาร {custom[3]}' if code.startswith('heat') and len(custom)>3 else '')
        if code in ('timeline1','theme2','stack2','misinfo2'):
            value=custom[0] if custom else point.get('x')
            if isinstance(value,str) and len(value)==7:s['month']=value;s['year']=int(value[:4]);s['level']='items'
            else:
                try:s['year']=int(value);s['month']=None;s['level']='month'
                except (ValueError,TypeError):raise PreventUpdate
            if code=='stack2' and len(custom)>1:s['afnc_category']=custom[1]
        elif code=='category1':s['category']=None if s.get('category')==custom[0] else custom[0]
        elif code=='acsc1':
            value=custom[0]
            if custom[1]=='month':s['acsc_month']=value;s['acsc_level']='week';s['month']=value;s['year']=int(value[:4]);s['level']='items'
            else:s['acsc_week']=value
        elif code.startswith('heat'):
            s['year']=int(custom[0]);s['theme']=custom[1];s['month']=None;s['level']='month'
        elif code=='rank3':s['iso3']=custom[0];s['level']='country'
        elif code=='components3':
            if s['level']=='group':s['iso3']=custom[1];s['level']='country'
            else:s['fy']=int(custom[0]);s['iso3']=custom[1];s['level']='year'
        elif code=='context3':s['fy']=int(custom[0])
        else:return no_update
        s['page']=0
    result=encode(tab,states)
    return no_update if result==search else result

@server.get('/health')
def health():
    return {'status':'ok','afnc_rows':int(q.query('SELECT COUNT(*) n FROM afnc_item').iloc[0,0])}
@server.get('/download/raw/<name>')
def raw_download(name):
    from scripts.build_db import FILES
    if name not in FILES:abort(404)
    return send_file(q.ROOT/'Datasets'/name,as_attachment=True,download_name=name)
def csv_response(frame,name):
    return Response(q.csv_bytes(frame),mimetype='text/csv; charset=utf-8',headers={'Content-Disposition':"attachment; filename*=UTF-8''"+quote(name)})
@server.get('/download/processed/<name>.csv')
def processed_download(name):
    if name not in q.TABLES:abort(404)
    return csv_response(q.table(name),f'adidur_{name}_prepared.csv')
@server.get('/download/filtered/<tab>.csv')
def filtered_download(tab):
    if tab not in ('1','2','3'):abort(404)
    _,states=decode('?'+request.query_string.decode());s=states[tab]
    scope='_'.join(f'{k}-{str(v)}' for k,v in s.items() if v is not None and k not in ('page','detail','selected'))
    # Readable tab/year plus a stable digest encodes all remaining filters without exceeding filename limits.
    import hashlib
    years=f'{be(s["y0"])}-{be(s["y1"])}' if 'y0' in s else be(s['fy'])
    return csv_response(q.evidence(tab,s),f'adidur_tab{tab}_{years}_'+hashlib.sha256(scope.encode()).hexdigest()[:10]+'.csv')
@server.get('/download/acsc.csv')
def acsc_download():
    _,states=decode('?'+request.query_string.decode());return csv_response(q.acsc_panel(states['1']),'adidur_ACSC_'+be(states['1']['y0'])+'-'+be(states['1']['y1'])+'.csv')
if __name__=='__main__':app.run(host='0.0.0.0',port=int(os.environ.get('PORT','8050')),debug=False)
