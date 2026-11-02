"""Project-defined, versioned matching rules; never reinterpret in UI callbacks."""
import re
from html import unescape
RULE_VERSION = 'adidur-1.0'
DEEPFAKE = re.compile(r'deep\s?-?fake|voice[- ]clon|face[- ]?swap|synthetic (voice|video|media|image)', re.I)
AI_TOKEN = r'(?<![A-Za-z])AI(?![A-Za-z])|A\.I\.|artificial intelligence|ปัญญาประดิษฐ์|เอไอ(?!เอส)|ChatGPT|แชทจีพีที|chatbot|แชทบอท|generative'
MENTION = re.compile(AI_TOKEN)  # standalone uppercase AI; other named terms explicit
MEDIA = re.compile(r'deepfake|ดีปเฟก|ดีพเฟค|โคลนเสียง|ปลอมเสียง|เลียนเสียง|(?:สร้าง|ทำ|ตัดต่อ|ปลอม|ดัดแปลง|เจน).{0,12}(?:ด้วย|โดย|จาก|ใช้)\s*(?:AI|เอไอ(?!เอส)|ปัญญาประดิษฐ์)|(?<![A-Za-z])AI(?![A-Za-z])(?:สร้าง|ปลอม|ตัดต่อ|เจน)|(?:ภาพ|คลิป|วิดีโอ|เสียง).{0,10}(?:\bAI\b|เอไอ(?!เอส))')
THEMES = {
 'covid': ('โควิด-19','coronavirus|COVID-19|Sputnik V|pandemic','โควิด|covid|โคโรนา|ซิโนแวค|ซิโนฟาร์ม|ไฟเซอร์|โมเดอร์นา|แอสตร้า',None),
 'ukraine': ('สงครามยูเครน','War in Ukraine|Invasion of Ukraine|Ukraine|Eastern Ukraine|Donbas|Crimea|Euromaidan|Ukrainian statehood|Ukrainian disintegration|Volodymyr Zelensky|Minsk agreements|Abandoned Ukraine|DNR|LNR|DPR|Petro Poroshenko|Azov sea|Kerch','ยูเครน|เซเลนส|ไครเมีย|ดอนบาส|ukraine',None),
 'other_conflict': ('สงครามและความขัดแย้งอื่น','Syrian War|Military|Terrorism|Chemical weapons/attack|Nuclear issues|war crimes|Civil war|Daesh|Nagorno-Karabakh|Russo-Georgian War|Military exercise|Warmongering|War preparation','สงคราม|ปะทะ|อิสราเอล|ปาเลสไตน์|ฮามาส|ขีปนาวุธ|นิวเคลียร์|ก่อการร้าย',None),
 'health': ('สุขภาพ','vaccination|health|Biological weapons|Virus / bacteria threat|laboratory|Lugar Laboratory|food','', ['Health products']),
 'finance': ('การเงินและเศรษฐกิจ','Sanctions|Economic difficulties|economy|Energy|gas|Nord Stream 2|Trade','', ['Finance & stocks','Economy']),
 'politics': ('การเมือง การเลือกตั้ง และนโยบายรัฐ','Elections|Manipulated elections/referendum|election meddling|Referendum|US Presidential Election 2020|Protest|Coup|Colour revolutions|Democracy','', ['Government policy & news']),
 'conspiracy': ('ทฤษฎีสมคบคิด','Conspiracy theory|Secret elites / global elites|Deep state|George Soros','สมคบคิด|อิลลูมินาติ|ฟรีเมสัน',None),
}
COUNTRIES = {'THA':'ไทย','MYS':'มาเลเซีย','IDN':'อินโดนีเซีย','PHL':'ฟิลิปปินส์','VNM':'เวียดนาม','MMR':'เมียนมา','KHM':'กัมพูชา','SGP':'สิงคโปร์','RUS':'รัสเซีย'}
def clean(text):
    return re.sub(r'\s+', ' ', unescape(re.sub(r'<[^>]+>|https?://\S+|www\.\S+', ' ', str(text)))).strip()
def match_ai(text):
    text=clean(text)
    found=list(MEDIA.finditer(text)); level='media_evidence'
    if not found:
        found=list(MENTION.finditer(text));level='mention'
    if not found: return None
    first=found[0]
    return dict(ai_level=level, matched_terms='; '.join(dict.fromkeys(m.group() for m in found)), evidence_snippet=text[max(0,first.start()-60):first.end()+60], review_status='ต้องตรวจสอบ', impersonation_flag=int('แอบอ้าง' in text),rule_version=RULE_VERSION)
