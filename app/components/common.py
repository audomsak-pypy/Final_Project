from dash import html,dcc
from app import queries as q
from app.state import be,display_date,encode
from scripts.rules import THEMES

def action(label,kind,value='',**kwargs):return html.Button(label,id={'type':'action','kind':kind,'value':str(value)},n_clicks=0,**kwargs)
def dropdown(key,label,options,value,multi=False):
    return html.Label([html.Span(label),dcc.Dropdown(id={'type':'field','key':key},options=options,value=value,multi=multi,clearable=True,placeholder='ทั้งหมด')],className='filter-field')
def filters(tab,s):
    fields=[]
    if tab in ('1','2'):
        years=[{'label':be(y),'value':y} for y in range(1983 if tab=='1' else 2015,2027)]
        fields=[dropdown('y0','ปีเริ่มต้น (พ.ศ.)',years,s['y0']),dropdown('y1','ปีสิ้นสุด (พ.ศ.)',years,s['y1']),dropdown('year','เจาะปี',years,s.get('year'))]
        months=[{'label':display_date(f'{y}-{m:02d}'),'value':f'{y}-{m:02d}'} for y in range(s['y0'],s['y1']+1) for m in range(1,13)]
        fields.append(dropdown('month','เจาะเดือน',months,s.get('month')))
        categories=q.query("SELECT DISTINCT category_th FROM afnc_item WHERE item_type='Verdict' ORDER BY category_th").category_th.tolist()
        if tab=='1':
            fields += [dropdown('levels','ระดับเกี่ยวกับ AI',[{'label':'กล่าวถึง AI','value':'mention'},{'label':'มีคำบ่งชี้สร้างสื่อ · ต้องตรวจสอบ','value':'media_evidence'}],s['levels'],True),dropdown('category','หมวดข่าว AFNC',categories,s['category']),dropdown('imp','แอบอ้างหน่วยงาน/บุคคล',[{'label':'แอบอ้าง','value':1},{'label':'ไม่พบคำว่าแอบอ้าง','value':0}],s['imp']),dropdown('inc_suspect','สัปดาห์ ACSC น่าสงสัย',[{'label':'รวม suspect','value':1},{'label':'ไม่รวม suspect','value':0}],int(s['inc_suspect'])),dropdown('acsc_month','ACSC เจาะเดือน',months,s['acsc_month'])]
            panel=q.acsc_panel(s);fields.append(dropdown('acsc_week','ACSC สัปดาห์ (รายละเอียด)',[{'label':display_date(x),'value':x} for x in panel.week_start],s['acsc_week']))
        else:fields += [dropdown('theme','ประเด็น (ตั้งเอง)',[{'label':v[0],'value':k} for k,v in THEMES.items()],s['theme']),dropdown('afnc_category','หมวด AFNC (ไม่มีผลกับ EU)',categories,s['afnc_category'])]
    elif tab=='3':
        fields=[dropdown('fy','ปีข้อมูล (พ.ศ.)',[{'label':f'{be(y)} · รายงาน {be(y+1)}','value':y} for y in range(2010,2025)],s['fy']),dropdown('groups','กลุ่มเปรียบเทียบ',[{'label':'อาเซียนที่มีข้อมูล','value':'ASEAN'},{'label':'ทุกประเทศในไฟล์','value':'ALL'}],s['groups'],True),dropdown('add_rus','เพิ่มรัสเซีย',[{'label':'ไม่เพิ่ม','value':0},{'label':'เพิ่ม','value':1}],int(s['add_rus'])),dropdown('iso3','เจาะประเทศ',[{'label':r.country_th,'value':r.iso3} for r in q.query('SELECT * FROM country ORDER BY country_th').itertuples()],s['iso3'])]
    chips=[]
    for k in ('year','month','category','imp','acsc_month','acsc_week','afnc_category','iso3'):
        if s.get(k) is not None:chips.append(action(f'{k}: {display_date(s[k])} ×','clear',k,className='chip'))
    return html.Div([html.Details([html.Summary('ตัวกรอง · เลือกแล้วกดนำไปใช้'),html.Div(fields,className='filter-grid'),action('นำตัวกรองไปใช้','apply',className='primary')],open=True,className='filters'),html.Div([html.Span('ใช้อยู่: '),*chips,action('ล้างตัวกรอง','reset'),action('ย้อนระดับ','up')],className='chips'),html.P(breadcrumb(tab,s),className='breadcrumb')])
def breadcrumb(tab,s):
    bits=['ทั้งหมด']
    if tab in ('1','2'):
        bits=[f"{be(s['y0'])}–{be(s['y1'])}"]
        bits += [display_date(s[k]) for k in ('year','month','acsc_month','acsc_week') if s.get(k)]
    if tab=='3':bits=[', '.join(s['groups']),be(s['fy']),s['iso3'] or 'ทุกประเทศ',s['level']]
    return ' › '.join(bits)
def number(n,digits=0):return 'ไม่มีข้อมูล' if n is None else f'{n:,.{digits}f}'
def kpi(label,value,unit,source,period,sub=None):
    return html.Div([html.P(label,className='eyebrow'),html.Div(value,className='kpi-value'),html.Div(unit),html.Small(f'{source} · {period}'),html.P(sub,className='muted') if sub else None],className='kpi')
def panel(title,children,note=None,wide=False):
    return html.Section([html.H3(title),html.P(note,className='scope') if note else None,* (children if isinstance(children,list) else [children])],className='panel'+(' wide' if wide else ''))
def graph(code,figure):return dcc.Graph(id={'type':'graph','code':code},figure=figure,config={'displayModeBar':False,'responsive':True},responsive=True)
def download(tab,states,label='ดาวน์โหลดผลตามตัวกรอง CSV'):
    return html.A(label,href=f'/download/filtered/{tab}.csv'+encode(tab,states),className='download',download='')
def table(frame,tab,s,columns=None,source=None):
    if source:frame=frame[frame.source==source]
    columns=columns or [c for c in ['source','id','date','title','category','reason','evidence_snippet','review_status','matched_by','matched_terms','url'] if c in frame]
    if frame.empty:return html.P('ไม่มีรายการตรงตัวกรอง · ถ้าช่วงอยู่นอก coverage แหล่งนี้ไม่มีข้อมูลในช่วงนี้',className='empty')
    page=s.get('page',0);total=len(frame);start=min(page*20,max(0,((total-1)//20)*20));small=frame if tab=='4' else frame.iloc[start:start+20]
    if s.get('selected') and 'id' in frame and 'source' in frame:
        selected=frame[(frame.source=='AFNC')&(frame.id==s['selected'])]
        small=__import__('pandas').concat([selected,small]).drop_duplicates(['source','id'])
    def value(c,v):
        if c in ('url','source_url','article_url'):return html.A('เปิดต้นทาง ↗',href=str(v),target='_blank',rel='noopener noreferrer') if str(v).startswith(('https://','http://')) else 'ไม่มีลิงก์'
        if c in ('date','week_start','week_end','data_year','report_edition','year','month'):return display_date(v)
        return str(v) if str(v) not in ('nan','None','<NA>') else '—'
    return html.Div([html.P(f'พบ {total:,} รายการ · แสดง {start+1}–{min(start+20,total)} · ดาวน์โหลดได้ครบชุด'),html.Div(html.Table([html.Thead(html.Tr([html.Th(q.HEADERS.get(c,c)) for c in columns])),html.Tbody([html.Tr([html.Td(value(c,r[c])) for c in columns],className='highlight' if s.get('selected')==r.get('id') else '') for _,r in small.iterrows()])]),className='table-scroll'),html.Div([action('หน้าก่อน','page-'+str(source or tab),max(0,page-1),disabled=page==0),action('หน้าถัดไป','page-'+str(source or tab),page+1,disabled=start+20>=total)],className='pager') if tab!='4' else None])
def summary(findings,limits):
    return html.Div([panel('ข้อค้นพบจากข้อมูล',html.P(findings)),panel('ข้อจำกัด',html.P(limits))],className='grid-2')
def footer():
    return html.Footer([html.H2('ทำไมจึงจัดทำ Dashboard นี้'),html.P('เพื่อสำรวจว่าแต่ละแหล่งบันทึกอะไรไว้ในเวลาเดียวกัน และเปิดหลักฐานต้นทางได้ด้วยตนเอง ข้อมูลคนละหน่วยและวิธีคัดเลือกจึงไม่ใช้พิสูจน์สาเหตุ'),html.H3('ค่าแต่ละค่าคืออะไร'),html.Dl([html.Dt(k) if i%2==0 else html.Dd(k) for i,k in enumerate(['Deepfake','ภาพ เสียง หรือวิดีโอสังเคราะห์ ในเว็บนับด้วยคำค้น AIID','Misinformation','เหตุการณ์ AIID ที่ Risk Domain ระบุ Misinformation','ข่าวปลอม / ข่าวบิดเบือน','คำตัดสิน AFNC: ไม่จริง / มีส่วนจริงแต่นำเสนอให้เข้าใจผิด ข่าวเท็จ = สองกลุ่มนี้','การหักล้าง','บันทึกหนึ่งเรื่องของ EUvsDisinfo ไม่ใช่บทความหนึ่งชิ้น','คะแนนเสรีภาพอินเทอร์เน็ต','คะแนน 0–100 สูงคือเสรีมาก แบ่งการเข้าถึง /25 เนื้อหา /35 สิทธิผู้ใช้ /40','ปีข้อมูล / ปีรายงาน','ปีการประเมิน / ปีตีพิมพ์รายงาน (ต่างกัน 1 ปีในไฟล์นี้)','ยอดเข้าชม','ยอดสะสม ณ 1 พ.ย. 2569 ไม่ใช่ความรุนแรงหรือความน่าเชื่อถือ'])]),html.Small('Adidur (ตั้งเอง) · ผู้จัดทำ: [ชื่อผู้จัดทำ] · Basic Programming for Data Scientist and Data Visualization')])
