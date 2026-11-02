"""Validated browser state. Years in URLs/DB are CE; only presentation uses BE."""
import copy,json,re
from urllib.parse import parse_qs,urlencode
from scripts.rules import THEMES
DEFAULTS={
 '1':dict(y0=2015,y1=2026,level='year',year=None,month=None,levels=['mention','media_evidence'],category=None,imp=None,inc_suspect=True,acsc_level='month',acsc_month=None,acsc_week=None,page=0,selected=None,detail=None),
 '2':dict(y0=2020,y1=2022,level='year',year=None,month=None,theme='covid',afnc_category=None,page=0,detail=None),
 '3':dict(fy=2024,groups=['ASEAN'],add_rus=False,iso3=None,level='group',page=0,detail=None),
 '4':dict(dataset='afnc_item')}
def defaults():return copy.deepcopy(DEFAULTS)
def be(year):return str(int(year)+543)
def display_date(value):
    if value is None:return 'ไม่มีข้อมูล'
    s=str(value)
    return re.sub(r'(?<!\d)(19\d{2}|20\d{2})(?=-|$)',lambda m:be(m.group()),s)
def integer(value,lo,hi,default):
    try:
        if isinstance(value,bool):return default
        return max(lo,min(hi,int(value)))
    except (ValueError,TypeError):return default

def sanitize(raw):
    result=defaults()
    if not isinstance(raw,dict):return result
    for tab,d in result.items():
        incoming=raw.get(tab,{})
        if not isinstance(incoming,dict):continue
        for k,v in incoming.items():
            if k not in d:continue
            if k in ('y0','y1','year','fy'):
                d[k]=None if k=='year' and v is None else integer(v,1983 if tab=='1' else 2010,2026 if k!='fy' else 2024,d[k])
            elif k=='page':d[k]=integer(v,0,100000,0)
            elif k in ('inc_suspect','add_rus'):d[k]=v is True or v==1
            elif k=='imp':d[k]=v if type(v)==int and v in (0,1) else None
            elif k=='levels':d[k]=[x for x in v if x in ('mention','media_evidence')] if isinstance(v,list) else d[k]
            elif k=='groups':d[k]=[x for x in v if x in ('ASEAN','ALL')] if isinstance(v,list) else ['ASEAN']
            elif k in ('month','acsc_month'):d[k]=v if isinstance(v,str) and re.fullmatch(r'(19\d\d|20\d\d)-(0[1-9]|1[0-2])',v) else None
            elif k=='acsc_week':d[k]=v if isinstance(v,str) and re.fullmatch(r'20\d\d-\d\d-\d\d',v) else None
            elif k=='theme':d[k]=v if v in THEMES else 'covid'
            elif k=='iso3':d[k]=v if isinstance(v,str) and re.fullmatch('[A-Z]{3}',v) else None
            elif k=='level':d[k]=v if v in ('year','month','items','group','country') else d[k]
            elif k=='acsc_level':d[k]=v if v in ('month','week') else 'month'
            elif k=='detail':d[k]=str(v)[:1000] if v else None
            elif k=='selected':d[k]=integer(v,1,10000000,None)
            elif k in ('category','afnc_category','dataset'):d[k]=v[:100] if isinstance(v,str) and v else None
        if 'y0' in d:
            if d['y0']>d['y1']:d['y0'],d['y1']=d['y1'],d['y0']
            if d['year'] is not None and not d['y0']<=d['year']<=d['y1']:d['year']=None;d['month']=None;d['level']='year'
            if d['month'] and not d['y0']<=int(d['month'][:4])<=d['y1']:d['month']=None
            if d['month']:d['year']=int(d['month'][:4]);d['level']='items'
    return result

def decode(search):
    q=parse_qs((search or '').lstrip('?'));tab=q.get('tab',['0'])[0]
    tab=tab if tab in ('0','1','2','3','4') else '0'
    try:raw=json.loads(q.get('s',['{}'])[0]) if len(search or '')<20000 else {}
    except (ValueError,TypeError):raw={}
    # Accept the human-readable example URL from the specification as well.
    if not raw and tab in ('1','2','3'):
        raw={tab:{k:v[0] for k,v in q.items() if k in DEFAULTS[tab]}}
        if 'levels' in q:raw[tab]['levels']=q['levels'][0].split(',')
    return tab,sanitize(raw)
def encode(tab,states):return '?'+urlencode({'tab':str(tab),'s':json.dumps(sanitize(states),ensure_ascii=False,separators=(',',':'))})
def up(tab,s):
    s=copy.deepcopy(s);s['page']=0
    if tab in ('1','2'):
        if tab=='1' and s.get('acsc_week'):s['acsc_week']=None
        elif tab=='1' and s.get('acsc_month'):s['acsc_month']=None;s['acsc_level']='month';s['month']=None;s['level']='month' if s.get('year') else 'year'
        elif s.get('month'):s['month']=None;s['level']='month'
        else:s['year']=None;s['level']='year'
    elif tab=='3':
        if s['level']=='year':s['level']='country'
        else:s['iso3']=None;s['level']='group'
    return s
