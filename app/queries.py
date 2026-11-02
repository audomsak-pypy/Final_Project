"""Bound SQL shared by figures, KPIs, evidence and CSV exports."""
from pathlib import Path
import sqlite3
import pandas as pd
ROOT=Path(__file__).resolve().parents[1];DB=ROOT/'data/adidur.db'
TABLES=['aiid_incident','afnc_item','afnc_ai_match','weekly_panel','acsc_week','eu_debunk','eu_article','eu_debunk_keyword','theme','eu_debunk_theme','afnc_theme','fotn_score','country_group','thai_data_dictionary']
def query(sql,params=(),db=None):
    with sqlite3.connect(f'file:{db or DB}?mode=ro',uri=True) as c:
        c.execute('PRAGMA foreign_keys=ON')
        return pd.read_sql_query(sql,c,params=params)
def table(name):
    if name not in TABLES:raise ValueError('Unknown export table')
    return query(f'SELECT * FROM {name}')
def time_where(s,alias='',year='year',month='month'):
    pre=alias+'.' if alias else '';clauses=[f'{pre}{year} BETWEEN ? AND ?'];args=[s['y0'],s['y1']]
    if s.get('year') is not None:clauses.append(f'{pre}{year}=?');args.append(s['year'])
    if s.get('month'):clauses.append(f'{pre}{month}=?');args.append(s['month'])
    return ' AND '.join(clauses),args

def aiid(s,misinfo=False):
    wh,args=time_where(s)
    return query(f'SELECT * FROM aiid_incident WHERE {wh} AND '+('is_misinfo=1' if misinfo else 'is_deepfake=1')+' ORDER BY date,incident_id',args)
def afnc(s,ai=True):
    wh,args=time_where(s,'a');join='JOIN afnc_ai_match m USING(post_id)' if ai else ''
    if ai:
        levels=s.get('levels',['mention','media_evidence'])
        wh+=' AND m.ai_level IN ('+','.join('?' for _ in levels)+')' if levels else ' AND 0'
        args+=levels
        if s.get('category'):wh+=' AND a.category_th=?';args.append(s['category'])
        if s.get('imp') is not None:wh+=' AND m.impersonation_flag=?';args.append(s['imp'])
    else:
        wh+=" AND a.item_type='Verdict' AND a.verdict_en IN ('Fake','Distorted')"
        if s.get('theme'):
            wh+=' AND EXISTS (SELECT 1 FROM afnc_theme t WHERE t.post_id=a.post_id AND t.theme_id=?)';args.append(s['theme'])
        if s.get('afnc_category'):wh+=' AND a.category_th=?';args.append(s['afnc_category'])
    return query(f'SELECT a.*'+(',m.ai_level,m.matched_terms,m.evidence_snippet,m.review_status,m.impersonation_flag' if ai else '')+f' FROM afnc_item a {join} WHERE {wh} ORDER BY a.date,a.post_id',args)
def acsc(s,include=None):
    wh,args=time_where(s,year='CAST(substr(week_start,1,4) AS INT)')
    if not (s.get('inc_suspect',True) if include is None else include):wh+=" AND COALESCE(flag_type,'')<>'suspect'"
    return query(f'SELECT * FROM acsc_week WHERE {wh} ORDER BY week_start',args)
def acsc_panel(s):
    # Map panel dates to real source intervals; use real week_start for month attribution.
    year_expr="CAST(substr(COALESCE(c.week_start,w.week_start),1,4) AS INT)"
    wh,args=time_where(s,year=year_expr,month="substr(COALESCE(c.week_start,w.week_start),1,7)")
    include=s.get('inc_suspect',True)
    frame=query(f'''SELECT w.week_start,w.week_end,c.week_start AS source_week_start,c.week_end AS source_week_end,c.days,
      w.acsc_cases AS cases,w.acsc_loss_baht AS loss_baht,w.acsc_loss_precision AS loss_precision,
      c.flag_type,c.flag,c.notes,w.acsc_reported,w.acsc_source_url AS source_url,
      substr(COALESCE(c.week_start,w.week_start),1,7) AS month
      FROM weekly_panel w LEFT JOIN acsc_week c ON c.panel_week_start=w.week_start
      WHERE w.week_start>='2025-11-09' AND {wh} ORDER BY w.week_start''',args)
    frame['missing_reason']=frame.acsc_reported.map(lambda v:'' if v else 'ไม่มีรายงาน')
    if not include:
        mask=frame.flag_type=='suspect';frame.loc[mask,['cases','loss_baht']]=float('nan');frame.loc[mask,'missing_reason']='ไม่รวมเพราะ suspect'
    return frame

def eu_items(s):
    wh,args=time_where(s,'d')
    if s.get('theme'):wh+=' AND t.theme_id=?';args.append(s['theme'])
    return query(f'''SELECT DISTINCT d.*,t.matched_terms,'keyword' AS matched_by,
        (SELECT article_url FROM eu_article e WHERE e.debunk_id=d.debunk_id ORDER BY (class='disinformation') DESC,article_id LIMIT 1) AS url
        FROM eu_debunk d JOIN eu_debunk_theme t USING(debunk_id) WHERE {wh} ORDER BY d.debunk_date,d.debunk_id''',args)

def theme_shares(s,source):
    if source=='EU':base='eu_debunk';key='debunk_id';links='eu_debunk_theme';extra=''
    else:base='afnc_item';key='post_id';links='afnc_theme';extra=" AND item_type='Verdict' AND verdict_en IN ('Fake','Distorted')"
    # denominator deliberately ignores selected theme and AFNC category; the complete source in each year.
    return query(f'''WITH den AS (SELECT year,COUNT(*) AS denominator FROM {base} WHERE year BETWEEN ? AND ? {extra} GROUP BY year),
        nums AS (SELECT b.year,t.theme_id,COUNT(DISTINCT t.{key}) AS n FROM {links} t JOIN {base} b USING({key}) WHERE b.year BETWEEN ? AND ? GROUP BY b.year,t.theme_id)
        SELECT den.year,theme.theme_id,theme.theme_th,den.denominator,COALESCE(nums.n,0) AS n,
        100.0*COALESCE(nums.n,0)/den.denominator AS pct FROM den CROSS JOIN theme
        LEFT JOIN nums ON nums.year=den.year AND nums.theme_id=theme.theme_id
        ORDER BY den.year,theme.theme_id''',[s['y0'],s['y1'],s['y0'],s['y1']])

def rank(s):
    wh='f.data_year=?';args=[s['fy']]
    if 'ALL' not in s.get('groups',['ASEAN']):
        groups=['ASEAN'] if 'ASEAN' in s.get('groups',[]) else []
        if s.get('add_rus'):groups+=['RUS']
        if groups:wh+=' AND EXISTS (SELECT 1 FROM country_group g WHERE g.iso3=f.iso3 AND g.group_name IN ('+','.join('?' for _ in groups)+'))';args+=groups
        else:wh+=' AND 0'
    return query(f'''SELECT f.*,RANK() OVER (ORDER BY total_score DESC) AS rank_in_group,COUNT(*) OVER () AS n_in_group
        FROM fotn_score f WHERE {wh} ORDER BY total_score DESC,iso3''',args)
def thai_score(s):return query("SELECT * FROM fotn_score WHERE iso3='THA' AND data_year=?",[s['fy']])
def components(s):
    if not s.get('iso3'):return rank(s)
    return query('SELECT * FROM fotn_score WHERE iso3=?'+(' AND data_year=?' if s.get('level')=='year' else '')+' ORDER BY data_year',[s['iso3']]+([s['fy']] if s.get('level')=='year' else []))
def thai_context():
    return query("SELECT f.*, (SELECT COUNT(*) FROM afnc_item a WHERE item_type='Verdict' AND a.year=f.data_year) AS afnc_verdicts FROM fotn_score f WHERE iso3='THA' AND data_year BETWEEN 2019 AND 2024 ORDER BY data_year")
def eu_context():return query('SELECT year,COUNT(*) AS debunks,SUM(n_articles) AS articles FROM eu_debunk GROUP BY year ORDER BY year')
def totals(frame):
    if frame.empty:return (None,None,None)
    both=frame.dropna(subset=['cases','loss_baht']);cases=both.cases.sum();loss=both.loss_baht.sum()
    return (int(cases),int(loss),float(loss/cases) if cases else None) if not both.empty else (None,None,None)
def evidence(tab,s):
    if tab=='1':
        a=afnc(s);i=aiid(s)
        aa=pd.DataFrame(dict(source='AFNC',id=a.post_id,date=a.date,title=a.title,category=a.category_th,reason=a.matched_terms,evidence_snippet=a.evidence_snippet,review_status=a.review_status,url=a.url,view_count=a.view_count))
        ii=pd.DataFrame(dict(source='AIID',id=i.incident_id,date=i.date,title=i.title,category=i.risk_domain,reason=i.deepfake_terms,evidence_snippet=i.description,review_status='คำค้นโครงการ',url=i.url))
        return pd.concat([aa,ii],ignore_index=True).sort_values(['date','source','id'],ascending=[False,True,True])
    if tab=='2':
        a=afnc(s,ai=False);e=eu_items(s)
        aa=pd.DataFrame(dict(source='AFNC',id=a.post_id,date=a.date,title=a.title,category=a.category_th,url=a.url))
        if not a.empty:
            rules=query('SELECT post_id,matched_by,matched_terms FROM afnc_theme WHERE theme_id=?',[s['theme']]);aa=aa.merge(rules,left_on='id',right_on='post_id',how='left')
        ee=pd.DataFrame(dict(source='EUvsDisinfo',id=e.debunk_id,date=e.debunk_date,title=e.keywords,matched_by=e.matched_by,matched_terms=e.matched_terms,url=e.url))
        return pd.concat([aa,ee],ignore_index=True).sort_values(['date','source','id'],ascending=[False,True,True])
    return rank(s)
HEADERS={'source':'แหล่งข้อมูล','date':'วันที่','title':'หัวข้อ','category':'หมวด','reason':'กฎและคำที่ตรง','evidence_snippet':'ข้อความหลักฐาน','review_status':'สถานะตรวจสอบ','view_count':'ยอดเข้าชม','url':'ลิงก์ต้นทาง','matched_by':'วิธีจับคู่','matched_terms':'คำที่ตรง','country_th':'ประเทศ','total_score':'คะแนนรวม','rank_in_group':'อันดับ','n_in_group':'จำนวนประเทศ'}
def csv_bytes(frame):return frame.rename(columns=HEADERS).to_csv(index=False).encode('utf-8-sig')
def news_selection(frame):
    ordered=frame.sort_values(['view_count','post_id'],ascending=[False,True]);top=ordered.head(3)
    remaining=ordered[~ordered.post_id.isin(top.post_id)]
    low=remaining.sort_values(['view_count','post_id']).head(1)
    return top,low

def comparable(s):
    results={}
    for year in (2025,2026):
        state={**s,'y0':year,'y1':year,'year':None,'month':None}
        af=afnc(state);ai=aiid(state)
        results[year]={'ai_posts':len(af[af.date.str[5:]<='10-31']),'deepfake':len(ai[ai.date.str[5:]<='10-26'])}
    def change(key):
        old=results[2025][key];new=results[2026][key]
        return f'{old:,} → {new:,} ('+(f'{(new-old)/old*100:+.1f}%' if old else 'คำนวณไม่ได้ ฐานเป็นศูนย์')+')'
    return 'บริบทช่วงเดียวกัน 2568 → 2569: AFNC ข่าว AI ม.ค.–ต.ค. '+change('ai_posts')+'; AIID Deepfake 1 ม.ค.–26 ต.ค. '+change('deepfake')+' · AIID อาจบันทึกล่าช้า ไม่สรุปว่าลดลง · ACSC ไม่มีปีก่อนให้เทียบ คำนวณไม่ได้'
