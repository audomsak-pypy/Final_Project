"""queries.py — ฟังก์ชันรัน SQL ทุกตัวจาก 03_DATABASE_SCHEMA.md รับ state คืน DataFrame หรือ dict"""
import os
import sqlite3
import pandas as pd

def get_connection(db_path=None):
    if db_path is None:
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        db_path = os.path.join(base_dir, "data", "adidur.db")
    return sqlite3.connect(db_path)

# =========================================================================
# TAB 1 QUERIES
# =========================================================================

def get_k1_1(con, state):
    """K1.1 เหตุการณ์ Deepfake (AIID)"""
    y0, y1 = state.get('y0', 2015), state.get('y1', 2026)
    year = state.get('year')
    month = state.get('month')
    sql = """
    SELECT COUNT(DISTINCT incident_id) FROM aiid_incident
    WHERE is_deepfake=1 AND year BETWEEN ? AND ?
      AND (? IS NULL OR year=?) AND (? IS NULL OR month=?)
    """
    cur = con.cursor()
    cur.execute(sql, (y0, y1, year, year, month, month))
    row = cur.fetchone()
    return row[0] if row else 0

def get_k1_2(con, state):
    """K1.2 ข่าวเท็จที่เกี่ยวกับ AI (AFNC) แยก mention / media_evidence"""
    y0, y1 = state.get('y0', 2015), state.get('y1', 2026)
    year = state.get('year')
    month = state.get('month')
    category = state.get('category')
    imp = state.get('imp')
    levels = state.get('levels') or ['mention', 'media_evidence']
    if not levels:
        return {'total': 0, 'mention': 0, 'media_evidence': 0}
    placeholders = ','.join('?' for _ in levels)
    sql = f"""
    SELECT m.ai_level, COUNT(DISTINCT a.post_id) AS n
    FROM afnc_ai_match m JOIN afnc_item a USING(post_id)
    WHERE a.year BETWEEN ? AND ? AND (? IS NULL OR a.year=?) AND (? IS NULL OR a.month=?)
      AND m.ai_level IN ({placeholders}) AND (? IS NULL OR a.category_th=?)
      AND (? IS NULL OR m.impersonation_flag=?)
    GROUP BY m.ai_level
    """
    params = [y0, y1, year, year, month, month] + list(levels) + [category, category, imp, imp]
    df = pd.read_sql(sql, con, params=params)
    counts = dict(zip(df['ai_level'], df['n']))
    mention = counts.get('mention', 0)
    media = counts.get('media_evidence', 0)
    return {'total': mention + media, 'mention': mention, 'media_evidence': media}

def get_k1_3_4(con, state):
    """K1.3 / K1.4 คดีและความเสียหาย (ACSC)"""
    y0, y1 = state.get('y0', 2015), state.get('y1', 2026)
    year = state.get('year')
    month = state.get('month')
    inc_suspect = 1 if state.get('inc_suspect', True) else 0

    # Query with user's inc_suspect setting
    sql = """
    SELECT COUNT(*) AS weeks, SUM(cases) AS cases, SUM(loss_baht) AS loss_baht,
           CASE WHEN SUM(cases) > 0 THEN 1.0*SUM(loss_baht)/SUM(cases) ELSE NULL END AS loss_per_case
    FROM acsc_week
    WHERE cases IS NOT NULL AND loss_baht IS NOT NULL
      AND CAST(substr(week_start,1,4) AS INT) BETWEEN ? AND ?
      AND (? IS NULL OR substr(week_start,1,4)=CAST(? AS TEXT))
      AND (? IS NULL OR month=?)
      AND (?=1 OR COALESCE(flag_type,'')<>'suspect')
    """
    cur = con.cursor()
    cur.execute(sql, (y0, y1, year, year, month, month, inc_suspect))
    row = cur.fetchone()
    weeks = row[0] or 0
    cases = row[1] or 0
    loss_baht = row[2] or 0
    loss_per_case = row[3] or 0.0

    # Query with suspect = 1 and suspect = 0 for difference
    cur.execute(sql, (y0, y1, year, year, month, month, 1))
    r_all = cur.fetchone()
    cur.execute(sql, (y0, y1, year, year, month, month, 0))
    r_nosus = cur.fetchone()

    diff_cases = (r_all[1] or 0) - (r_nosus[1] or 0)
    diff_loss = (r_all[2] or 0) - (r_nosus[2] or 0)
    diff_lpc = ((r_all[3] or 0.0) - (r_nosus[3] or 0.0))

    return {
        'weeks': weeks,
        'cases': cases,
        'loss_baht': loss_baht,
        'loss_per_case': loss_per_case,
        'diff_cases': diff_cases,
        'diff_loss': diff_loss,
        'diff_lpc': diff_lpc,
        'has_data': weeks > 0
    }

def get_c1_1(con, state):
    """C1.1 เส้น Deepfake (AIID)"""
    y0, y1 = state.get('y0', 2015), state.get('y1', 2026)
    year = state.get('year')
    level = state.get('level', 'year')
    if level == 'month' and year is not None:
        sql = """
        SELECT month AS t, COUNT(*) AS n FROM aiid_incident
        WHERE is_deepfake=1 AND year=? GROUP BY month ORDER BY month
        """
        return pd.read_sql(sql, con, params=[year])
    else:
        sql = """
        SELECT year AS t, COUNT(*) AS n FROM aiid_incident
        WHERE is_deepfake=1 AND year BETWEEN ? AND ? GROUP BY year ORDER BY year
        """
        return pd.read_sql(sql, con, params=[y0, y1])

def get_c1_2(con, state):
    """C1.2 เส้นข่าว AI (AFNC) แยกระดับ"""
    y0, y1 = state.get('y0', 2015), state.get('y1', 2026)
    year = state.get('year')
    category = state.get('category')
    imp = state.get('imp')
    level = state.get('level', 'year')

    if level == 'month' and year is not None:
        sql = """
        SELECT a.month AS t, m.ai_level, COUNT(*) AS n
        FROM afnc_ai_match m JOIN afnc_item a USING(post_id)
        WHERE a.year=? AND (? IS NULL OR a.category_th=?)
          AND (? IS NULL OR m.impersonation_flag=?)
        GROUP BY a.month, m.ai_level ORDER BY a.month
        """
        return pd.read_sql(sql, con, params=[year, category, category, imp, imp])
    else:
        sql = """
        SELECT a.year AS t, m.ai_level, COUNT(*) AS n
        FROM afnc_ai_match m JOIN afnc_item a USING(post_id)
        WHERE a.year BETWEEN ? AND ? AND (? IS NULL OR a.category_th=?)
          AND (? IS NULL OR m.impersonation_flag=?)
        GROUP BY a.year, m.ai_level ORDER BY a.year
        """
        return pd.read_sql(sql, con, params=[y0, y1, category, category, imp, imp])

def get_c1_3(con, state):
    """C1.3 แท่งแนวนอน หมวดข่าว AI"""
    y0, y1 = state.get('y0', 2015), state.get('y1', 2026)
    year = state.get('year')
    month = state.get('month')
    imp = state.get('imp')
    levels = state.get('levels') or ['mention', 'media_evidence']
    if not levels:
        return pd.DataFrame(columns=['category_th', 'n'])
    placeholders = ','.join('?' for _ in levels)
    sql = f"""
    SELECT a.category_th, COUNT(*) AS n FROM afnc_ai_match m JOIN afnc_item a USING(post_id)
    WHERE a.year BETWEEN ? AND ? AND (? IS NULL OR a.year=?) AND (? IS NULL OR a.month=?)
      AND m.ai_level IN ({placeholders}) AND (? IS NULL OR m.impersonation_flag=?)
    GROUP BY a.category_th ORDER BY n DESC
    """
    params = [y0, y1, year, year, month, month] + list(levels) + [imp, imp]
    return pd.read_sql(sql, con, params=params)

def get_c1_4(con, state):
    """C1.4 การ์ดข่าวเด่น (อันดับ 1–3 ยอดเข้าชมสูงสุด + 1 ต่ำสุด)"""
    y0, y1 = state.get('y0', 2015), state.get('y1', 2026)
    year = state.get('year')
    month = state.get('month')
    category = state.get('category')
    imp = state.get('imp')
    levels = state.get('levels') or ['mention', 'media_evidence']
    if not levels:
        return {'top1': None, 'top2': None, 'top3': None, 'lowest': None, 'total_items': 0}
    placeholders = ','.join('?' for _ in levels)
    sql = f"""
    SELECT a.post_id, a.date, a.title, a.category_th, a.view_count, a.url, m.ai_level, m.evidence_snippet
    FROM afnc_ai_match m JOIN afnc_item a USING(post_id)
    WHERE a.year BETWEEN ? AND ? AND (? IS NULL OR a.year=?) AND (? IS NULL OR a.month=?)
      AND m.ai_level IN ({placeholders}) AND (? IS NULL OR a.category_th=?)
      AND (? IS NULL OR m.impersonation_flag=?)
    ORDER BY a.view_count DESC, a.post_id ASC
    """
    params = [y0, y1, year, year, month, month] + list(levels) + [category, category, imp, imp]
    df = pd.read_sql(sql, con, params=params)
    total_items = len(df)
    if total_items == 0:
        return {'top1': None, 'top2': None, 'top3': None, 'lowest': None, 'total_items': 0}
    top1 = df.iloc[0].to_dict()
    top2 = df.iloc[1].to_dict() if total_items > 1 else None
    top3 = df.iloc[2].to_dict() if total_items > 2 else None
    lowest = df.iloc[-1].to_dict() if total_items >= 4 else None
    return {'top1': top1, 'top2': top2, 'top3': top3, 'lowest': lowest, 'total_items': total_items}

def get_c1_5_6(con, state):
    """C1.5 / C1.6 คดีและความเสียหายรายสัปดาห์ (จาก weekly_panel)"""
    month = state.get('month')
    inc_suspect = 1 if state.get('inc_suspect', True) else 0
    sql = """
    SELECT w.week_start, w.week_end,
      CASE WHEN ?=0 AND w.acsc_flag LIKE 'Suspect%' THEN NULL ELSE w.acsc_cases END AS cases,
      CASE WHEN ?=0 AND w.acsc_flag LIKE 'Suspect%' THEN NULL ELSE w.acsc_loss_baht END AS loss_baht,
      w.acsc_loss_precision AS loss_precision,
      CASE WHEN w.acsc_flag IS NULL THEN NULL WHEN w.acsc_flag LIKE 'Suspect%' THEN 'suspect' ELSE 'note' END AS flag_type,
      w.acsc_reported, w.acsc_source_url AS source_url, w.acsc_flag AS flag_desc
    FROM weekly_panel w
    WHERE w.week_start >= '2025-11-09' AND (? IS NULL OR substr(w.week_start,1,7)=?)
    ORDER BY w.week_start
    """
    return pd.read_sql(sql, con, params=[inc_suspect, inc_suspect, month, month])

def get_t1(con, state):
    """T1 ตารางหลักฐาน: ข่าว AFNC + AIID"""
    y0, y1 = state.get('y0', 2015), state.get('y1', 2026)
    year = state.get('year')
    month = state.get('month')
    category = state.get('category')
    imp = state.get('imp')
    levels = state.get('levels') or ['mention', 'media_evidence']
    placeholders = ','.join('?' for _ in levels) if levels else "''"

    afnc_sql = f"""
    SELECT 'AFNC' AS source, a.date, a.title, a.category_th AS category, m.matched_terms AS reason,
           m.evidence_snippet, m.review_status, a.url
    FROM afnc_ai_match m JOIN afnc_item a USING(post_id)
    WHERE a.year BETWEEN ? AND ? AND (? IS NULL OR a.year=?) AND (? IS NULL OR a.month=?)
      AND m.ai_level IN ({placeholders}) AND (? IS NULL OR a.category_th=?)
      AND (? IS NULL OR m.impersonation_flag=?)
    """
    params_afnc = [y0, y1, year, year, month, month] + list(levels) + [category, category, imp, imp]

    aiid_sql = """
    SELECT 'AIID' AS source, date, title, risk_domain AS category, deepfake_terms AS reason,
           substr(description,1,160) AS evidence_snippet, 'ต้องตรวจสอบ' AS review_status, url
    FROM aiid_incident
    WHERE is_deepfake=1 AND year BETWEEN ? AND ? AND (? IS NULL OR year=?) AND (? IS NULL OR month=?)
    """
    params_aiid = [y0, y1, year, year, month, month]

    sql = f"""
    {afnc_sql}
    UNION ALL
    {aiid_sql}
    ORDER BY date DESC
    """
    return pd.read_sql(sql, con, params=params_afnc + params_aiid)

# =========================================================================
# TAB 2 QUERIES
# =========================================================================

def get_k2(con, state):
    """K2 การ์ด 3 ใบ: EU การหักล้าง / AFNC ข่าวเท็จ / AIID Misinformation"""
    y0, y1 = state.get('y0', 2020), state.get('y1', 2022)
    year = state.get('year')
    cur = con.cursor()

    cur.execute("""
    SELECT COUNT(DISTINCT debunk_id) FROM eu_debunk
    WHERE year BETWEEN ? AND ? AND (? IS NULL OR year=?)
    """, (y0, y1, year, year))
    eu_cnt = cur.fetchone()[0] or 0

    cur.execute("""
    SELECT COUNT(*) FROM afnc_item
    WHERE item_type='Verdict' AND verdict_en IN ('Fake','Distorted')
      AND year BETWEEN ? AND ? AND (? IS NULL OR year=?)
    """, (y0, y1, year, year))
    af_cnt = cur.fetchone()[0] or 0

    cur.execute("""
    SELECT COUNT(*) FROM aiid_incident
    WHERE is_misinfo=1 AND year BETWEEN ? AND ? AND (? IS NULL OR year=?)
    """, (y0, y1, year, year))
    ai_cnt = cur.fetchone()[0] or 0

    return {'eu_debunks': eu_cnt, 'afnc_false': af_cnt, 'aiid_misinfo': ai_cnt}

def get_c2_1(con, state):
    """C2.1 Heatmap EUvsDisinfo: ปี × ประเด็น สัดส่วน %"""
    y0, y1 = state.get('y0', 2020), state.get('y1', 2022)
    sql = """
    WITH den AS (SELECT year, COUNT(*) n FROM eu_debunk WHERE year BETWEEN ? AND ? GROUP BY year)
    SELECT d.year, t.theme_id, th.theme_th, COUNT(DISTINCT t.debunk_id) AS n,
           100.0*COUNT(DISTINCT t.debunk_id)/den.n AS pct
    FROM eu_debunk_theme t
    JOIN eu_debunk d USING(debunk_id)
    JOIN theme th USING(theme_id)
    JOIN den USING(year)
    GROUP BY d.year, t.theme_id ORDER BY d.year, t.theme_id
    """
    return pd.read_sql(sql, con, params=[y0, y1])

def get_c2_2(con, state):
    """C2.2 Heatmap AFNC: ปี × ประเด็น สัดส่วน %"""
    y0, y1 = state.get('y0', 2020), state.get('y1', 2022)
    sql = """
    WITH den AS (SELECT year, COUNT(*) n FROM afnc_item
                 WHERE item_type='Verdict' AND verdict_en IN ('Fake','Distorted') AND year BETWEEN ? AND ?
                 GROUP BY year)
    SELECT a.year, t.theme_id, th.theme_th, th.afnc_rule, COUNT(DISTINCT t.post_id) AS n,
           100.0*COUNT(DISTINCT t.post_id)/den.n AS pct
    FROM afnc_theme t
    JOIN afnc_item a USING(post_id)
    JOIN theme th USING(theme_id)
    JOIN den USING(year)
    GROUP BY a.year, t.theme_id ORDER BY a.year, t.theme_id
    """
    return pd.read_sql(sql, con, params=[y0, y1])

def get_c2_3(con, state):
    """C2.3 เส้นสัดส่วนของประเด็นที่เลือก (:theme) ทั้งสองแหล่ง"""
    y0, y1 = state.get('y0', 2020), state.get('y1', 2022)
    theme = state.get('theme', 'covid')
    df_eu = get_c2_1(con, state)
    df_af = get_c2_2(con, state)
    sub_eu = df_eu[df_eu['theme_id'] == theme][['year', 'pct']].rename(columns={'pct': 'eu_pct'})
    sub_af = df_af[df_af['theme_id'] == theme][['year', 'pct']].rename(columns={'pct': 'afnc_pct'})
    years = pd.DataFrame({'year': list(range(y0, y1 + 1))})
    m = years.merge(sub_eu, on='year', how='left').merge(sub_af, on='year', how='left')
    return m

def get_c2_4(con, state):
    """C2.4 แท่งซ้อน: ข่าวเท็จ AFNC ตามหมวด รายปี (หรือรายเดือน)"""
    y0, y1 = state.get('y0', 2020), state.get('y1', 2022)
    year = state.get('year')
    level = state.get('level', 'year')
    if level == 'month' and year is not None:
        sql = """
        SELECT month AS t, category_th, COUNT(*) AS n FROM afnc_item
        WHERE item_type='Verdict' AND verdict_en IN ('Fake','Distorted') AND year=?
        GROUP BY month, category_th ORDER BY month
        """
        return pd.read_sql(sql, con, params=[year])
    else:
        sql = """
        SELECT year AS t, category_th, COUNT(*) AS n FROM afnc_item
        WHERE item_type='Verdict' AND verdict_en IN ('Fake','Distorted') AND year BETWEEN ? AND ?
        GROUP BY year, category_th ORDER BY year
        """
        return pd.read_sql(sql, con, params=[y0, y1])

def get_c2_5(con, state):
    """C2.5 แผงบริบท AIID Misinformation รายปี"""
    y0, y1 = state.get('y0', 2020), state.get('y1', 2022)
    sql = """
    SELECT year, COUNT(*) AS n FROM aiid_incident
    WHERE is_misinfo=1 AND year BETWEEN ? AND ? GROUP BY year ORDER BY year
    """
    return pd.read_sql(sql, con, params=[y0, y1])

def get_t2(con, state):
    """T2 ตารางรายการในประเด็นและปีที่เลือก"""
    theme = state.get('theme', 'covid')
    year = state.get('year')
    sql = """
    SELECT 'AFNC' AS source, a.date, a.title AS headline, t.matched_by, t.matched_terms, a.url
    FROM afnc_theme t JOIN afnc_item a USING(post_id)
    WHERE t.theme_id=? AND (? IS NULL OR a.year=?)
    UNION ALL
    SELECT 'EUvsDisinfo' AS source, d.debunk_date AS date, d.keywords AS headline, 'keyword' AS matched_by,
           t.matched_terms,
           (SELECT article_url FROM eu_article e WHERE e.debunk_id=d.debunk_id
            ORDER BY (e.class='disinformation') DESC, e.article_id LIMIT 1) AS url
    FROM eu_debunk_theme t JOIN eu_debunk d USING(debunk_id)
    WHERE t.theme_id=? AND (? IS NULL OR d.year=?)
    ORDER BY date DESC
    """
    return pd.read_sql(sql, con, params=[theme, year, year, theme, year, year])

# =========================================================================
# TAB 3 QUERIES
# =========================================================================

def get_k3(con, state):
    """K3 คะแนนไทย สถานะ ปีข้อมูล ปีรายงาน"""
    fy = state.get('fy', 2024)
    sql = """
    SELECT total_score, status_th, data_year, report_edition
    FROM fotn_score WHERE iso3='THA' AND data_year=?
    """
    df = pd.read_sql(sql, con, params=[fy])
    if not df.empty:
        return df.iloc[0].to_dict()
    return {'total_score': 39, 'status_th': 'ไม่เสรี', 'data_year': fy, 'report_edition': fy + 1}

def get_c3_1(con, state):
    """C3.1 แท่งแนวนอนเทียบประเทศในกลุ่มที่เลือก"""
    fy = state.get('fy', 2024)
    groups = state.get('groups') or ['ASEAN']
    add_rus = state.get('add_rus', False)
    grps = list(groups)
    if add_rus and 'เปรียบเทียบเพิ่ม' not in grps:
        grps.append('เปรียบเทียบเพิ่ม')
    placeholders = ','.join('?' for _ in grps)
    sql = f"""
    SELECT f.iso3, COALESCE(f.country_th, f.country) AS name, f.total_score, f.status_th,
           RANK() OVER (ORDER BY f.total_score DESC) AS rank_in_group,
           COUNT(*) OVER () AS n_in_group
    FROM fotn_score f JOIN country_group g ON g.iso3=f.iso3 AND g.group_name IN ({placeholders})
    WHERE f.data_year=? ORDER BY f.total_score DESC
    """
    return pd.read_sql(sql, con, params=grps + [fy])

def get_c3_2(con, state):
    """C3.2 แท่งซ้อน 3 องค์ประกอบ (L0 ประเทศในกลุ่ม / L1 ประเทศเดียวรายปี)"""
    fy = state.get('fy', 2024)
    iso3 = state.get('iso3')
    level = state.get('level', 'group')
    if level in ('country', 'year') and iso3 is not None:
        sql = """
        SELECT iso3, COALESCE(country_th, country) AS name, data_year, report_edition,
               obstacles_to_access, limits_on_content, violations_of_user_rights, total_score
        FROM fotn_score WHERE iso3=? ORDER BY data_year
        """
        return pd.read_sql(sql, con, params=[iso3])
    else:
        groups = state.get('groups') or ['ASEAN']
        add_rus = state.get('add_rus', False)
        grps = list(groups)
        if add_rus and 'เปรียบเทียบเพิ่ม' not in grps:
            grps.append('เปรียบเทียบเพิ่ม')
        placeholders = ','.join('?' for _ in grps)
        sql = f"""
        SELECT f.iso3, COALESCE(f.country_th, f.country) AS name, f.data_year, f.report_edition,
               f.obstacles_to_access, f.limits_on_content, f.violations_of_user_rights, f.total_score
        FROM fotn_score f JOIN country_group g ON g.iso3=f.iso3 AND g.group_name IN ({placeholders})
        WHERE f.data_year=? ORDER BY f.total_score DESC
        """
        return pd.read_sql(sql, con, params=grps + [fy])

def get_c3_3(con):
    """C3.3 สองแผง 2562–2567: คะแนนไทย กับจำนวนคำตัดสิน AFNC (ไทยเท่านั้น)"""
    sql = """
    SELECT f.data_year, f.report_edition, f.total_score,
           (SELECT COUNT(*) FROM afnc_item a WHERE a.item_type='Verdict' AND a.year=f.data_year) AS afnc_verdicts
    FROM fotn_score f WHERE f.iso3='THA' AND f.data_year BETWEEN 2019 AND 2024 ORDER BY f.data_year
    """
    return pd.read_sql(sql, con)

def get_c3_4(con):
    """C3.4 บริบท EUvsDisinfo: การหักล้างรายปี"""
    sql = """
    SELECT year, COUNT(*) AS debunks, SUM(n_articles) AS articles FROM eu_debunk GROUP BY year ORDER BY year
    """
    return pd.read_sql(sql, con)

def get_c3_5(con, fy=2024):
    """C3.5 แผนที่สถานะแต่ละประเทศ"""
    sql = """
    SELECT iso3, country, country_th, total_score, status_th, status_code
    FROM fotn_score WHERE data_year=?
    """
    return pd.read_sql(sql, con, params=[fy])

# =========================================================================
# TAB 4 QUERIES & EXPORTS
# =========================================================================

def get_table_data(con, table_name):
    """ดึงข้อมูลเต็มของตารางที่กำหนด"""
    return pd.read_sql(f"SELECT * FROM {table_name}", con)

def get_theme_definitions(con):
    """พจนานุกรมประเด็น"""
    return pd.read_sql("SELECT * FROM theme", con)

def get_thai_data_dict(con):
    """พจนานุกรมข้อมูลไทย"""
    return pd.read_sql("SELECT * FROM thai_data_dictionary", con)
