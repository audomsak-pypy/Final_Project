"""เทียบผลคิวรีกับค่าคาดหวังใน 03_DATABASE_SCHEMA.md ข้อ 4"""
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app import queries as Q  # noqa: E402

pytestmark = pytest.mark.skipif(not os.path.exists(Q.DB_PATH), reason="ยังไม่ได้สร้าง data/adidur.db")


def one(sql, p=()):
    return Q.q(sql, p).iloc[0]


def test_e01_afnc_verdicts():
    r = one("SELECT SUM(verdict_en='Fake') f, SUM(verdict_en='Distorted') d, SUM(verdict_en='True') t, COUNT(*) n "
            "FROM afnc_item WHERE item_type='Verdict' AND year=2020")
    assert (r.f, r.d, r.t) == (711, 167, 181)
    r = one("SELECT SUM(verdict_en='Fake') f, SUM(verdict_en='Distorted') d, SUM(verdict_en='True') t, COUNT(*) n "
            "FROM afnc_item WHERE item_type='Verdict'")
    assert (r.f, r.d, r.t, r.n) == (9520, 1435, 3503, 14458)


def test_e02_ai_news():
    r = one("SELECT COUNT(*) n, SUM(ai_level='mention') m, SUM(ai_level='media_evidence') e FROM afnc_ai_match")
    assert (r.n, r.m, r.e) == (56, 33, 23)
    by = Q.q("SELECT a.year, COUNT(*) n FROM afnc_ai_match m JOIN afnc_item a USING(post_id) GROUP BY a.year")
    d = dict(zip(by["year"], by["n"]))
    assert d[2025] == 11 and d[2026] == 44


def test_e04_aiid_deepfake():
    d = Q.q("SELECT year, SUM(is_deepfake) n FROM aiid_incident GROUP BY year")
    d = dict(zip(d["year"], d["n"]))
    assert d[2024] == 140 and d[2025] == 235
    assert one("SELECT SUM(is_deepfake) n FROM aiid_incident").n == 588


def test_e06_acsc_totals():
    s = {"y0": 2025, "y1": 2026, "inc_suspect": True, "year": None, "month": None}
    a = Q.k13_14(s, inc_suspect=True)
    assert (a["cases"], a["loss"]) == (381390, 18177373771)
    assert round(a["per_case"], 2) == 47660.86
    b = Q.k13_14(s, inc_suspect=False)
    assert (b["cases"], b["loss"]) == (302079, 15402373771)
    assert round(b["per_case"], 2) == 50987.90


def test_e08_acsc_gaps():
    df = Q.c15({"inc_suspect": True, "acsc_month": None})
    gaps = df[df["acsc_reported"].fillna(0) == 0]["week_start"].tolist()
    assert gaps == ["2026-06-14", "2026-07-26", "2026-10-25"]


def test_e10_eu():
    assert one("SELECT COUNT(DISTINCT debunk_id) n FROM eu_debunk").n == 8522
    assert one("SELECT COUNT(*) n FROM eu_article").n == 18249
    r = one("SELECT COUNT(*) d, SUM(n_articles) a FROM eu_debunk WHERE year=2020")
    assert (r.d, r.a) == (2006, 4720)


def test_e12_asean_thailand_rank():
    df = Q.c31({"fy": 2024, "groups": ["ASEAN"], "add_rus": False})
    th = df[df["iso3"] == "THA"].iloc[0]
    assert th.total_score == 39 and th.rank_in_group == 6 and th.n_in_group == 8


def test_e15_theme_share():
    eu_den, af_den = Q.denominators(2020, 2022)
    assert sum(eu_den.values()) == 4820 and sum(af_den.values()) == 3556
    eu = Q.c21(2020, 2022).query("theme_id=='covid'")["n"].sum()
    af = Q.c22(2020, 2022).query("theme_id=='covid'")["n"].sum()
    assert (eu, af) == (629, 657)


def test_e19_top_and_lowest_views():
    s = {"y0": 2015, "y1": 2026, "year": None, "month": None, "levels": ["mention", "media_evidence"],
         "category": None, "imp": None}
    top, low, total = Q.c14(s)
    assert total == 56
    assert (int(top.iloc[0]["post_id"]), int(top.iloc[0]["view_count"])) == (10098, 4818)
    assert (int(low.iloc[0]["post_id"]), int(low.iloc[0]["view_count"])) == (93299, 32)
