"""ดาวน์โหลดผลตามตัวกรองปัจจุบัน: CSV UTF-8 พร้อม BOM"""
import pandas as pd

from . import queries as Q
from .state import be


def filtered_download(tab, state):
    """tab: '1' | '2' | '3', state: state ของแท็บนั้น -> dict สำหรับ dcc.Download"""
    s = state
    if tab == "1":
        df = Q.t1(s)
        name = f"adidur_tab1_{be(s['y0'])}-{be(s['y1'])}" + (f"_{be(s['year'])}" if s.get("year") else "") + "_filtered.csv"
    elif tab == "2":
        af, eu = Q.t2(s)
        df = pd.concat([af, eu], ignore_index=True)
        name = f"adidur_tab2_{s['theme']}_{be(s['y0'])}-{be(s['y1'])}_filtered.csv"
    else:
        df = Q.c31(s)
        name = f"adidur_tab3_{be(s['fy'])}_filtered.csv"
    return dict(content=Q.to_csv_bytes_str(df), filename=name, type="text/csv")
