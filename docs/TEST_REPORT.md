# รายงานทดสอบจริง
วันที่ 2 พ.ย. 2569 · Debian13 x86_64 · Python3.12.14 · Dash3.2.0 Plotly6.3.1 Pandas2.3.3 · branch SU

## คำสั่งและผล
| ชุด | คำสั่ง | Expected | Actual | สถานะ |
|---|---|---|---|---|
| Pipeline | `.venv/bin/python scripts/build_db.py --input Datasets --output data/adidur.db` | รันซ้ำไม่เปลี่ยนต้นฉบับ PK/FK ใช้ได้ | สร้างซ้ำหลายรอบ 8.0–8.4วินาที ทุก hash เดิม integrity/FKผ่าน | ผ่าน |
| Reference | `.venv/bin/python scripts/expected_values.py data/adidur.db` | 29 assertions E01–E24 ที่มีจริง | 25ผ่าน 4ไม่ผ่าน exit1 | ไม่ผ่านครบ |
| pytest | `.venv/bin/python -m pytest -q --junitxml=data/pytest-results.xml` | 57 tests | 53ผ่าน 4ไม่ผ่าน 1.66วินาที ไม่ skip/xfail | ไม่ผ่านครบ |
| App | `.venv/bin/python -m app.app` | ให้บริการจริง | health status ok, AFNC17726; browser เปิดครบ4แท็บ | ผ่าน |
| UI | `.venv/bin/python scripts/browser_check.py` | 3ขนาด ×2โหมด หน้าเปิด/แท็บ1 ไม่มี overflow | ดู tests/artifacts/browser-results.json และภาพ PNG รุ่นล่าสุด | ผลตาม JSON |

## การทดสอบข้อมูล
E01, E04–E08, E10–E15, E17–E21, E23–E24 และ E22 ฝั่ง AFNC false/AIID ผ่าน รวม25 assertions

**4 assertions ไม่ผ่าน:** E02 count/levels (52/27/25 vs56/33/23), E02 ปี2569 (40vs44), E03 หมวด (ความมั่นคง18vs20 รัฐบาล27vs29), E22 ข่าวAIช่วงเดียวกัน (40vs44) คง expected ตามเอกสาร ไม่แก้ให้ผ่าน รายละเอียดกฎและ candidate7 รายการใน data/ai_rule_audit.json ความต่างยังปิดไม่ได้จากเอกสารและไฟล์ที่ได้รับ ห้ามถือชุดนี้ผ่านครบ

## กติกาที่ผ่านใน pytest
- หมวด/ระดับ/แอบอ้างไม่เปลี่ยน ACSC/AIID; ประเทศอื่นไม่เปลี่ยน KPIไทย/บริบทไทย
- อันดับ71ประเทศหรืออาเซียน+รัสเซีย9ประเทศไม่ซ้ำ
- ACSC51ช่อง 48มีค่า3ว่าง; ตัด suspect เหลือ47รายงานและ4ช่องว่าง noteไม่หาย
- 8วัน source2026-05-30 อยู่ panel2026-05-31 ยอดเดือนตรง; ratioฐาน0ไม่หารศูนย์; coverageขาดต่างจาก0
- heatmap ตัวหารไม่เปลี่ยนตาม theme/category; EUปี2024+ไม่มีข้อมูล
- URL roundtrip และ parameterผิดรูปแบบ; drill up เก็บ filterอื่น
- AIไม่จับ Thailand/AIS/เอไอเอส/said/URL/HTML และเก็บหลักฐานใน positive cases
- ข่าว0–4รายการ/ยอดเสมอไม่ซ้ำ ใช้ post_idตัดสินลำดับ
- BOMและจำนวน exportครบแม้เลือกหน้าตาราง4; rawdownload hashตรง; exportallowlistกันไฟล์อื่น
- PK/FK/integrity/manifest hash และ renderทุกแท็บ

## Browser และหลักฐาน
ใช้ Chromium headless /usr/bin/chromium ผ่าน Playwright ไม่ใช่ iPadจริง เก็บหน้าเปิด/แท็บ1 ทุก 360/768/1280px ทั้งlight/dark และแท็บ2–4 desktop ใน tests/artifacts มีการคลิก SVG จุดจริงปี→เดือน→รายการ, ย้อน, เปลี่ยนแท็บ, reload, Back/Forward, reset, downloadจริงและตรวจBOM

รอบแรกพบ nestedchildren React errors แก้ flatten component แล้วไม่มีReact errors รอบถัดพบ Plotly axis scaling 2ข้อความ เพิ่มการระบุแกนcategoryและตรวจซ้ำ ผลสุดท้ายอ่าน JSON ไม่มีการลบconsoleเพื่อทำให้ผ่าน

## ประสิทธิภาพ
วัด Python server render ด้วย perf_counter หลังเพิ่ม index eu_article(debunk_id): แท็บ1~0.11–0.23s แท็บ2~0.21s แท็บ3~0.08–0.17s ก่อนเพิ่มindexแท็บ2~2s ค่าเหล่านี้ไม่ใช่เวลาเครือข่าย/ทุกเครื่อง เวลาโหลดจริงอยู่ browser-results.json build~8.4s เป้าหมาย BRD build<60s/render<2s รองรับในเครื่องนี้หลังเพิ่มindex

## ยังไม่ได้ตรวจหรือมีข้อจำกัด
- ยังไม่ทดสอบบนอุปกรณ์สัมผัส/iPadจริง, C3.5optional mapไม่พัฒนา
- Browser smoke ไม่ได้ยืนยันทุกชุดผสมของ filter/ทุกsource link/ทุกเส้นทาง ACSC/FOTN; SQLและrenderมี unit checks แต่ไม่แทน touchจริง
- ยังไม่ตรวจคำชี้แจงข่าวAIทุกชิ้นจากต้นทาง จึงคงต้องตรวจสอบ และยังไม่มี fullcontentCSV
- การเข้าถึงคู่มือ Render ปัจจุบันถูกHTTP403; ยังไม่deploy/push และไม่อ้างว่าสำเร็จ
- ไม่ถือว่า Definition of Done ทั้งหมดผ่าน เพราะมีreference mismatches4ข้อ ต้องเทียบสคริปต์/รายการ56เดิมก่อนยืนยันเลขอ้างอิง

## ผล browser สุดท้ายหลังแก้และแพ็ก
`python scripts/browser_check.py` exit0: **24/24 ผ่าน** viewport12กรณีและทุกแท็บแสดงกราฟครบ, year/monthdrill, tabstate, reload/history, reset, download, consoleไม่มีerror แก้ขั้นสุดท้ายให้ Graphมีheightชัดเจนและresponsiveauto ภาพทุกใบถูกสร้างใหม่จากรุ่นนี้ ดู tests/artifacts/browser-results.json ไม่รวมถึงอุปกรณ์จริง/ทุกcombination

pytestรอบสุดท้าย53ผ่าน4ไม่ผ่านใน1.66วินาที ไม่เปลี่ยนexpectedหรือdisableassertions สถานะreference mismatchยังคงเดิม
