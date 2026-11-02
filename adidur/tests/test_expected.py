"""test_expected.py — pytest เทียบผลลัพธ์คิวรีกับค่าคาดหวังใน 03 ข้อ 4"""
import os
import sqlite3
import pandas as pd
import pytest

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "adidur.db")

@pytest.fixture(scope="module")
def con():
    assert os.path.exists(DB_PATH), f"Database not found at {DB_PATH}"
    connection = sqlite3.connect(DB_PATH)
    yield connection
    connection.close()

def test_e01_afnc_verdicts(con):
    # E01 ปี 2020 = (Fake 711, Distorted 167, True 181) และรวมทั้งหมด 9,520 / 1,435 / 3,503
    sql_2020 = """
    SELECT SUM(verdict_en='Fake') AS fake, SUM(verdict_en='Distorted') AS distorted,
           SUM(verdict_en='True') AS true_
    FROM afnc_item WHERE item_type='Verdict' AND year=2020
    """
    row_2020 = con.execute(sql_2020).fetchone()
    assert row_2020 == (711, 167, 181)

    sql_total = """
    SELECT SUM(verdict_en='Fake') AS fake, SUM(verdict_en='Distorted') AS distorted,
           SUM(verdict_en='True') AS true_
    FROM afnc_item WHERE item_type='Verdict'
    """
    row_total = con.execute(sql_total).fetchone()
    assert row_total == (9520, 1435, 3503)

def test_e02_afnc_ai_matches(con):
    # E02 ข่าว AI รวม 56 (mention 33, media_evidence 23) ปี 2025 = 11, ปี 2026 = 44
    cur = con.cursor()
    cur.execute("SELECT COUNT(*), SUM(ai_level='mention'), SUM(ai_level='media_evidence') FROM afnc_ai_match")
    total, mention, media = cur.fetchone()
    assert total == 56
    assert mention == 33
    assert media == 23

    cur.execute("""
    SELECT a.year, COUNT(*) FROM afnc_ai_match m JOIN afnc_item a USING(post_id)
    WHERE a.year IN (2025, 2026) GROUP BY a.year ORDER BY a.year
    """)
    rows = dict(cur.fetchall())
    assert rows.get(2025) == 11
    assert rows.get(2026) == 44

def test_e04_aiid_deepfake(con):
    # E04 Deepfake ปี 2024 = 140, ปี 2025 = 235 และรวมทั้งฐาน 588
    cur = con.cursor()
    cur.execute("SELECT SUM(is_deepfake) FROM aiid_incident WHERE year=2024")
    assert cur.fetchone()[0] == 140

    cur.execute("SELECT SUM(is_deepfake) FROM aiid_incident WHERE year=2025")
    assert cur.fetchone()[0] == 235

    cur.execute("SELECT SUM(is_deepfake) FROM aiid_incident")
    assert cur.fetchone()[0] == 588

def test_e06_acsc_totals(con):
    # E06 ACSC รวม 381,390 คดี 18,177,373,771 บาท / ไม่รวม suspect 302,079 คดี 15,402,373,771 บาท
    # บาทต่อคดี 47,660.86 และ 50,987.90
    cur = con.cursor()
    cur.execute("""
    SELECT SUM(cases), SUM(loss_baht), ROUND(1.0*SUM(loss_baht)/SUM(cases), 2)
    FROM acsc_week WHERE cases IS NOT NULL AND loss_baht IS NOT NULL
    """)
    cases_all, loss_all, lpc_all = cur.fetchone()
    assert cases_all == 381390
    assert loss_all == 18177373771
    assert lpc_all == 47660.86

    cur.execute("""
    SELECT SUM(cases), SUM(loss_baht), ROUND(1.0*SUM(loss_baht)/SUM(cases), 2)
    FROM acsc_week WHERE cases IS NOT NULL AND loss_baht IS NOT NULL AND COALESCE(flag_type,'')<>'suspect'
    """)
    cases_nosus, loss_nosus, lpc_nosus = cur.fetchone()
    assert cases_nosus == 302079
    assert loss_nosus == 15402373771
    assert lpc_nosus == 50987.90

def test_e08_acsc_gaps(con):
    # E08 สัปดาห์ขาด 3 สัปดาห์: 2026-06-14, 2026-07-26, 2026-10-25
    cur = con.cursor()
    cur.execute("""
    SELECT w.week_start FROM weekly_panel w
    WHERE w.week_start >= '2025-11-09' AND (w.acsc_reported = 0 OR w.acsc_reported IS NULL)
    ORDER BY w.week_start
    """)
    gaps = [r[0] for r in cur.fetchall()]
    assert gaps == ['2026-06-14', '2026-07-26', '2026-10-25']

def test_e10_eu_debunks(con):
    # E10 การหักล้างรวม 8,522 บทความรวม 18,249 ปี 2020 = 2,006 การหักล้าง / 4,720 บทความ
    cur = con.cursor()
    cur.execute("SELECT COUNT(DISTINCT debunk_id), SUM(n_articles) FROM eu_debunk")
    debunks_tot, articles_tot = cur.fetchone()
    assert debunks_tot == 8522
    assert articles_tot == 18249

    cur.execute("SELECT COUNT(DISTINCT debunk_id), SUM(n_articles) FROM eu_debunk WHERE year=2020")
    debunks_2020, articles_2020 = cur.fetchone()
    assert debunks_2020 == 2006
    assert articles_2020 == 4720

def test_e12_fotn_asean_2024(con):
    # E12 อาเซียนปีข้อมูล 2024: ไทย 39 คะแนน อันดับ 6 จาก 8
    cur = con.cursor()
    cur.execute("""
    SELECT f.iso3, f.total_score, RANK() OVER (ORDER BY f.total_score DESC) AS rnk
    FROM fotn_score f JOIN country_group g ON g.iso3=f.iso3 AND g.group_name='ASEAN'
    WHERE f.data_year=2024 ORDER BY f.total_score DESC
    """)
    rows = cur.fetchall()
    assert len(rows) == 8
    tha_entry = [r for r in rows if r[0] == 'THA'][0]
    assert tha_entry[1] == 39
    assert tha_entry[2] == 6

def test_e15_theme_denominators_and_covid(con):
    # E15 ตัวหาร 2020–2022: EU 4,820, AFNC 3,556 และโควิด-19 EU 629 / AFNC 657
    cur = con.cursor()
    cur.execute("SELECT COUNT(*) FROM eu_debunk WHERE year BETWEEN 2020 AND 2022")
    eu_den = cur.fetchone()[0]
    assert eu_den == 4820

    cur.execute("""
    SELECT COUNT(*) FROM afnc_item
    WHERE item_type='Verdict' AND verdict_en IN ('Fake','Distorted') AND year BETWEEN 2020 AND 2022
    """)
    af_den = cur.fetchone()[0]
    assert af_den == 3556

    cur.execute("""
    SELECT COUNT(DISTINCT t.debunk_id) FROM eu_debunk_theme t JOIN eu_debunk d USING(debunk_id)
    WHERE d.year BETWEEN 2020 AND 2022 AND t.theme_id='covid'
    """)
    eu_covid = cur.fetchone()[0]
    assert eu_covid == 629

    cur.execute("""
    SELECT COUNT(DISTINCT t.post_id) FROM afnc_theme t JOIN afnc_item a USING(post_id)
    WHERE a.year BETWEEN 2020 AND 2022 AND t.theme_id='covid'
    """)
    af_covid = cur.fetchone()[0]
    assert af_covid == 657

def test_e19_views_extremes(con):
    # E19 ข่าว AI ยอดเข้าชมสูงสุด post_id 10098 (4,818) และต่ำสุด 93299 (32)
    cur = con.cursor()
    cur.execute("""
    SELECT a.post_id, a.view_count FROM afnc_ai_match m JOIN afnc_item a USING(post_id)
    ORDER BY a.view_count DESC, a.post_id LIMIT 1
    """)
    top_post, top_view = cur.fetchone()
    assert top_post == 10098
    assert top_view == 4818

    cur.execute("""
    SELECT a.post_id, a.view_count FROM afnc_ai_match m JOIN afnc_item a USING(post_id)
    ORDER BY a.view_count ASC, a.post_id LIMIT 1
    """)
    low_post, low_view = cur.fetchone()
    assert low_post == 93299
    assert low_view == 32
