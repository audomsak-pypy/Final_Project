"""Real Chromium smoke test, console capture, viewport screenshots and interactions."""
from pathlib import Path
import json,os,sys,time
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from playwright.sync_api import sync_playwright
from app.state import defaults,encode
OUT=Path(__file__).resolve().parents[1]/'tests/artifacts';OUT.mkdir(parents=True,exist_ok=True)
results=[];errors=[]
def record(name,ok,detail=''):results.append(dict(test=name,status='PASS' if ok else 'FAIL',detail=detail))
with sync_playwright() as p:
    browser=p.chromium.launch(executable_path=os.environ.get('CHROMIUM_PATH','/usr/bin/chromium'),headless=True,args=['--no-sandbox'])
    for width in (360,768,1280):
        for mode in ('light','dark'):
            page=browser.new_page(viewport={'width':width,'height':900},color_scheme=mode)
            page.on('pageerror',lambda e:errors.append(str(e)))
            page.on('console',lambda m:errors.append({'message':m.text,'url':page.url}) if m.type=='error' else None)
            for tab in ('0','1'):
                start=time.perf_counter();page.goto('http://127.0.0.1:8050/'+encode(tab,defaults()));page.locator('h1').wait_for();page.wait_for_timeout(1000)
                if tab=='1':page.locator('.js-plotly-plot').first.wait_for()
                overflow=page.evaluate('document.documentElement.scrollWidth>window.innerWidth')
                record(f'viewport-{width}-{mode}-tab{tab}',not overflow,{'seconds':round(time.perf_counter()-start,3),'graphs':page.locator('.js-plotly-plot').count()})
                page.screenshot(path=str(OUT/f'{width}-{mode}-tab{tab}.png'),full_page=True)
            page.close()
    page=browser.new_page(viewport={'width':1280,'height':900})
    page.on('pageerror',lambda e:errors.append(str(e)))
    page.on('console',lambda m:errors.append({'message':m.text,'url':page.url}) if m.type=='error' else None)
    for tab,count in [('1',3),('2',5),('3',4),('4',0)]:
        page.goto('http://127.0.0.1:8050/'+encode(tab,defaults()));page.locator('h1').wait_for();page.wait_for_timeout(900)
        record('tab-'+tab,page.locator('.js-plotly-plot').count()==count,{'graphs':page.locator('.js-plotly-plot').count(),'overflow':page.evaluate('document.documentElement.scrollWidth>window.innerWidth')})
        page.screenshot(path=str(OUT/f'1280-light-tab{tab}-all.png'),full_page=True)
    page.goto('http://127.0.0.1:8050/?tab=1');page.locator('.js-plotly-plot').first.wait_for();page.wait_for_timeout(700)
    # Actual SVG point click, then drill up; state assertion through URL.
    points=page.locator('.js-plotly-plot').first.locator('.scatterlayer .trace').first.locator('.point')
    points.last.click(force=True);page.wait_for_timeout(700)
    from app.state import decode
    s=decode('?'+page.url.split('?',1)[1])[1]['1'];record('year-drill',s['year'] is not None,s)
    if s['year']:
        page.locator('.js-plotly-plot').first.locator('.scatterlayer .trace').first.locator('.point').first.click(force=True);page.wait_for_timeout(500)
        s=decode('?'+page.url.split('?',1)[1])[1]['1'];record('month-drill',s['month'] is not None,s)
    page.get_by_role('button',name='ย้อนระดับ',exact=True).click();page.wait_for_timeout(500)
    before=page.url;page.get_by_role('button',name='เสรีภาพอินเทอร์เน็ต',exact=True).click();page.wait_for_timeout(700)
    page.get_by_role('button',name='AI และภัยออนไลน์',exact=True).click();page.wait_for_timeout(700)
    record('tab-state-retained',decode('?'+page.url.split('?',1)[1])[1]['1']==decode('?'+before.split('?',1)[1])[1]['1'])
    page.reload();page.locator('h1').wait_for();page.wait_for_timeout(500);record('reload-state',decode('?'+page.url.split('?',1)[1])[1]['1']==decode('?'+before.split('?',1)[1])[1]['1'])
    page.go_back();page.wait_for_timeout(500);page.go_forward();page.wait_for_timeout(500);record('history',page.locator('h1').count()==1)
    with page.expect_download() as dl:page.get_by_role('link',name='ดาวน์โหลดผลตามตัวกรอง CSV',exact=True).click()
    download=dl.value;download.save_as(str(OUT/'browser-filtered.csv'));record('browser-download',Path(download.path()).read_bytes().startswith(b'\xef\xbb\xbf'),download.suggested_filename)
    page.get_by_role('button',name='ล้างตัวกรอง',exact=True).click();page.wait_for_timeout(500);record('reset',decode('?'+page.url.split('?',1)[1])[1]['1']==defaults()['1'])
    browser.close()
record('console-errors',not errors,errors)
(OUT/'browser-results.json').write_text(json.dumps({'results':results,'console_errors':errors},ensure_ascii=False,indent=2))
for r in results:print(r['test'],r['status'])
sys.exit(int(any(r['status']=='FAIL' for r in results)))
