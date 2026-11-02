"""Reference regressions from document 03. Fail visibly; never rewrite expected data."""
import argparse,json,sqlite3,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def checks(db):
    c=sqlite3.connect(db);c.row_factory=sqlite3.Row
    def rows(sql):return [list(r) for r in c.execute(sql)]
    result=[]
    def check(code,label,expected,sql):
        actual=rows(sql);result.append(dict(code=code,label=label,expected=expected,actual=actual,status='PASS' if actual==expected else 'FAIL'))
    check('E01','AFNC totals',[[1435,9520,3503]],"SELECT SUM(verdict_en='Distorted'),SUM(verdict_en='Fake'),SUM(verdict_en='True') FROM afnc_item WHERE item_type='Verdict'")
    check('E01','AFNC 2020',[[167,711,181]],"SELECT SUM(verdict_en='Distorted'),SUM(verdict_en='Fake'),SUM(verdict_en='True') FROM afnc_item WHERE item_type='Verdict' AND year=2020")
    check('E02','AI total and levels',[[56,33,23]],"SELECT COUNT(*),SUM(ai_level='mention'),SUM(ai_level='media_evidence') FROM afnc_ai_match")
    check('E02','AI years',[[2021,1],[2025,11],[2026,44]],'SELECT year,COUNT(*) FROM afnc_ai_match JOIN afnc_item USING(post_id) GROUP BY year ORDER BY year')
    check('E03','AI categories',[['ความสงบและความมั่นคง',20],['นโยบายรัฐบาล-ข่าวสาร',29],['ผลิตภัณฑ์สุขภาพ',3],['ภัยพิบัติ',3],['อาชญากรรมออนไลน์',1]],'SELECT category_th,COUNT(*) FROM afnc_ai_match JOIN afnc_item USING(post_id) GROUP BY category_th ORDER BY category_th')
    expected=[[2015,24,0,0],[2016,41,0,1],[2017,51,2,2],[2018,46,1,0],[2019,45,2,2],[2020,91,10,5],[2021,80,4,4],[2022,109,11,11],[2023,179,57,35],[2024,311,140,51],[2025,463,235,66],[2026,288,126,18]]
    check('E04','AIID annual',expected,'SELECT year,COUNT(*),SUM(is_deepfake),SUM(is_misinfo) FROM aiid_incident WHERE year>=2015 GROUP BY year ORDER BY year')
    check('E05','AIID base',[[1775,1775,588,196,'1983-09-26','2026-10-22']], 'SELECT COUNT(*),COUNT(DISTINCT incident_id),SUM(is_deepfake),SUM(is_misinfo),MIN(date),MAX(date) FROM aiid_incident')
    check('E06','ACSC all',[[48,381390,18177373771,47660.86]],'SELECT COUNT(*),SUM(cases),SUM(loss_baht),ROUND(1.0*SUM(loss_baht)/SUM(cases),2) FROM acsc_week')
    check('E06','ACSC no suspect',[[47,302079,15402373771,50987.90]],"SELECT COUNT(*),SUM(cases),SUM(loss_baht),ROUND(1.0*SUM(loss_baht)/SUM(cases),2) FROM acsc_week WHERE COALESCE(flag_type,'')<>'suspect'")
    vals=[['2025-11',4,28542,1891164841],['2025-12',4,27048,1559067268],['2026-01',4,28976,1662912487],['2026-02',4,29215,1780347113],['2026-03',5,37222,2251798334],['2026-04',4,25329,1317514358],['2026-05',5,28282,856114577],['2026-06',3,16071,523361290],['2026-07',3,16867,602791316],['2026-08',4,24126,1030302187],['2026-09',4,21885,1038000000],['2026-10',3,18516,889000000]]
    check('E07','ACSC months',vals,"SELECT month,COUNT(*),SUM(cases),SUM(loss_baht) FROM acsc_week WHERE COALESCE(flag_type,'')<>'suspect' GROUP BY month ORDER BY month")
    check('E08','Missing weeks',[['2026-06-14'],['2026-07-26'],['2026-10-25']],"SELECT week_start FROM weekly_panel WHERE week_start>='2025-11-09' AND acsc_cases IS NULL ORDER BY week_start")
    check('E10','EU base',[[8522,18249]],'SELECT COUNT(*),SUM(n_articles) FROM eu_debunk')
    check('E10','EU annual',[[2015,171,204],[2016,446,504],[2017,491,615],[2018,530,880],[2019,1499,2632],[2020,2006,4720],[2021,1920,5273],[2022,894,2193],[2023,565,1228]],'SELECT year,COUNT(*),SUM(n_articles) FROM eu_debunk GROUP BY year ORDER BY year')
    check('E11','EU class',[['disinformation',10682],['trustworthy',7567]],'SELECT class,COUNT(*) FROM eu_article GROUP BY class ORDER BY class')
    check('E12','ASEAN 2024',[['PHL',61,1],['MYS',60,2],['SGP',53,3],['IDN',48,4],['KHM',42,5],['THA',39,6],['VNM',22,7],['MMR',9,8]],"SELECT iso3,total_score,RANK() OVER (ORDER BY total_score DESC) FROM fotn_score f WHERE data_year=2024 AND EXISTS (SELECT 1 FROM country_group g WHERE g.iso3=f.iso3 AND group_name='ASEAN') ORDER BY total_score DESC")
    check('E13','Global ranks',[['RUS',68,71],['THA',51,71]],"SELECT iso3,r,n FROM (SELECT iso3,RANK() OVER (ORDER BY total_score DESC) r,COUNT(*) OVER () n FROM fotn_score WHERE data_year=2024) WHERE iso3 IN ('THA','RUS') ORDER BY iso3")
    check('E14','Thai context',[[2019,2020,35,12,78],[2020,2021,36,13,1059],[2021,2022,39,14,1367],[2022,2023,39,14,2201],[2023,2024,39,14,2496],[2024,2025,39,14,2462]],"SELECT data_year,report_edition,total_score,limits_on_content,(SELECT COUNT(*) FROM afnc_item a WHERE a.item_type='Verdict' AND a.year=f.data_year) FROM fotn_score f WHERE iso3='THA' AND data_year>=2019 ORDER BY data_year")
    check('E15','Theme denominators',[[4820,3556]],"SELECT (SELECT COUNT(*) FROM eu_debunk WHERE year BETWEEN 2020 AND 2022),(SELECT COUNT(*) FROM afnc_item WHERE item_type='Verdict' AND verdict_en IN ('Fake','Distorted') AND year BETWEEN 2020 AND 2022)")
    for code,source,link,key in [('E17','eu_debunk','eu_debunk_theme','debunk_id'),('E18','afnc_item','afnc_theme','post_id')]:
        expected=([['conspiracy',697],['covid',629],['finance',459],['health',417],['other_conflict',864],['politics',903],['ukraine',1671]] if code=='E17' else [['conspiracy',0],['covid',657],['finance',559],['health',1739],['other_conflict',12],['politics',847],['ukraine',1]])
        check(code,'Theme 2020–2022',expected,f'SELECT th.theme_id,COUNT(DISTINCT b.{key}) FROM theme th LEFT JOIN {link} t ON th.theme_id=t.theme_id LEFT JOIN {source} b ON b.{key}=t.{key} AND b.year BETWEEN 2020 AND 2022 GROUP BY th.theme_id ORDER BY th.theme_id')
    check('E19','News high',[[10098,4818]],'SELECT post_id,view_count FROM afnc_ai_match JOIN afnc_item USING(post_id) ORDER BY view_count DESC,post_id LIMIT 1')
    check('E20','News 2–3',[[74172,2200],[75986,750]],'SELECT post_id,view_count FROM afnc_ai_match JOIN afnc_item USING(post_id) ORDER BY view_count DESC,post_id LIMIT 2 OFFSET 1')
    check('E21','News 2025',[[74172,2200],[75986,750],[72687,526]],'SELECT post_id,view_count FROM afnc_ai_match JOIN afnc_item USING(post_id) WHERE year=2025 ORDER BY view_count DESC,post_id LIMIT 3')
    check('E19','News low',[[93299,32]],'SELECT post_id,view_count FROM afnc_ai_match JOIN afnc_item USING(post_id) ORDER BY view_count,post_id LIMIT 1')
    check('E22','Comparable AFNC false',[[2025,1583],[2026,1538]],"SELECT year,COUNT(*) FROM afnc_item WHERE item_type='Verdict' AND verdict_en IN ('Fake','Distorted') AND year IN (2025,2026) AND substr(date,6,5)<='10-31' GROUP BY year ORDER BY year")
    check('E22','Comparable AI',[[2025,8],[2026,44]],"SELECT year,COUNT(*) FROM afnc_ai_match JOIN afnc_item USING(post_id) WHERE year IN (2025,2026) AND substr(date,6,5)<='10-31' GROUP BY year ORDER BY year")
    check('E22','Comparable Deepfake',[[2025,194],[2026,126]],"SELECT year,COUNT(*) FROM aiid_incident WHERE is_deepfake=1 AND year IN (2025,2026) AND substr(date,6,5)<='10-26' GROUP BY year ORDER BY year")
    check('E23','Panel consistency',[[9520,14458,381390]],'SELECT SUM(afnc_fake),SUM(afnc_verdicts),CAST(SUM(acsc_cases) AS INT) FROM weekly_panel')
    check('E24','AFNC base',[[17726,17726,'2019-01-05','2026-10-31',3641,6,595030]],'SELECT COUNT(*),COUNT(DISTINCT post_id),MIN(date),MAX(date),SUM(checked_by_agency IS NULL),MIN(view_count),MAX(view_count) FROM afnc_item')
    c.close();return result
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('database',nargs='?',type=Path,default=ROOT/'data/adidur.db');p.add_argument('--report',type=Path,default=ROOT/'data/expected_results.json');args=p.parse_args();results=checks(args.database)
    args.report.parent.mkdir(parents=True,exist_ok=True);args.report.write_text(json.dumps(results,ensure_ascii=False,indent=2))
    for r in results:print(f'{r["code"]} {r["label"]}: {r["status"]}'+(' expected='+str(r['expected'])+' actual='+str(r['actual']) if r['status']=='FAIL' else ''))
    print(f'{sum(r["status"]=="PASS" for r in results)}/{len(results)} checks passed')
    sys.exit(int(any(r['status']=='FAIL' for r in results)))
