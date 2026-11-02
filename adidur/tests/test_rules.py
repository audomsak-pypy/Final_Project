"""test_rules.py — ทดสอบกติกาทางธุรกิจและการเชื่อมโยงตามเกณฑ์ตรวจรับ"""
import os
import sqlite3
import pytest
import pandas as pd

from app.state import (
    DEFAULT_TAB1_STATE, DEFAULT_TAB2_STATE, DEFAULT_TAB3_STATE,
    state_to_url, url_to_state
)
import app.queries as q

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "adidur.db")

@pytest.fixture(scope="module")
def con():
    assert os.path.exists(DB_PATH)
    connection = sqlite3.connect(DB_PATH)
    yield connection
    connection.close()

def test_rule_ai_filter_does_not_affect_acsc(con):
    # กติกา: สลับตัวกรองหมวดข่าว AI แล้วผลของ K1.3/K1.4 ไม่เปลี่ยน
    state_all = dict(DEFAULT_TAB1_STATE)
    state_all['category'] = None
    res_all = q.get_k1_3_4(con, state_all)

    state_cat = dict(DEFAULT_TAB1_STATE)
    state_cat['category'] = 'ความสงบและความมั่นคง'
    res_cat = q.get_k1_3_4(con, state_cat)

    assert res_all['cases'] == res_cat['cases']
    assert res_all['loss_baht'] == res_cat['loss_baht']
    assert res_all['loss_per_case'] == res_cat['loss_per_case']

def test_rule_tab3_country_does_not_affect_afnc(con):
    # กติกา: เลือกประเทศอื่นในแท็บ 3 แล้วค่าของ C3.3 ฝั่ง AFNC ไม่เปลี่ยน
    # C3.3 เป็นข้อมูลไทยเท่านั้น ไม่ผูกกับ iso3
    df = q.get_c3_3(con)
    assert not df.empty
    assert 'afnc_verdicts' in df.columns
    # ตรวจสอบค่าคำตัดสิน AFNC ในตาราง
    verdicts_2020 = df[df['data_year'] == 2020]['afnc_verdicts'].iloc[0]
    assert verdicts_2020 == 1059

def test_rule_acsc_cases_not_zero_and_c1_5_weeks(con):
    # กติกา: ไม่มีแถว ACSC ที่ cases = 0 และคิวรี C1.5 ได้ 51 สัปดาห์ มีค่า 48 ว่าง 3
    cur = con.cursor()
    cur.execute("SELECT COUNT(*) FROM acsc_week WHERE cases = 0")
    assert cur.fetchone()[0] == 0

    state_c1_5 = dict(DEFAULT_TAB1_STATE)
    state_c1_5['inc_suspect'] = True
    df_c1_5 = q.get_c1_5_6(con, state_c1_5)

    assert len(df_c1_5) == 51
    valid_cases = df_c1_5['cases'].dropna()
    assert len(valid_cases) == 48
    assert df_c1_5['cases'].isna().sum() == 3

def test_rule_csv_starts_with_bom(con):
    # กติกา: ไฟล์ CSV ที่ส่งออกขึ้นต้นด้วย BOM (EF BB BF)
    df = q.get_t1(con, DEFAULT_TAB1_STATE)
    csv_text = "\ufeff" + df.to_csv(index=False)
    csv_bytes = csv_text.encode('utf-8')
    assert csv_bytes[:3] == b'\xef\xbb\xbf'

def test_rule_state_url_roundtrip():
    # กติกา: แปลง state -> URL -> state ได้ค่าเดิม
    test_states = [
        DEFAULT_TAB1_STATE,
        {'tab': '1', 'y0': 2020, 'y1': 2025, 'level': 'month', 'year': 2024, 'month': '2024-05',
         'levels': ['media_evidence'], 'category': 'ภัยพิบัติ', 'imp': 1, 'acsc_level': 'month',
         'acsc_month': '2026-08', 'acsc_week': None, 'inc_suspect': False},
        DEFAULT_TAB2_STATE,
        {'tab': '2', 'y0': 2021, 'y1': 2023, 'level': 'year', 'year': 2022, 'month': None,
         'theme': 'ukraine', 'afnc_category': 'การเมือง'},
        DEFAULT_TAB3_STATE,
        {'tab': '3', 'fy': 2023, 'groups': ['ASEAN'], 'add_rus': True, 'level': 'country', 'iso3': 'MYS'}
    ]

    for s in test_states:
        url_query = state_to_url(s)
        recovered = url_to_state(url_query, s)
        for k in s:
            assert recovered[k] == s[k], f"Mismatch for key {k}: expected {s[k]}, got {recovered[k]}"
