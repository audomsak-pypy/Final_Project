"""Atomic, repeatable source → SQLite + BOM CSV + audit manifest. No source writes."""
from pathlib import Path
import argparse, hashlib, json, sqlite3, time, sys
import pandas as pd
if __package__ in (None,''): sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from scripts.rules import COUNTRIES, THEMES, DEEPFAKE, RULE_VERSION, clean, match_ai
ROOT=Path(__file__).resolve().parents[1]
FILES=['AIID_Excel_Export-20261026.xlsx','freedom_on_the_net_scores.csv','euvsdisinfo_base.csv','thai-disinfo-scam-dataset.xlsx']

def profile(df, key):
    return {'rows':len(df),'duplicate_keys':int(df.duplicated(key).sum()),'nulls':{str(k):int(v) for k,v in df.isna().sum().items()},'schema':{str(k):str(v) for k,v in df.dtypes.items()}}

def dates(df, cols):
    for c in cols:
        df[c]=pd.to_datetime(df[c],errors='raise').dt.strftime('%Y-%m-%d')
    return df

def write_table(conn,name,df,pk,fks=()):
    if df.duplicated(pk).any(): raise ValueError(f'{name}: duplicate primary key {pk}')
    types={c:('INTEGER' if pd.api.types.is_integer_dtype(df[c]) or pd.api.types.is_bool_dtype(df[c]) else 'REAL' if pd.api.types.is_numeric_dtype(df[c]) else 'TEXT') for c in df}
    cols=[f'"{c}" {t}'+(' NOT NULL' if c in pk else '') for c,t in types.items()]
    cols+=['PRIMARY KEY ('+','.join('"'+c+'"' for c in pk)+')']
    cols+=list(fks)
    conn.execute(f'CREATE TABLE "{name}" ({",".join(cols)})')
    df.to_sql(name,conn,if_exists='append',index=False)

def build(input_dir=ROOT/'Datasets',output=ROOT/'data/adidur.db'):
    started=time.perf_counter();src=Path(input_dir);out=Path(output);out.parent.mkdir(parents=True,exist_ok=True)
    for f in FILES:
        if not (src/f).is_file(): raise FileNotFoundError(f'Required source: {src/f}')
    sources=[{'file':f,'sha256':hashlib.sha256((src/f).read_bytes()).hexdigest(),'bytes':(src/f).stat().st_size} for f in FILES]
    ai=pd.read_excel(src/FILES[0],sheet_name='Incidents',header=2)
    f=pd.read_csv(src/FILES[1]); eu=pd.read_csv(src/FILES[2]);book=pd.ExcelFile(src/FILES[3])
    a=pd.read_excel(book,'afnc_items');w=pd.read_excel(book,'weekly_panel');c=pd.read_excel(book,'acsc_weekly');dictionary=pd.read_excel(book,'data_dictionary')
    full=src/'afnc_items.csv'
    if full.exists():
        a=pd.read_csv(full);sources.append({'file':full.name,'sha256':hashlib.sha256(full.read_bytes()).hexdigest(),'bytes':full.stat().st_size})
    before={'aiid_incident':profile(ai,['Incident ID']),'fotn_score':profile(f,['iso3','data_year']),'eu_article':profile(eu,['article_id']),'afnc_item':profile(a,['post_id']),'weekly_panel':profile(w,['week_start']),'acsc_week':profile(c,['week_start'])}
    ai=ai.rename(columns={'Incident ID':'incident_id','Implicated Systems':'implicated_systems','Risk Domain':'risk_domain'})
    ai=ai[['incident_id','date','year','title','description','implicated_systems','risk_domain','report_count']].copy();dates(ai,['date']);ai['month']=ai.date.str[:7]
    text=ai[['title','description','implicated_systems']].fillna('').agg(' '.join,axis=1)
    ai['deepfake_terms']=text.map(lambda v:'; '.join(dict.fromkeys(m.group() for m in DEEPFAKE.finditer(v))))
    ai['is_deepfake']=(ai.deepfake_terms!='').astype(int);ai['is_misinfo']=ai.risk_domain.fillna('').str.contains('Misinformation',case=False).astype(int)
    ai['url']=ai.incident_id.map(lambda v:f'https://incidentdatabase.ai/cite/{v}')
    assert (ai.date.str[:4].astype(int)==ai.year).all()
    dates(a,['date','week_start']);a=a.rename(columns={'content':'content_500'});a['clean_text']=(a.title.fillna('')+' '+a.content_500.fillna('')).map(clean)
    false=a[(a.item_type=='Verdict')&a.verdict_en.isin(['Fake','Distorted'])]
    matches=[]
    for r in false.itertuples():
        match=match_ai(r.clean_text)
        if match: matches.append({'post_id':r.post_id,**match})
    m=pd.DataFrame(matches,columns=['post_id','ai_level','matched_terms','evidence_snippet','review_status','impersonation_flag','rule_version'])
    dates(w,['week_start','week_end']);dates(c,['week_start','week_end','article_date'])
    c['month']=c.week_start.str[:7];c['flag_type']=c.flag.map(lambda v:'suspect' if str(v).startswith('Suspect') else 'note' if pd.notna(v) else None)
    # Explicit source-URL mapping retains the actual 8-day source interval and panel calendar.
    lookup=w[w.acsc_reported.astype(bool)].set_index('acsc_source_url').week_start
    c['panel_week_start']=c.source_url.map(lookup)
    if c.panel_week_start.isna().any():raise ValueError('ACSC source URL missing in weekly panel')
    assert int(c.cases.sum())==int(w.acsc_cases.sum())
    eu['debunk_date']=pd.to_datetime(eu.debunk_date,format='%d-%m-%Y').dt.strftime('%Y-%m-%d')
    assert (eu.groupby('debunk_id').debunk_date.nunique()==1).all()
    d=eu.groupby('debunk_id',sort=True).agg(debunk_date=('debunk_date','first'),keywords=('keywords','first'),n_articles=('article_id','size')).reset_index()
    d['year']=d.debunk_date.str[:4].astype(int);d['month']=d.debunk_date.str[:7]
    keywords=[];et=[];at=[];themes=[]
    for row in d.itertuples():
        words=list(dict.fromkeys(v.strip() for v in str(row.keywords).split(',') if pd.notna(row.keywords) and v.strip()))
        keywords.extend({'debunk_id':row.debunk_id,'keyword':v} for v in words)
        for tid,(_,ew,_,_) in THEMES.items():
            matched=[v for v in words if v.casefold() in {x.casefold() for x in ew.split('|')}]
            if matched:et.append({'debunk_id':row.debunk_id,'theme_id':tid,'matched_terms':'; '.join(matched)})
    for tid,(name,ew,aw,cats) in THEMES.items():
        themes.append(dict(theme_id=tid,theme_th=name,named_by='โครงการ (ตั้งเอง)',eu_rule=ew,afnc_rule='หมวด: '+','.join(cats) if cats else aw))
        for row in false.itertuples():
            matched=[row.category_en] if cats and row.category_en in cats else [] if cats else list(dict.fromkeys(__import__('re').findall(aw,row.clean_text,__import__('re').I)))
            if matched:at.append(dict(post_id=row.post_id,theme_id=tid,matched_by='category' if cats else 'keyword',matched_terms='; '.join(matched)))
    f['country_th']=f.iso3.map(COUNTRIES).fillna(f.country)
    assert (f.total_score==f[['obstacles_to_access','limits_on_content','violations_of_user_rights']].sum(axis=1)).all()
    countries=f[['iso3','country','country_th']].drop_duplicates('iso3')
    groups=pd.DataFrame([dict(iso3=iso,group_name='ASEAN' if iso!='RUS' else 'RUS') for iso in COUNTRIES])
    fk=lambda col,table,ref:f'FOREIGN KEY("{col}") REFERENCES "{table}"("{ref}")'
    tables=[('country',countries,['iso3'],[]),('theme',pd.DataFrame(themes),['theme_id'],[]),('aiid_incident',ai,['incident_id'],[]),('afnc_item',a,['post_id'],[]),('afnc_ai_match',m,['post_id'],[fk('post_id','afnc_item','post_id')]),('weekly_panel',w,['week_start'],[]),('acsc_week',c,['week_start'],[fk('panel_week_start','weekly_panel','week_start')]),('eu_debunk',d,['debunk_id'],[]),('eu_article',eu.drop(columns=['keywords','debunk_date']),['article_id'],[fk('debunk_id','eu_debunk','debunk_id')]),('eu_debunk_keyword',pd.DataFrame(keywords),['debunk_id','keyword'],[fk('debunk_id','eu_debunk','debunk_id')]),('eu_debunk_theme',pd.DataFrame(et),['debunk_id','theme_id'],[fk('debunk_id','eu_debunk','debunk_id'),fk('theme_id','theme','theme_id')]),('afnc_theme',pd.DataFrame(at),['post_id','theme_id'],[fk('post_id','afnc_item','post_id'),fk('theme_id','theme','theme_id')]),('fotn_score',f,['iso3','data_year'],[fk('iso3','country','iso3')]),('country_group',groups,['iso3','group_name'],[fk('iso3','country','iso3')]),('thai_data_dictionary',dictionary,['sheet','column'],[])]
    tmp=out.with_suffix('.building.db');tmp.unlink(missing_ok=True)
    with sqlite3.connect(tmp) as conn:
        conn.execute('PRAGMA foreign_keys=ON')
        for name,frame,pk,fks in tables:write_table(conn,name,frame,pk,fks)
        for table,cols in [('afnc_item','year,month,category_th'),('aiid_incident','year,month,is_deepfake'),('eu_debunk','year,month'),('eu_article','debunk_id'),('fotn_score','data_year,total_score'),('acsc_week','month,flag_type'),('afnc_theme','theme_id'),('eu_debunk_theme','theme_id')]:
            conn.execute(f'CREATE INDEX idx_{table}_filter ON {table}({cols})')
        assert not conn.execute('PRAGMA foreign_key_check').fetchall()
        assert conn.execute('PRAGMA integrity_check').fetchone()[0]=='ok'
    tmp.replace(out)
    processed=out.parent/'processed';processed.mkdir(exist_ok=True)
    for name,frame,_,_ in tables:frame.to_csv(processed/f'{name}.csv',index=False,encoding='utf-8-sig')
    manifest={'rule_version':RULE_VERSION,'sources':sources,'sheets':{FILES[0]:pd.ExcelFile(src/FILES[0]).sheet_names,FILES[3]:book.sheet_names},'before':before,'after':{name:profile(frame,pk) for name,frame,pk,_ in tables},'coverage':{name:{col:{'min':str(frame[col].min()),'max':str(frame[col].max())} for col in ['date','debunk_date','week_start','data_year'] if col in frame} for name,frame,_,_ in tables},'content_length':{'min':int(a.content_500.str.len().min()),'median':float(a.content_500.str.len().median()),'max':int(a.content_500.str.len().max())},'acsc_mapping':c[['week_start','week_end','panel_week_start','days','source_url']].to_dict('records'),'duration_seconds':round(time.perf_counter()-started,3),'notes':['No source file modified','AI rules are project-defined indicators; all matches need review','NULL means no report, not zero','ACSC month uses source week_start; 8-day interval not split','full AFNC CSV used' if full.exists() else 'Excel AFNC content truncated; AI counts are minimum']}
    (out.parent/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2))
    print(json.dumps({'database':str(out),'seconds':manifest['duration_seconds'],'rows':{n:len(df) for n,df,_,_ in tables}},ensure_ascii=False))
    return manifest
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--input',type=Path,default=ROOT/'Datasets');p.add_argument('--output',type=Path,default=ROOT/'data/adidur.db');args=p.parse_args()
    try:build(args.input,args.output)
    except (KeyError,ValueError,FileNotFoundError) as e:p.exit(1,f'Data preparation failed: {e}\n')
