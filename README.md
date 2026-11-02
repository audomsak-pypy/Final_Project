# Adidur — จริงหรือเฟค
Dashboard ภาษาไทยสำหรับ Basic Programming for Data Scientist and Data Visualization: AI ข่าวปลอม และภัยออนไลน์ มองโลกเปรียบเทียบไทย ใช้ Dash + Plotly + SQLite และข้อมูลจริง 4 ไฟล์ใน Datasets

## เริ่มใช้งาน (Python 3.12)
```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python scripts/build_db.py --input Datasets --output data/adidur.db
.venv/bin/python scripts/expected_values.py data/adidur.db
.venv/bin/python -m pytest -q
.venv/bin/python -m app.app
```
เซิร์ฟเวอร์ใช้ port8050 (เปลี่ยนด้วย PORT) เปิดผ่านเบราว์เซอร์บนเครื่องที่รัน แอปสร้างฐานให้อัตโนมัติถ้ายังไม่มี ไม่ต้องเตรียม Excel ด้วยมือ ทุกคำสั่งรันจาก root repo หากเปิดจาก cloud นี้ต้องให้ execution tool อนุญาต socket/network ตาม policy ระบบ

**ผลทดสอบข้อมูลยังมี mismatch:** กฎ AI ที่ระบุชัดให้52 ไม่ตรง reference56 มี 4 regression assertions ไม่ผ่าน (E02 สองข้อ E03 E22) รายละเอียดใน docs/DECISIONS.md และ data/ai_rule_audit.json ไม่ใช่ข่าวปลอมทั้งหมดของสังคม และไม่ใช่การยืนยันว่า AI สร้างข่าวทั้งหมด

## ใช้งาน
หน้าเปิด → สำรวจ Dashboard → 4 แท็บ เลือกตัวกรองแล้วกดนำไปใช้ คลิกกราฟปี→เดือน→รายการ, ACSC เดือน→สัปดาห์, FOTN ประเทศ→ปี→องค์ประกอบ ปุ่มย้อนระดับและชิปลบไม่ล้างมิติอื่น ลิงก์ URL เก็บ state ของทุกแท็บ reload/back/forward ได้ ข่าวเด่นเปิดต้นทางหรือเน้นหลักฐาน ตารางแบ่งหน้า export ยังครบทุกแถว แท็บ4แยกต้นฉบับ/เตรียมแล้ว/ผลกรอง ไม่ส่งเนื้อหาข่าวทั้งฐานเข้า Store

โหมดสว่าง/มืดตามระบบ ฟอนต์ไทย local พร้อม OFL กราฟที่ตัวกรองไม่มีผลมีป้าย ข้อมูลไม่มีรายงานเป็น NULL ไม่แทนด้วย0 ปีแสดง พ.ศ. ฐาน/URL ค.ศ.

## ทดสอบและหลักฐาน
```bash
.venv/bin/python -m pytest -q --junitxml=data/pytest-results.xml
.venv/bin/python scripts/browser_check.py
.venv/bin/python scripts/audit_ai_rules.py
```
Browser check ต้องเปิดแอปก่อน ใช้ Chromium ผ่าน Playwright ตั้ง CHROMIUM_PATH ได้ ค่าเริ่มต้น /usr/bin/chromium ภาพและผลอยู่ tests/artifacts ไม่อ้างเป็นอุปกรณ์จริง ดู docs/TEST_REPORT.md

## Deploy บน Python server
เตรียม render.yaml สำหรับ Render Python Web Service เลือก branch SU และใช้ build/start command ในไฟล์ เซิร์ฟเวอร์ production ใช้ Gunicorn:
```bash
.venv/bin/gunicorn app.app:server --bind 0.0.0.0:8050 --workers 2
```
หากบริการกำหนด PORT ให้ใช้ `$PORT` แทน8050 ฐานสร้างระหว่าง build ไม่ต้องใช้ credential ของแหล่งข้อมูล Dashboard ไม่รองรับ GitHub Pages โดยตรงเพราะต้องมี Python server ยังไม่ deploy/push และการเข้าถึงคู่มือ Render ฉบับปัจจุบันถูก HTTP policy403 จึงต้องตรวจ https://render.com/docs/deploy-plotly-dash ก่อนเผยแพร่จริง

## เอกสารและผลลัพธ์
- docs/BRD.md และ docs/REQUIREMENTS_TRACEABILITY.md
- docs/DATA_PREPARATION.md และ docs/DECISIONS.md
- docs/TEST_REPORT.md, data/manifest.json, data/expected_results.json
- data/adidur.db และ data/processed/*.csv เป็นผลสร้างซ้ำในเครื่อง ไม่ commit ไฟล์ขนาดใหญ่
- docs/reference/ เก็บเอกสาร01–05 ที่ผู้ใช้ให้เพื่ออ้างอิง ไม่ใช่ข้อมูลภายนอกที่ใช้สั่งรันโดยอัตโนมัติ

## การเปลี่ยนแปลงจากสเปก
ใช้ Datasets ตามตำแหน่งจริงแทน data/raw; ไม่มี build_db/expected_values เดิม จึงสร้างใหม่; E02/E03/E22 ยังไม่ตรง reference ไม่แก้ข้อมูลต้นฉบับหรือ hardcode56; ไม่มี C3.5 เพราะส่วนเสริม; ใช้ผู้จัดทำ [ชื่อผู้จัดทำ]; ไม่มี full-content AFNC CSV/PDF จึงไม่ได้อ้างว่าอ่านแล้ว ไม่สรุปสาเหตุ การแพร่ข้ามประเทศ หรือเวลาที่ไทยตามหลังโลก
