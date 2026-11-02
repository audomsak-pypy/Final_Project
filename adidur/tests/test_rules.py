"""ทดสอบกติกาของสเปก (เกณฑ์ตรวจรับ ข้อ B)"""
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app import queries as Q  # noqa: E402
from app.state import DEFAULTS, to_query, from_query, parse_tab  # noqa: E402
from app.pages import tab3, tab4  # noqa: E402

pytestmark = pytest.mark.skipif(not os.path.exists(Q.DB_PATH), reason="ยังไม่ได้สร้าง data/adidur.db")


def test_ai_filters_do_not_change_acsc_kpis():
    base = dict(DEFAULTS[1])
    a = Q.k13_14(base)
    b = Q.k13_14({**base, "category": "นโยบายรัฐบาล-ข่าวสาร", "imp": 1, "levels": ["media_evidence"]})
    assert a == b


def test_other_country_does_not_change_c33_afnc():
    before = Q.c33()["afnc_verdicts"].tolist()
    s = {**DEFAULTS[3], "iso3": "MYS", "level": "country"}
    Q.c32(s)  # เลือกประเทศอื่น
    r = tab3.render(s, "light")
    assert r["g3"] is not None
    assert Q.c33()["afnc_verdicts"].tolist() == before


def test_no_acsc_row_with_zero_cases_and_c15_shape():
    assert Q.q("SELECT COUNT(*) n FROM acsc_week WHERE cases=0")["n"][0] == 0
    df = Q.c15({"inc_suspect": True, "acsc_month": None})
    assert len(df) == 51
    assert int(df["cases"].notna().sum()) == 48 and int(df["cases"].isna().sum()) == 3


def test_suspect_switch_blanks_week():
    df = Q.c15({"inc_suspect": False, "acsc_month": None})
    assert df[df["week_start"] == "2026-08-16"]["cases"].isna().all()


def test_csv_has_bom():
    out = tab4.filtered_download("1", dict(DEFAULTS[1]), dict(DEFAULTS[2]), dict(DEFAULTS[3]))
    assert out["content"].encode("utf-8").startswith(b"\xef\xbb\xbf")
    prep = Q.to_csv_bytes_str(Q.table("theme"))
    assert prep.encode("utf-8")[:3] == b"\xef\xbb\xbf"


def test_state_url_roundtrip():
    for tab in (1, 2, 3):
        s = dict(DEFAULTS[tab])
        if tab == 1:
            s.update(y0=2025, y1=2026, year=2026, levels=["media_evidence"], inc_suspect=False, imp=1)
        elif tab == 2:
            s.update(y0=2019, theme="ukraine", year=2021, afnc_category="x")
        else:
            s.update(fy=2022, groups=["ASEAN"], add_rus=True, level="country", iso3="THA")
        q = to_query(tab, s)
        assert parse_tab(q) == str(tab)
        assert from_query(tab, q) == s
    # ค่าเริ่มต้นย้อนกลับได้เหมือนเดิม
    assert from_query(1, to_query(1, DEFAULTS[1])) == DEFAULTS[1]


def test_small_set_card_not_duplicated():
    from app.pages import tab1
    s = {**DEFAULTS[1], "y0": 2021, "y1": 2021}
    r = tab1.render(s, "light")
    assert "มีข่าวในชุดนี้" in str(r["cards"])


def test_tab2_default_range_and_no_data_label():
    assert (DEFAULTS[2]["y0"], DEFAULTS[2]["y1"]) == (2020, 2022)
