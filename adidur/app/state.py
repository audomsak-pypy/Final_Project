"""state.py — จัดการสถานะ (state) ของแต่ละแท็บ, การแปลง URL query และฟังก์ชันช่วย พ.ศ."""
from urllib.parse import urlencode, parse_qs

MONTH_NAMES_TH = {
    1: 'ม.ค.', 2: 'ก.พ.', 3: 'มี.ค.', 4: 'เม.ย.', 5: 'พ.ค.', 6: 'มิ.ย.',
    7: 'ก.ค.', 8: 'ส.ค.', 9: 'ก.ย.', 10: 'ต.ค.', 11: 'พ.ย.', 12: 'ธ.ค.'
}

def to_be(year):
    if year is None:
        return None
    try:
        return int(year) + 543
    except (ValueError, TypeError):
        return year

def to_ce(year_be):
    if year_be is None:
        return None
    try:
        return int(year_be) - 543
    except (ValueError, TypeError):
        return year_be

def format_year_be(year):
    be = to_be(year)
    return str(be) if be is not None else ''

def format_month_be(yyyy_mm):
    if not yyyy_mm or '-' not in str(yyyy_mm):
        return str(yyyy_mm) if yyyy_mm else ''
    parts = str(yyyy_mm).split('-')
    try:
        y, m = int(parts[0]), int(parts[1])
        return f'{MONTH_NAMES_TH.get(m, m)} {to_be(y)}'
    except Exception:
        return yyyy_mm

def format_date_be(yyyy_mm_dd):
    if not yyyy_mm_dd or '-' not in str(yyyy_mm_dd):
        return str(yyyy_mm_dd) if yyyy_mm_dd else ''
    parts = str(yyyy_mm_dd).split('-')
    try:
        y, m, d = int(parts[0]), int(parts[1]), int(parts[2])
        return f'{d} {MONTH_NAMES_TH.get(m, m)} {to_be(y)}'
    except Exception:
        return yyyy_mm_dd

DEFAULT_TAB1_STATE = {
    'tab': '1',
    'y0': 2015,
    'y1': 2026,
    'level': 'year',
    'year': None,
    'month': None,
    'levels': ['mention', 'media_evidence'],
    'category': None,
    'imp': None,
    'acsc_level': 'week',
    'acsc_month': None,
    'acsc_week': None,
    'inc_suspect': True,
}

DEFAULT_TAB2_STATE = {
    'tab': '2',
    'y0': 2020,
    'y1': 2022,
    'level': 'year',
    'year': None,
    'month': None,
    'theme': 'covid',
    'afnc_category': None,
}

DEFAULT_TAB3_STATE = {
    'tab': '3',
    'fy': 2024,
    'groups': ['ASEAN'],
    'add_rus': False,
    'level': 'group',
    'iso3': 'THA',
}

DEFAULT_TAB4_STATE = {
    'tab': '4',
    'dataset': 'AIID',
}

def state_to_url(state):
    params = {}
    for k, v in state.items():
        if v is None:
            continue
        if isinstance(v, bool):
            params[k] = 'true' if v else 'false'
        elif isinstance(v, list):
            params[k] = ','.join(str(x) for x in v)
        else:
            params[k] = str(v)
    return '?' + urlencode(params) if params else ''

def url_to_state(query_string, default_state):
    if not query_string:
        return dict(default_state)
    if query_string.startswith('?'):
        query_string = query_string[1:]
    parsed = parse_qs(query_string)
    result = dict(default_state)
    for k, default_val in default_state.items():
        if k in parsed:
            raw = parsed[k][0]
            if isinstance(default_val, bool):
                result[k] = (raw.lower() in ('true', '1', 'yes'))
            elif isinstance(default_val, int):
                try:
                    result[k] = int(raw)
                except ValueError:
                    result[k] = default_val
            elif isinstance(default_val, list):
                if raw.strip():
                    result[k] = [x.strip() for x in raw.split(',') if x.strip()]
                else:
                    result[k] = []
            elif default_val is None:
                if k in ('year', 'imp', 'y0', 'y1', 'fy'):
                    try:
                        result[k] = int(raw)
                    except ValueError:
                        result[k] = raw
                else:
                    result[k] = raw
            else:
                result[k] = raw
    return result
