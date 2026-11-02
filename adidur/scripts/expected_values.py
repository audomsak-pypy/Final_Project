"""expected_values.py — คำนวณค่าคาดหวัง (test) จาก adidur.db ด้วย SQL ชุดเดียวกับที่แดชบอร์ดใช้"""
import sqlite3, sys
import pandas as pd
pd.set_option("display.width", 220); pd.set_option("display.max_colwidth", 90)
con = sqlite3.connect(sys.argv[1] if len(sys.argv) > 1 else "adidur.db")
Q = {}
Q["E01_afnc_verdict_by_year"] = """
SELECT year, SUM(verdict_en='Fake') AS fake, SUM(verdict_en='Distorted') AS distorted,
       SUM(verdict_en='True') AS true_, COUNT(*) AS verdicts
FROM afnc_item WHERE item_type='Verdict' GROUP BY year ORDER BY year"""
Q["E02_afnc_ai_by_year"] = """
SELECT a.year, SUM(m.ai_level='mention') AS mention, SUM(m.ai_level='media_evidence') AS media_evidence,
       COUNT(*) AS ai_total, SUM(m.impersonation_flag) AS impersonation
FROM afnc_ai_match m JOIN afnc_item a USING(post_id) GROUP BY a.year ORDER BY a.year"""
Q["E03_afnc_ai_by_category"] = """
SELECT a.category_th, COUNT(*) AS n FROM afnc_ai_match m JOIN afnc_item a USING(post_id)
GROUP BY a.category_th ORDER BY n DESC"""
Q["E04_aiid_by_year"] = """
SELECT year, COUNT(*) AS incidents, SUM(is_deepfake) AS deepfake, SUM(is_misinfo) AS misinformation
FROM aiid_incident WHERE year >= 2015 GROUP BY year ORDER BY year"""
Q["E05_aiid_totals"] = """
SELECT COUNT(*) AS incidents, COUNT(DISTINCT incident_id) AS uniq_id, SUM(is_deepfake) AS deepfake,
       SUM(is_misinfo) AS misinformation, MIN(date) AS min_date, MAX(date) AS max_date,
       SUM(year IS NULL) AS no_date FROM aiid_incident"""
Q["E06_acsc_totals"] = """
SELECT 'รวมทุกสัปดาห์ที่มีข้อมูล' AS scope, COUNT(*) AS weeks, SUM(cases) AS cases, SUM(loss_baht) AS loss_baht,
       ROUND(1.0*SUM(loss_baht)/SUM(cases),2) AS loss_per_case
FROM acsc_week WHERE cases IS NOT NULL AND loss_baht IS NOT NULL
UNION ALL
SELECT 'ไม่รวมสัปดาห์ที่ตัวเลขน่าสงสัย (suspect)', COUNT(*), SUM(cases), SUM(loss_baht), ROUND(1.0*SUM(loss_baht)/SUM(cases),2)
FROM acsc_week WHERE cases IS NOT NULL AND loss_baht IS NOT NULL AND COALESCE(flag_type,'')<>'suspect'"""
Q["E07_acsc_by_month_excl_suspect"] = """
SELECT month, COUNT(*) AS weeks, SUM(cases) AS cases, SUM(loss_baht) AS loss_baht,
       ROUND(1.0*SUM(loss_baht)/SUM(cases),0) AS loss_per_case
FROM acsc_week WHERE COALESCE(flag_type,'')<>'suspect' GROUP BY month ORDER BY month"""
Q["E08_acsc_gaps"] = """
SELECT w.week_start, w.week_end FROM weekly_panel w
WHERE w.week_start >= '2025-11-09' AND (w.acsc_reported = 0 OR w.acsc_reported IS NULL)"""
Q["E09_acsc_flag_precision"] = """
SELECT week_start, cases, loss_baht, loss_precision, days, flag_type, substr(flag,1,60) AS flag FROM acsc_week
WHERE is_flagged=1 OR days<>7 OR week_start IN ('2026-08-09')"""
Q["E10_eu_by_year"] = """
SELECT d.year, COUNT(DISTINCT d.debunk_id) AS debunks, SUM(d.n_articles) AS articles,
       SUM(d.keywords IS NULL) AS debunks_no_keyword
FROM eu_debunk d GROUP BY d.year ORDER BY d.year"""
Q["E11_eu_class"] = """SELECT class, COUNT(*) AS articles FROM eu_article GROUP BY class"""
Q["E12_fotn_asean_2024"] = """
SELECT f.iso3, f.country_th, f.total_score, f.obstacles_to_access, f.limits_on_content,
       f.violations_of_user_rights, f.status_th, f.report_edition,
       RANK() OVER (ORDER BY f.total_score DESC) AS rank_in_asean
FROM fotn_score f JOIN country_group g ON g.iso3=f.iso3 AND g.group_name='ASEAN'
WHERE f.data_year=2024 ORDER BY f.total_score DESC"""
Q["E13_fotn_tha_rank_all_2024"] = """
SELECT * FROM (SELECT iso3, total_score, RANK() OVER (ORDER BY total_score DESC) AS rnk,
       COUNT(*) OVER () AS n_countries FROM fotn_score WHERE data_year=2024) WHERE iso3 IN ('THA','RUS')"""
Q["E14_tha_fotn_vs_afnc"] = """
SELECT f.data_year, f.report_edition, f.total_score, f.limits_on_content, f.status_th,
  (SELECT COUNT(*) FROM afnc_item a WHERE a.item_type='Verdict' AND a.year=f.data_year) AS afnc_verdicts
FROM fotn_score f WHERE f.iso3='THA' AND f.data_year BETWEEN 2019 AND 2024 ORDER BY f.data_year"""
Q["E15_theme_share_2020_2022"] = """
WITH eu_den AS (SELECT COUNT(*) n FROM eu_debunk WHERE year BETWEEN 2020 AND 2022),
af_den AS (SELECT COUNT(*) n FROM afnc_item WHERE item_type='Verdict' AND verdict_en IN ('Fake','Distorted')
           AND year BETWEEN 2020 AND 2022),
eu AS (SELECT t.theme_id, COUNT(DISTINCT t.debunk_id) n FROM eu_debunk_theme t JOIN eu_debunk d USING(debunk_id)
       WHERE d.year BETWEEN 2020 AND 2022 GROUP BY t.theme_id),
af AS (SELECT t.theme_id, COUNT(DISTINCT t.post_id) n FROM afnc_theme t JOIN afnc_item a USING(post_id)
       WHERE a.year BETWEEN 2020 AND 2022 GROUP BY t.theme_id)
SELECT th.theme_th, COALESCE(eu.n,0) AS eu_debunks, ROUND(100.0*COALESCE(eu.n,0)/(SELECT n FROM eu_den),1) AS eu_pct,
       COALESCE(af.n,0) AS afnc_false, ROUND(100.0*COALESCE(af.n,0)/(SELECT n FROM af_den),1) AS afnc_pct
FROM theme th LEFT JOIN eu USING(theme_id) LEFT JOIN af USING(theme_id)"""
Q["E16_theme_denominators_2020_2022"] = """
SELECT (SELECT COUNT(*) FROM eu_debunk WHERE year BETWEEN 2020 AND 2022) AS eu_debunks,
       (SELECT COUNT(*) FROM afnc_item WHERE item_type='Verdict' AND verdict_en IN ('Fake','Distorted')
        AND year BETWEEN 2020 AND 2022) AS afnc_false_verdicts"""
Q["E17_theme_by_year"] = """
SELECT d.year, t.theme_id, COUNT(DISTINCT t.debunk_id) AS eu_n FROM eu_debunk_theme t JOIN eu_debunk d USING(debunk_id)
WHERE t.theme_id IN ('covid','ukraine') GROUP BY 1,2 ORDER BY 2,1"""
Q["E18_afnc_theme_by_year"] = """
SELECT a.year, t.theme_id, COUNT(DISTINCT t.post_id) AS afnc_n FROM afnc_theme t JOIN afnc_item a USING(post_id)
WHERE t.theme_id IN ('covid','ukraine','other_conflict') GROUP BY 1,2 ORDER BY 2,1"""
Q["E19_top_views_ai_all"] = """
SELECT a.post_id, a.date, a.view_count, a.category_th, a.title, a.url FROM afnc_ai_match m JOIN afnc_item a USING(post_id)
ORDER BY a.view_count DESC, a.post_id LIMIT 3"""
Q["E20_lowest_view_ai_all"] = """
SELECT a.post_id, a.date, a.view_count, a.title FROM afnc_ai_match m JOIN afnc_item a USING(post_id)
ORDER BY a.view_count ASC, a.post_id LIMIT 1"""
Q["E21_top_views_ai_2025"] = """
SELECT a.post_id, a.date, a.view_count, a.title FROM afnc_ai_match m JOIN afnc_item a USING(post_id)
WHERE a.year=2025 ORDER BY a.view_count DESC, a.post_id LIMIT 3"""
Q["E22_ytd_2026_vs_2025"] = """
SELECT 'AFNC ข่าวเท็จ (ปลอม+บิดเบือน) ม.ค.–ต.ค.' AS metric,
  SUM(year=2025) AS y2025, SUM(year=2026) AS y2026
FROM afnc_item WHERE item_type='Verdict' AND verdict_en IN ('Fake','Distorted') AND substr(date,6,5) <= '10-31'
UNION ALL
SELECT 'AFNC ข่าวที่เกี่ยวกับ AI ม.ค.–ต.ค.', SUM(a.year=2025), SUM(a.year=2026)
FROM afnc_ai_match m JOIN afnc_item a USING(post_id) WHERE substr(a.date,6,5) <= '10-31'
UNION ALL
SELECT 'AIID เหตุการณ์ Deepfake 1 ม.ค.–26 ต.ค.', SUM(year=2025 AND is_deepfake=1), SUM(year=2026 AND is_deepfake=1)
FROM aiid_incident WHERE substr(date,6,5) <= '10-26'"""
Q["E23_weekly_panel_check"] = """
SELECT (SELECT SUM(afnc_fake) FROM weekly_panel) AS panel_fake,
       (SELECT COUNT(*) FROM afnc_item WHERE item_type='Verdict' AND verdict_en='Fake') AS items_fake,
       (SELECT SUM(afnc_verdicts) FROM weekly_panel) AS panel_verdicts,
       (SELECT COUNT(*) FROM afnc_item WHERE item_type='Verdict') AS items_verdicts,
       (SELECT SUM(acsc_cases) FROM weekly_panel) AS panel_cases,
       (SELECT SUM(cases) FROM acsc_week) AS acsc_cases"""
Q["E24_afnc_basic"] = """
SELECT COUNT(*) AS rows_, COUNT(DISTINCT post_id) AS uniq_post, MIN(date) AS first_date, MAX(date) AS last_date,
  SUM(item_type='Verdict') AS verdicts, SUM(item_type='Verdict' AND verdict_en IS NULL) AS verdict_missing,
  SUM(checked_by_agency IS NULL) AS agency_missing, MIN(view_count) AS min_view, MAX(view_count) AS max_view
FROM afnc_item"""
if __name__ == "__main__":
    for k, sql in Q.items():
        print(f"\n### {k}")
        print(pd.read_sql(sql, con).to_string(index=False))
