"""build_db.py — เตรียมข้อมูลโครงงาน Adidur และสร้างฐานข้อมูล SQLite (adidur.db)
ใช้: python build_db.py <โฟลเดอร์ไฟล์ต้นฉบับ> <ไฟล์ db ปลายทาง>
ไฟล์ต้นฉบับไม่ถูกแก้ไข ทุกตารางเก็บปี ค.ศ. (แปลงเป็น พ.ศ. ตอนแสดงผลเท่านั้น)
"""
import re, sys, sqlite3, glob, os
import pandas as pd

SRC = sys.argv[1] if len(sys.argv) > 1 else "data/raw"
DB = sys.argv[2] if len(sys.argv) > 2 else "data/adidur.db"

def find(pattern):
    hits = glob.glob(os.path.join(SRC, "**", pattern), recursive=True)
    if not hits:
        sys.exit(f"ไม่พบไฟล์ที่จำเป็น: {pattern} ในโฟลเดอร์ {SRC}")
    return hits[0]

# ---------- คำค้น (ตั้งเอง) ----------
URL_RE = re.compile(r"https?://\S+|www\.\S+")
TAG_RE = re.compile(r"<[^>]+>")
def clean(t):
    t = "" if pd.isna(t) else str(t)
    return re.sub(r"\s+", " ", URL_RE.sub(" ", TAG_RE.sub(" ", t))).strip()

# ข่าว AI ระดับ 2: มีคำบ่งชี้ว่าใช้ AI สร้าง/ดัดแปลงสื่อ
AI_MEDIA = re.compile(
    r"deep\s?-?fake|ดี[ปพ]\s?เฟ[กคค์]|โคลนเสียง|ปลอมเสียง|เลียนเสียง|"
    r"(?:สร้าง|ทำ|ตัดต่อ|ปลอม|ดัดแปลง|เจน)\S{0,12}?(?:ด้วย|โดย|จาก|ใช้)\s?(?:AI|เอไอ(?!เอส)|ปัญญาประดิษฐ์)|"
    r"(?<![A-Za-z])AI(?![A-Za-z])\s?(?:สร้าง|ปลอม|ตัดต่อ|เจน)|"
    r"(?:ภาพ|คลิป|วิดีโอ|เสียง)\S{0,10}?(?<![A-Za-z])(?:AI|เอไอ(?!เอส))(?![A-Za-z])",
    re.I)
# ข่าว AI ระดับ 1: กล่าวถึง AI (ห้ามค้น ai ตัวเล็กแบบหลวม)
AI_MENTION = re.compile(
    r"(?<![A-Za-z])AI(?![A-Za-z])|(?<![A-Za-z])A\.I\.|artificial intelligence|ปัญญาประดิษฐ์|"
    r"เอไอ(?!เอส)|chat\s?gpt|แชท\s?จีพีที|chatbot|แชทบอท|generative")
IMPERSONATE = re.compile(r"แอบอ้าง")

AIID_DEEPFAKE = re.compile(r"deep\s?-?fake|voice[- ]clon|face[- ]?swap|synthetic (?:voice|video|media|image)", re.I)

# พจนานุกรมประเด็น (ตั้งเอง)
THEMES = [
 # id, ชื่อ, EU keywords (ตรงทั้งคำ ไม่สนตัวพิมพ์), AFNC regex, AFNC category_en
 ("covid", "โควิด-19", {"coronavirus", "covid-19", "sputnik v", "pandemic"},
  r"โควิด|covid|โคโรนา|ซิโนแวค|ซิโนฟาร์ม|ไฟเซอร์|โมเดอร์นา|แอสตร้า", None),
 ("ukraine", "สงครามยูเครน", {"war in ukraine", "invasion of ukraine", "ukraine", "eastern ukraine", "donbas",
  "crimea", "euromaidan", "ukrainian statehood", "ukrainian disintegration", "volodymyr zelensky",
  "minsk agreements", "abandoned ukraine", "dnr", "lnr", "dpr", "petro poroshenko", "azov sea", "kerch"},
  r"ยูเครน|เซเลนส|ไครเมีย|ดอนบาส|ukraine", None),
 ("other_conflict", "สงครามและความขัดแย้งอื่น", {"syrian war", "military", "terrorism", "chemical weapons/attack",
  "nuclear issues", "war crimes", "civil war", "daesh", "nagorno-karabakh", "russo-georgian war",
  "military exercise", "warmongering", "war preparation"},
  r"สงคราม|ปะทะ|อิสราเอล|ปาเลสไตน์|ฮามาส|ขีปนาวุธ|นิวเคลียร์|ก่อการร้าย", None),
 ("health", "สุขภาพ", {"vaccination", "health", "biological weapons", "virus / bacteria threat", "laboratory",
  "lugar laboratory", "food"}, None, {"Health products"}),
 ("finance", "การเงินและเศรษฐกิจ", {"sanctions", "economic difficulties", "economy", "energy", "gas",
  "nord stream 2", "trade"}, None, {"Finance & stocks", "Economy"}),
 ("politics", "การเมือง การเลือกตั้ง และนโยบายรัฐ", {"elections", "manipulated elections/referendum",
  "election meddling", "referendum", "us presidential election 2020", "protest", "coup",
  "colour revolutions", "democracy"}, None, {"Government policy & news"}),
 ("conspiracy", "ทฤษฎีสมคบคิด", {"conspiracy theory", "secret elites / global elites", "deep state", "george soros"},
  r"สมคบคิด|อิลลูมินาติ|ฟรีเมสัน", None),
]
ASEAN = ["THA", "MYS", "IDN", "PHL", "VNM", "MMR", "KHM", "SGP"]
TH_NAME = {"THA": "ไทย", "MYS": "มาเลเซีย", "IDN": "อินโดนีเซีย", "PHL": "ฟิลิปปินส์", "VNM": "เวียดนาม",
           "MMR": "เมียนมา", "KHM": "กัมพูชา", "SGP": "สิงคโปร์", "RUS": "รัสเซีย"}

def main():
    con = sqlite3.connect(DB)
    # ---------- AIID ----------
    aiid = pd.read_excel(find("AIID_Excel_Export-*.xlsx"), sheet_name="Incidents", header=2)
    aiid = aiid.rename(columns={"Incident ID": "incident_id", "Implicated Systems": "implicated_systems",
                                "Risk Domain": "risk_domain", "Intent": "intent"})
    aiid["date"] = pd.to_datetime(aiid["date"], errors="coerce")
    txt = (aiid["title"].fillna("") + " " + aiid["description"].fillna("") + " " +
           aiid["implicated_systems"].fillna("").astype(str))
    aiid["deepfake_terms"] = txt.apply(lambda s: "; ".join(sorted({m.group(0).lower() for m in AIID_DEEPFAKE.finditer(s)})))
    aiid["is_deepfake"] = (aiid["deepfake_terms"] != "").astype(int)
    aiid["is_misinfo"] = aiid["risk_domain"].fillna("").str.contains("Misinformation").astype(int)
    aiid["year"] = aiid["date"].dt.year
    aiid["month"] = aiid["date"].dt.strftime("%Y-%m")
    aiid["url"] = "https://incidentdatabase.ai/cite/" + aiid["incident_id"].astype(str)
    aiid["date"] = aiid["date"].dt.strftime("%Y-%m-%d")
    cols = ["incident_id", "date", "year", "month", "title", "description", "deployer", "developer", "harmed",
            "implicated_systems", "risk_domain", "intent", "report_count", "is_deepfake", "deepfake_terms",
            "is_misinfo", "url"]
    aiid[cols].to_sql("aiid_incident", con, if_exists="replace", index=False)

    # ---------- AFNC / ACSC / weekly_panel ----------
    thai = pd.read_excel(find("thai-disinfo-scam-dataset.xlsx"), sheet_name=None)
    af = thai["afnc_items"].copy()
    af["clean_text"] = (af["title"].map(clean) + " " + af["content"].map(clean))
    af.drop(columns=["content"]).assign(content_500=thai["afnc_items"]["content"]).to_sql(
        "afnc_item", con, if_exists="replace", index=False)

    false_v = af[(af["item_type"] == "Verdict") & af["verdict_en"].isin(["Fake", "Distorted"])]
    rows = []
    for _, r in false_v.iterrows():
        t = r["clean_text"]
        med = [m.group(0) for m in AI_MEDIA.finditer(t)]
        men = [m.group(0) for m in AI_MENTION.finditer(t)]
        if not (med or men):
            continue
        hit = (AI_MEDIA.search(t) or AI_MENTION.search(t))
        s = max(0, hit.start() - 60)
        rows.append({"post_id": r["post_id"],
                     "ai_level": "media_evidence" if med else "mention",
                     "matched_terms": "; ".join(sorted(set(med + men))),
                     "evidence_snippet": t[s:hit.end() + 60],
                     "review_status": "ต้องตรวจสอบ",
                     "impersonation_flag": int(bool(IMPERSONATE.search(t)))})
    pd.DataFrame(rows).to_sql("afnc_ai_match", con, if_exists="replace", index=False)

    ac = thai["acsc_weekly"].copy()
    for c in ["week_start", "week_end", "article_date"]:
        ac[c] = pd.to_datetime(ac[c]).dt.strftime("%Y-%m-%d")
    ac["is_flagged"] = ac["flag"].notna().astype(int)
    # แยกชนิด flag (ตั้งเอง): suspect = ตัวเลขน่าสงสัย ใช้กับสวิตช์รวม/ไม่รวม, note = หมายเหตุช่วงเวลา/ตัวเลข
    ac["flag_type"] = ac["flag"].map(lambda f: None if pd.isna(f) else ("suspect" if str(f).startswith("Suspect") else "note"))
    ac["month"] = ac["week_start"].str[:7]
    ac.to_sql("acsc_week", con, if_exists="replace", index=False)

    wp = thai["weekly_panel"].copy()
    for c in ["week_start", "week_end"]:
        wp[c] = pd.to_datetime(wp[c]).dt.strftime("%Y-%m-%d")
    wp.to_sql("weekly_panel", con, if_exists="replace", index=False)
    thai["data_dictionary"].to_sql("thai_data_dictionary", con, if_exists="replace", index=False)

    # ---------- EUvsDisinfo ----------
    eu = pd.read_csv(find("euvsdisinfo_base.csv"))
    eu["debunk_date"] = pd.to_datetime(eu["debunk_date"], format="%d-%m-%Y").dt.strftime("%Y-%m-%d")
    eu.to_sql("eu_article", con, if_exists="replace", index=False)
    deb = eu.groupby("debunk_id").agg(debunk_date=("debunk_date", "first"), keywords=("keywords", "first"),
                                     n_articles=("article_id", "count")).reset_index()
    deb["year"] = deb["debunk_date"].str[:4].astype(int)
    deb["month"] = deb["debunk_date"].str[:7]
    deb.to_sql("eu_debunk", con, if_exists="replace", index=False)
    kw = deb[["debunk_id", "keywords"]].dropna().assign(keyword=lambda d: d["keywords"].str.split(","))
    kw = kw.explode("keyword").assign(keyword=lambda d: d["keyword"].str.strip())
    kw = kw[kw["keyword"] != ""].drop_duplicates(["debunk_id", "keyword"])[["debunk_id", "keyword"]]
    kw.to_sql("eu_debunk_keyword", con, if_exists="replace", index=False)

    # ---------- ประเด็น ----------
    theme_rows, eu_map, af_map = [], [], []
    for tid, name, eu_kw, af_re, af_cat in THEMES:
        theme_rows.append({"theme_id": tid, "theme_th": name, "named_by": "ตั้งเอง",
                           "eu_rule": "keyword ∈ {" + ", ".join(sorted(eu_kw)) + "}",
                           "afnc_rule": (f"category_en ∈ {sorted(af_cat)}" if af_cat else f"regex: {af_re}")})
        hits = kw[kw["keyword"].str.lower().isin(eu_kw)]
        for d, g in hits.groupby("debunk_id"):
            eu_map.append({"debunk_id": d, "theme_id": tid, "matched_terms": "; ".join(sorted(g["keyword"]))})
        if af_cat:
            for pid in false_v.loc[false_v["category_en"].isin(af_cat), "post_id"]:
                af_map.append({"post_id": pid, "theme_id": tid, "matched_by": "category", "matched_terms": ""})
        else:
            rx = re.compile(af_re, re.I)
            for _, r in false_v.iterrows():
                m = sorted({x.group(0) for x in rx.finditer(r["clean_text"])})
                if m:
                    af_map.append({"post_id": r["post_id"], "theme_id": tid, "matched_by": "keyword",
                                   "matched_terms": "; ".join(m)})
    pd.DataFrame(theme_rows).to_sql("theme", con, if_exists="replace", index=False)
    pd.DataFrame(eu_map).to_sql("eu_debunk_theme", con, if_exists="replace", index=False)
    pd.DataFrame(af_map).to_sql("afnc_theme", con, if_exists="replace", index=False)

    # ---------- Freedom on the Net ----------
    fo = pd.read_csv(find("freedom_on_the_net_scores.csv"))
    fo["country_th"] = fo["iso3"].map(TH_NAME)
    fo.to_sql("fotn_score", con, if_exists="replace", index=False)
    grp = [{"iso3": i, "group_name": "ASEAN"} for i in ASEAN] + [{"iso3": "RUS", "group_name": "เปรียบเทียบเพิ่ม"}]
    pd.DataFrame(grp).to_sql("country_group", con, if_exists="replace", index=False)

    con.executescript("""
      CREATE INDEX IF NOT EXISTS ix_aiid_year ON aiid_incident(year);
      CREATE INDEX IF NOT EXISTS ix_af_year ON afnc_item(year, item_type, verdict_en);
      CREATE INDEX IF NOT EXISTS ix_deb_year ON eu_debunk(year);
      CREATE INDEX IF NOT EXISTS ix_fo ON fotn_score(iso3, data_year);
    """)
    con.commit(); con.close()
    print("สร้าง", DB, "เรียบร้อย")

if __name__ == "__main__":
    main()
