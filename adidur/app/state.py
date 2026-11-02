"""ค่าเริ่มต้น state ต่อแท็บ, แปลง state <-> URL query, ตัวช่วย พ.ศ."""
from urllib.parse import urlencode, parse_qs

TH_MONTHS = ["ม.ค.", "ก.พ.", "มี.ค.", "เม.ย.", "พ.ค.", "มิ.ย.", "ก.ค.", "ส.ค.", "ก.ย.", "ต.ค.", "พ.ย.", "ธ.ค."]

DEFAULTS = {
    1: {"y0": 2015, "y1": 2026, "level": "year", "year": None, "month": None,
        "levels": ["mention", "media_evidence"], "category": None, "imp": None,
        "acsc_level": "month", "acsc_month": None, "acsc_week": None, "inc_suspect": True},
    2: {"y0": 2020, "y1": 2022, "level": "year", "year": None, "month": None, "theme": "covid",
        "afnc_category": None},
    3: {"fy": 2024, "groups": ["ASEAN"], "add_rus": False, "level": "group", "iso3": None},
    4: {"dataset": "aiid_incident"},
}
INT_KEYS = {"y0", "y1", "year", "fy"}
LIST_KEYS = {"levels", "groups"}
BOOL_KEYS = {"inc_suspect", "add_rus"}


def be(y):
    """ค.ศ. -> พ.ศ. (แสดงผลเท่านั้น)"""
    return None if y is None else int(y) + 543


def month_label(m):
    """'2025-07' -> 'ก.ค. 2568'"""
    if not m:
        return ""
    y, mm = m.split("-")
    return f"{TH_MONTHS[int(mm) - 1]} {int(y) + 543}"


def date_th(d):
    """'2025-07-13' -> '13 ก.ค. 2568'"""
    if not d or str(d) == "nan":
        return ""
    y, m, dd = str(d)[:10].split("-")
    return f"{int(dd)} {TH_MONTHS[int(m) - 1]} {int(y) + 543}"


def to_query(tab, state):
    """เก็บเฉพาะค่าที่ต่างจากค่าเริ่มต้น เพื่อให้ลิงก์สั้น"""
    d = DEFAULTS[tab]
    params = {"tab": tab}
    for k, v in state.items():
        if v == d.get(k) or v is None:
            continue
        if isinstance(v, bool):
            params[k] = int(v)
        elif isinstance(v, list):
            params[k] = ",".join(v)
        else:
            params[k] = v
    return "?" + urlencode(params)


def from_query(tab, query, current=None):
    """คืน state; ถ้า query ไม่มีพารามิเตอร์ของแท็บเลย ใช้ current (หรือค่าเริ่มต้น)"""
    q = parse_qs((query or "").lstrip("?"))
    q.pop("tab", None)
    if not q:
        return dict(current) if current else dict(DEFAULTS[tab])
    state = {k: (list(v) if isinstance(v, list) else v) for k, v in DEFAULTS[tab].items()}
    for k, vals in q.items():
        if k not in state:
            continue
        v = vals[0]
        if k in INT_KEYS:
            state[k] = int(v) if v.lstrip("-").isdigit() else state[k]
        elif k in BOOL_KEYS:
            state[k] = v in ("1", "true", "True")
        elif k in LIST_KEYS:
            state[k] = [x for x in v.split(",") if x]
        elif k == "imp":
            state[k] = int(v)
        else:
            state[k] = v
    return state


def parse_tab(query):
    q = parse_qs((query or "").lstrip("?"))
    t = q.get("tab", [""])[0]
    return t if t in ("1", "2", "3", "4") else "landing"
