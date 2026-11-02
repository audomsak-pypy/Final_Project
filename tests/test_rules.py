import copy,hashlib,json,sqlite3
from pathlib import Path
import pandas as pd
import pytest
from app import queries as q
from app.state import defaults,encode,decode,up,sanitize,be
from scripts.rules import match_ai

def test_ai_filters_are_scoped():
    s=defaults()['1'];baseline=q.totals(q.acsc(s));baseid=q.aiid(s).incident_id.tolist()
    for category in ['ผลิตภัณฑ์สุขภาพ','ไม่มีหมวดนี้',"' OR 1=1 --"]:
        other={**s,'category':category,'levels':['media_evidence'],'imp':1}
        assert q.totals(q.acsc(other))==baseline
        assert q.aiid(other).incident_id.tolist()==baseid

def test_country_scope_and_rank():
    s=defaults()['3'];base=q.thai_context().to_dict('records');thai=q.thai_score(s).to_dict('records')
    for iso in ['RUS','PHL','ZZZ']:
        assert q.thai_context().to_dict('records')==base
        assert q.thai_score({**s,'iso3':iso}).to_dict('records')==thai
    r=q.rank({**s,'groups':['ALL','ASEAN'],'add_rus':True});assert len(r)==r.iso3.nunique()==71
    r=q.rank({**s,'groups':['ASEAN'],'add_rus':True});assert len(r)==9

def test_acsc_null_suspect_and_eight_day():
    s=defaults()['1'];p=q.acsc_panel(s)
    assert len(p)==51 and p.cases.notna().sum()==48 and p.cases.isna().sum()==3
    assert not (p.cases==0).any()
    excluded=q.acsc_panel({**s,'inc_suspect':False})
    assert excluded.cases.isna().sum()==4
    assert int(p.cases.sum())==q.totals(q.acsc(s))[0]
    assert int(excluded.cases.sum())==q.totals(q.acsc({**s,'inc_suspect':False})) [0]
    eight=p[p.days==8].iloc[0];assert eight.week_start=='2026-05-31' and eight.source_week_start=='2026-05-30'
    assert p.cases.sum()-excluded.cases.sum()==79311
    assert excluded[excluded.flag_type=='note'].cases.notna().all()

def test_acsc_monthly_panel_totals():
    s=defaults()['1']
    for month in ['2026-05','2026-06','2026-08']:
        t={**s,'month':month};assert int(q.acsc_panel(t).cases.sum())==q.totals(q.acsc(t))[0]

def test_empty_coverage_and_zero_denominator():
    s={**defaults()['1'],'y0':2000,'y1':2001};assert q.acsc_panel(s).empty and q.totals(q.acsc(s))==(None,None,None)
    assert q.afnc({**defaults()['1'],'levels':[]}).empty
    assert q.totals(pd.DataFrame([dict(cases=0,loss_baht=0)]))==(0,0,None)

def test_heatmap_denominator_and_distinct():
    s=defaults()['2']
    for source in ['EU','AFNC']:
        baseline=q.theme_shares(s,source)
        for theme in ['covid','finance','ukraine']:
            actual=q.theme_shares({**s,'theme':theme,'afnc_category':'ผลิตภัณฑ์สุขภาพ'},source)
            pd.testing.assert_frame_equal(actual,baseline)
        assert (baseline.n<=baseline.denominator).all()
    assert q.theme_shares({**s,'y0':2024,'y1':2026},'EU').empty

def test_url_roundtrip_and_bad_inputs():
    states=defaults();states['1'].update(year=2026,month='2026-08',category='ภัยพิบัติ',imp=1,inc_suspect=False,detail='ค่าที่แตะ')
    states['2'].update(theme='health');states['3'].update(iso3='RUS',add_rus=True)
    tab,actual=decode(encode('2',states));assert tab=='2';assert actual==sanitize(states)
    assert decode('?tab=99&s=%7Bbad')[0]=='0'
    bad=sanitize({'1':{'levels':"' OR 1=1",'y0':'oops','month':'2026-99'},'3':{'iso3':'../../../etc'}})
    assert bad['1']['month'] is None and bad['3']['iso3'] is None
    assert decode('?tab=1&year=2025&levels=mention')[1]['1']['year']==2025

def test_up_preserves_unrelated_filters():
    s={**defaults()['1'],'year':2026,'month':'2026-08','category':'ภัยพิบัติ','level':'items'}
    a=up('1',s);assert a['month'] is None and a['year']==2026 and a['category']==s['category']
    b=up('1',a);assert b['year'] is None and b['category']==s['category']
    s={**defaults()['3'],'iso3':'THA','level':'year'};assert up('3',s)['level']=='country'
    assert up('3',up('3',s))['iso3'] is None

@pytest.mark.parametrize('text',['Thailand','AIS','เอไอเอส','said','https://some.site/AI','<AI>'])
def test_false_ai(text):assert match_ai(text) is None
@pytest.mark.parametrize('text',['AI','ปัญญาประดิษฐ์','ภาพ AI','สร้างด้วย AI','deepfake','ChatGPT'])
def test_positive_ai(text):
    result=match_ai(text);assert result and result['evidence_snippet'] and result['matched_terms'];assert result['review_status']=='ต้องตรวจสอบ'

@pytest.mark.parametrize('n',range(5))
def test_small_news_and_ties(n):
    frame=pd.DataFrame([dict(post_id=i,view_count=100) for i in range(n)],columns=['post_id','view_count'])
    top,low=q.news_selection(frame);ids=top.post_id.tolist()+low.post_id.tolist()
    assert len(set(ids))==len(ids)==n
    assert top.post_id.tolist()==list(range(min(n,3)))

def test_foreign_keys_and_sources():
    manifest=json.loads((q.ROOT/'data/manifest.json').read_text())
    for f in manifest['sources']:assert hashlib.sha256((q.ROOT/'Datasets'/f['file']).read_bytes()).hexdigest()==f['sha256']
    with sqlite3.connect(q.DB) as c:
        c.execute('PRAGMA foreign_keys=ON');assert c.execute('PRAGMA foreign_key_check').fetchall()==[]
        assert c.execute('PRAGMA integrity_check').fetchone()[0]=='ok'
        with pytest.raises(sqlite3.IntegrityError):c.execute("INSERT INTO afnc_ai_match(post_id) VALUES(-100)")

def test_bom_and_all_filtered_rows():
    from app.app import server
    client=server.test_client();states=defaults()
    for tab in ['1','2','3']:
        states[tab]['page']=4;res=client.get('/download/filtered/'+tab+'.csv'+encode(tab,states))
        assert res.status_code==200 and res.data.startswith(b'\xef\xbb\xbf')
        import io
        frame=pd.read_csv(io.BytesIO(res.data));assert len(frame)==len(q.evidence(tab,states[tab]))
    assert client.get('/download/processed/not_a_table.csv').status_code==404
    assert client.get('/download/raw/requirements.txt').status_code==404
    for name in __import__('scripts.build_db',fromlist=['FILES']).FILES:
        res=client.get('/download/raw/'+name)
        assert hashlib.sha256(res.data).hexdigest()==hashlib.sha256((q.ROOT/'Datasets'/name).read_bytes()).hexdigest()

def test_page_render_and_health():
    from app.app import render,server
    assert server.test_client().get('/health').json['afnc_rows']==17726
    for tab in '01234':assert render(encode(tab,defaults()),False)[0] is not None
