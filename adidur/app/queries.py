"""SQL ทุกตัวจาก 03_DATABASE_SCHEMA.md เป็นฟังก์ชันรับ state คืน DataFrame (SQL ใช้ ค.ศ.)"""
import os
import sqlite3
from functools import lru_cache
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.environ.get("ADIDUR_DB", os.path.join(ROOT, "data", "adidur.db"))
RAW_DIR = os.path.join(ROOT, "data", "raw")
ACSC_START = "2025-11-09"


def q(sql, params=()):
    con = sqlite3.connect(DB_PATH)
    try:
        return pd.read_sql(sql, con, params=params)
    finally:
        con.close()


def _in(values):
    return ",".join("?" * len(values))


# ---------- แท็บ 1 ----------
def _afnc_where(s, with_month=True):
    w = ["a.year BETWEEN ? AND ?"]
    p = [s["y0"], s["y1"]]
    if s.get("year") is not None:
        w.append("a.year=?"); p.append(s["year"])
    if with_month and s.get("month"):
        w.append("a.month=?"); p.append(s["month"])
    lv = s.get("levels") or []
    w.append(f"m.ai_level IN ({_in(lv)})"); p += lv
    if s.get("category"):
        w.append("a.category_th=?"); p.append(s["category"])
    if s.get("imp") is not None:
        w.append("m.impersonation_flag=?"); p.append(s["imp"])
    return " AND ".join(w), p


def k11(s):
    w, p = ["is_deepfake=1", "year BETWEEN ? AND ?"], [s["y0"], s["y1"]]
    if s.get("year") is not None:
        w.append("year=?"); p.append(s["year"])
    if s.get("month"):
        w.append("month=?"); p.append(s["month"])
    return int(q(f"SELECT COUNT(DISTINCT incident_id) n FROM aiid_incident WHERE {' AND '.join(w)}", p)["n"][0])


def k12(s):
    w, p = _afnc_where(s)
    df = q(f"SELECT m.ai_level, COUNT(DISTINCT a.post_id) n FROM afnc_ai_match m JOIN afnc_item a USING(post_id) "
           f"WHERE {w} GROUP BY m.ai_level", p)
    d = dict(zip(df["ai_level"], df["n"]))
    return {"mention": int(d.get("mention", 0)), "media_evidence": int(d.get("media_evidence", 0))}


def _acsc_where(s, inc_suspect):
    w = ["cases IS NOT NULL", "loss_baht IS NOT NULL",
         "CAST(substr(week_start,1,4) AS INT) BETWEEN ? AND ?"]
    p = [s["y0"], s["y1"]]
    if s.get("year") is not None:
        w.append("substr(week_start,1,4)=?"); p.append(str(s["year"]))
    month = s.get("month")
    if month:
        w.append("month=?"); p.append(month)
    if not inc_suspect:
        w.append("COALESCE(flag_type,'')<>'suspect'")
    return " AND ".join(w), p


def k13_14(s, inc_suspect=None):
    inc = s["inc_suspect"] if inc_suspect is None else inc_suspect
    w, p = _acsc_where(s, inc)
    r = q(f"SELECT COUNT(*) weeks, SUM(cases) cases, SUM(loss_baht) loss, "
          f"1.0*SUM(loss_baht)/SUM(cases) per_case FROM acsc_week WHERE {w}", p).iloc[0]
    return {"weeks": int(r["weeks"]), "cases": None if pd.isna(r["cases"]) else int(r["cases"]),
            "loss": None if pd.isna(r["loss"]) else int(r["loss"]),
            "per_case": None if pd.isna(r["per_case"]) else float(r["per_case"])}


def c11(s):
    if s["level"] == "year":
        return q("SELECT year t, COUNT(*) n FROM aiid_incident WHERE is_deepfake=1 AND year BETWEEN ? AND ? "
                 "GROUP BY year ORDER BY year", (s["y0"], s["y1"]))
    return q("SELECT month t, COUNT(*) n FROM aiid_incident WHERE is_deepfake=1 AND year=? GROUP BY month "
             "ORDER BY month", (s["year"],))


def c12(s):
    p, w = [], []
    if s["level"] == "year":
        w.append("a.year BETWEEN ? AND ?"); p += [s["y0"], s["y1"]]; col = "a.year"
    else:
        w.append("a.year=?"); p.append(s["year"]); col = "a.month"
    if s.get("category"):
        w.append("a.category_th=?"); p.append(s["category"])
    if s.get("imp") is not None:
        w.append("m.impersonation_flag=?"); p.append(s["imp"])
    return q(f"SELECT {col} t, m.ai_level, COUNT(*) n FROM afnc_ai_match m JOIN afnc_item a USING(post_id) "
             f"WHERE {' AND '.join(w)} GROUP BY {col}, m.ai_level", p)


def c13(s):
    w, p = _afnc_where({**s, "category": None})
    return q(f"SELECT a.category_th, COUNT(*) n FROM afnc_ai_match m JOIN afnc_item a USING(post_id) "
             f"WHERE {w} GROUP BY a.category_th ORDER BY n DESC", p)


def c14(s):
    w, p = _afnc_where(s)
    base = ("SELECT a.post_id, a.date, a.title, a.category_th, a.view_count, a.url, m.ai_level, m.evidence_snippet "
            f"FROM afnc_ai_match m JOIN afnc_item a USING(post_id) WHERE {w} ")
    top = q(base + "ORDER BY a.view_count DESC, a.post_id ASC LIMIT 3", p)
    low = q(base + "ORDER BY a.view_count ASC, a.post_id ASC LIMIT 1", p)
    total = q(f"SELECT COUNT(*) n FROM afnc_ai_match m JOIN afnc_item a USING(post_id) WHERE {w}", p)["n"][0]
    return top, low, int(total)


def c15(s):
    """รายสัปดาห์จาก weekly_panel (51 สัปดาห์ ว่าง 3); เลือกเดือนแล้วเหลือเฉพาะสัปดาห์ของเดือนนั้น"""
    p = [ACSC_START]
    month_sql = ""
    if s.get("month"):
        month_sql = " AND substr(w.week_start,1,7)=?"; p.append(s["month"])
    inc = 1 if s["inc_suspect"] else 0
    sql = (f"SELECT w.week_start, w.week_end, "
           f"CASE WHEN {inc}=0 AND w.acsc_flag LIKE 'Suspect%' THEN NULL ELSE w.acsc_cases END AS cases, "
           f"CASE WHEN {inc}=0 AND w.acsc_flag LIKE 'Suspect%' THEN NULL ELSE w.acsc_loss_baht END AS loss_baht, "
           f"w.acsc_loss_precision AS loss_precision, "
           f"CASE WHEN w.acsc_flag IS NULL THEN NULL WHEN w.acsc_flag LIKE 'Suspect%' THEN 'suspect' ELSE 'note' END AS flag_type, "
           f"w.acsc_flag AS flag, w.acsc_reported, w.acsc_source_url AS source_url "
           f"FROM weekly_panel w WHERE w.week_start >= ?{month_sql} ORDER BY w.week_start")
    return q(sql, p)


def c15_month(s):
    """รายเดือนของ ACSC ตามช่วงปี/ปีที่เลือก (ใช้แกนเวลาเดียวกับกราฟอื่น)"""
    w = ["CAST(substr(month,1,4) AS INT) BETWEEN ? AND ?"]
    p = [s.get("y0", 2000), s.get("y1", 2100)]
    if s.get("year") is not None:
        w.append("substr(month,1,4)=?"); p.append(str(s["year"]))
    if not s.get("inc_suspect", True):
        w.append("COALESCE(flag_type,'')<>'suspect'")
    return q(f"SELECT month, COUNT(*) weeks, SUM(cases) cases, SUM(loss_baht) loss_baht, "
             f"1.0*SUM(loss_baht)/SUM(cases) per_case, "
             f"MAX(loss_precision='rounded') any_rounded, MAX(flag_type='suspect') any_suspect "
             f"FROM acsc_week WHERE {' AND '.join(w)} GROUP BY month ORDER BY month", p)


def t1(s):
    w, p = _afnc_where(s)
    sql = ("SELECT 'AFNC' AS source, a.date, a.title, a.category_th AS category, m.ai_level, m.matched_terms AS reason, "
           "m.evidence_snippet, m.review_status, a.url, a.view_count FROM afnc_ai_match m JOIN afnc_item a USING(post_id) "
           f"WHERE {w}")
    w2, p2 = ["is_deepfake=1", "year BETWEEN ? AND ?"], [s["y0"], s["y1"]]
    if s.get("year") is not None:
        w2.append("year=?"); p2.append(s["year"])
    if s.get("month"):
        w2.append("month=?"); p2.append(s["month"])
    sql += (" UNION ALL SELECT 'AIID', date, title, risk_domain, NULL, deepfake_terms, substr(description,1,160), "
            f"NULL, url, NULL FROM aiid_incident WHERE {' AND '.join(w2)} ORDER BY date DESC")
    return q(sql, p + p2)


@lru_cache(maxsize=None)
def ytd_compare():
    return q("""
SELECT 'AFNC ข่าวเท็จ' AS metric, SUM(year=2025) y2025, SUM(year=2026) y2026
FROM afnc_item WHERE item_type='Verdict' AND verdict_en IN ('Fake','Distorted') AND substr(date,6,5) <= '10-31'
UNION ALL SELECT 'AFNC ข่าว AI', SUM(a.year=2025), SUM(a.year=2026)
FROM afnc_ai_match m JOIN afnc_item a USING(post_id) WHERE substr(a.date,6,5) <= '10-31'
UNION ALL SELECT 'AIID Deepfake', SUM(year=2025 AND is_deepfake=1), SUM(year=2026 AND is_deepfake=1)
FROM aiid_incident WHERE substr(date,6,5) <= '10-26'""")


@lru_cache(maxsize=None)
def categories_ai():
    return q("SELECT DISTINCT a.category_th FROM afnc_ai_match m JOIN afnc_item a USING(post_id) ORDER BY 1")["category_th"].tolist()


# ---------- แท็บ 2 ----------
def c21(y0, y1):
    return q("""
WITH den AS (SELECT year, COUNT(*) n FROM eu_debunk WHERE year BETWEEN ? AND ? GROUP BY year)
SELECT d.year, t.theme_id, COUNT(DISTINCT t.debunk_id) AS n, 100.0*COUNT(DISTINCT t.debunk_id)/den.n AS pct
FROM eu_debunk_theme t JOIN eu_debunk d USING(debunk_id) JOIN den USING(year) GROUP BY d.year, t.theme_id""", (y0, y1))


def c22(y0, y1):
    return q("""
WITH den AS (SELECT year, COUNT(*) n FROM afnc_item WHERE item_type='Verdict' AND verdict_en IN ('Fake','Distorted')
             AND year BETWEEN ? AND ? GROUP BY year)
SELECT a.year, t.theme_id, COUNT(DISTINCT t.post_id) AS n, 100.0*COUNT(DISTINCT t.post_id)/den.n AS pct
FROM afnc_theme t JOIN afnc_item a USING(post_id) JOIN den USING(year) GROUP BY a.year, t.theme_id""", (y0, y1))


def denominators(y0, y1):
    eu = q("SELECT year, COUNT(*) n FROM eu_debunk WHERE year BETWEEN ? AND ? GROUP BY year", (y0, y1))
    af = q("SELECT year, COUNT(*) n FROM afnc_item WHERE item_type='Verdict' AND verdict_en IN ('Fake','Distorted') "
           "AND year BETWEEN ? AND ? GROUP BY year", (y0, y1))
    return dict(zip(eu["year"], eu["n"])), dict(zip(af["year"], af["n"]))


def c24(s):
    """ข่าวเท็จ AFNC ของประเด็นที่เลือก แยกตามหมวด (เชื่อมกับ heatmap ผ่าน theme)"""
    col, rng, p = ("a.year", "a.year BETWEEN ? AND ?", [s["y0"], s["y1"]]) if s["level"] == "year" else                   ("a.month", "a.year=?", [s["year"]])
    return q(f"SELECT {col} t, a.category_th, COUNT(DISTINCT a.post_id) n FROM afnc_theme th "
             f"JOIN afnc_item a USING(post_id) WHERE th.theme_id=? AND {rng} GROUP BY {col}, a.category_th",
             [s["theme"]] + p)


def c25(y0, y1):
    return q("SELECT year, COUNT(*) n FROM aiid_incident WHERE is_misinfo=1 AND year BETWEEN ? AND ? GROUP BY year", (y0, y1))


def k2(s):
    y0, y1 = s["y0"], s["y1"]
    yr = (s["year"], s["year"]) if s.get("year") is not None else (y0, y1)
    eu = q("SELECT COUNT(DISTINCT debunk_id) n FROM eu_debunk WHERE year BETWEEN ? AND ?", yr)["n"][0]
    af = q("SELECT COUNT(DISTINCT post_id) n FROM afnc_item WHERE item_type='Verdict' AND verdict_en IN ('Fake','Distorted') "
           "AND year BETWEEN ? AND ?", yr)["n"][0]
    ai = q("SELECT COUNT(DISTINCT incident_id) n FROM aiid_incident WHERE is_misinfo=1 AND year BETWEEN ? AND ?", yr)["n"][0]
    return int(eu), int(af), int(ai)


def t2(s, limit=300):
    p_af, w_af = [s["theme"]], ""
    p_eu, w_eu = [s["theme"]], ""
    if s.get("year") is not None:
        w_af, w_eu = " AND a.year=?", " AND d.year=?"
        p_af.append(s["year"]); p_eu.append(s["year"])
    else:
        w_af, w_eu = " AND a.year BETWEEN ? AND ?", " AND d.year BETWEEN ? AND ?"
        p_af += [s["y0"], s["y1"]]; p_eu += [s["y0"], s["y1"]]
    if s.get("month"):
        w_af += " AND a.month=?"; p_af.append(s["month"])
        w_eu += " AND d.month=?"; p_eu.append(s["month"])
    if s.get("afnc_category"):
        w_af += " AND a.category_th=?"; p_af.append(s["afnc_category"])
    af = q("SELECT 'AFNC' AS source, a.date, a.title AS headline, t.matched_by, t.matched_terms, a.url "
           f"FROM afnc_theme t JOIN afnc_item a USING(post_id) WHERE t.theme_id=?{w_af} ORDER BY a.date DESC", p_af)
    eu = q("SELECT 'EUvsDisinfo' AS source, d.debunk_date AS date, d.keywords AS headline, 'keyword' AS matched_by, "
           "t.matched_terms, l.article_url AS url "
           f"FROM eu_debunk_theme t JOIN eu_debunk d USING(debunk_id) LEFT JOIN eu_debunk_link l USING(debunk_id) "
           f"WHERE t.theme_id=?{w_eu} ORDER BY d.debunk_date DESC", p_eu)
    return af, eu


@lru_cache(maxsize=None)
def themes():
    return q("SELECT * FROM theme")


# ---------- แท็บ 3 ----------
def groups_of(s):
    g = list(s.get("groups") or [])
    if s.get("add_rus"):
        g.append("เปรียบเทียบเพิ่ม")
    return g or ["ASEAN"]


def k3(fy, iso3="THA"):
    return q("SELECT COALESCE(country_th, country) AS name, total_score, status_th, data_year, report_edition "
             "FROM fotn_score WHERE iso3=? AND data_year=?", (iso3, fy))


def c31(s):
    g = groups_of(s)
    return q(f"SELECT f.iso3, COALESCE(f.country_th, f.country) AS name, f.total_score, f.status_th, "
             f"RANK() OVER (ORDER BY f.total_score DESC) AS rank_in_group, COUNT(*) OVER () AS n_in_group "
             f"FROM fotn_score f JOIN country_group g ON g.iso3=f.iso3 AND g.group_name IN ({_in(g)}) "
             f"WHERE f.data_year=? ORDER BY f.total_score DESC", g + [s["fy"]])


def c32(s):
    g = groups_of(s)
    if s["level"] == "group":
        return q(f"SELECT f.iso3, COALESCE(f.country_th, f.country) AS name, f.data_year, f.report_edition, "
                 f"f.obstacles_to_access, f.limits_on_content, f.violations_of_user_rights "
                 f"FROM fotn_score f JOIN country_group g ON g.iso3=f.iso3 AND g.group_name IN ({_in(g)}) "
                 f"WHERE f.data_year=? ORDER BY f.total_score DESC", g + [s["fy"]])
    sql = ("SELECT iso3, COALESCE(country_th, country) AS name, data_year, report_edition, obstacles_to_access, "
           "limits_on_content, violations_of_user_rights FROM fotn_score WHERE iso3=?")
    p = [s["iso3"] or "THA"]
    if s["level"] == "year":
        sql += " AND data_year=?"; p.append(s["fy"])
    return q(sql + " ORDER BY data_year", p)


@lru_cache(maxsize=None)
def c33():
    return q("SELECT f.data_year, f.report_edition, f.total_score, "
             "(SELECT COUNT(*) FROM afnc_item a WHERE a.item_type='Verdict' AND a.year=f.data_year) AS afnc_verdicts "
             "FROM fotn_score f WHERE f.iso3='THA' AND f.data_year BETWEEN 2019 AND 2024 ORDER BY f.data_year")


def score_series(iso3):
    """คะแนนรวมรายปีของประเทศที่เลือก (ปีเดียวกับกราฟของไทย)"""
    return q("SELECT data_year, total_score FROM fotn_score WHERE iso3=? AND data_year BETWEEN 2019 AND 2024 "
             "ORDER BY data_year", (iso3,))


@lru_cache(maxsize=None)
def c34():
    return q("SELECT year, COUNT(*) AS debunks, SUM(n_articles) AS articles FROM eu_debunk GROUP BY year ORDER BY year")


def c35(fy):
    return q("SELECT iso3, COALESCE(country_th, country) AS name, status_code, status_th, total_score "
             "FROM fotn_score WHERE data_year=?", (fy,))


def rank_all(fy):
    return q("SELECT * FROM (SELECT iso3, total_score, RANK() OVER (ORDER BY total_score DESC) AS rnk, "
             "COUNT(*) OVER () AS n FROM fotn_score WHERE data_year=?) WHERE iso3='THA'", (fy,))


@lru_cache(maxsize=None)
def fotn_years():
    return q("SELECT DISTINCT data_year FROM fotn_score ORDER BY data_year")["data_year"].tolist()


# ---------- แท็บ 4 ----------
PREPARED_TABLES = ["aiid_incident", "afnc_item", "afnc_ai_match", "acsc_week", "weekly_panel", "eu_article",
                   "eu_debunk", "eu_debunk_keyword", "theme", "eu_debunk_theme", "afnc_theme", "fotn_score",
                   "country_group", "thai_data_dictionary"]


def table(name):
    if name not in PREPARED_TABLES:
        raise ValueError(name)
    return q(f"SELECT * FROM {name}")


def to_csv_bytes_str(df):
    """CSV UTF-8 พร้อม BOM (ใส่ BOM นำหน้าเมื่อส่งเป็น string)"""
    return "﻿" + df.to_csv(index=False)
