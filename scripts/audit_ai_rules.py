"""Explain ambiguous reference rules without changing expected values or source files."""
import re,sys,json
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from app.queries import query,ROOT
from scripts.rules import MEDIA,MENTION,match_ai
f=query("SELECT post_id,date,title,clean_text FROM afnc_item WHERE item_type='Verdict' AND verdict_en IN ('Fake','Distorted')")
candidates=[]
for row in f.itertuples():
    current=match_ai(row.clean_text)
    relaxed=re.search(MEDIA.pattern,row.clean_text,re.I) or re.search(MENTION.pattern,row.clean_text,re.I)
    if relaxed and not current:candidates.append(dict(post_id=row.post_id,date=row.date,title=row.title,matched=relaxed.group(),snippet=row.clean_text[max(0,relaxed.start()-60):relaxed.end()+60]))
report={'strict_rule_count':sum(match_ai(v) is not None for v in f.clean_text),'case_insensitive_rule_count':sum(bool(re.search(MEDIA.pattern,t,re.I) or re.search(MENTION.pattern,t,re.I)) for t in f.clean_text),'reference_count':56,'extra_case_insensitive_candidates':candidates,'decision':'Keep explicit uppercase AI rule from document 02; do not turn all ai matches on merely to approach 56. Original reference script and match list were not provided. Retain failing reference checks and need-review status.'}
(ROOT/'data/ai_rule_audit.json').write_text(json.dumps(report,ensure_ascii=False,indent=2));print(json.dumps(report,ensure_ascii=False,indent=2))
