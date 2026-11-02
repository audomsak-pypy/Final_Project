# การเตรียมข้อมูล
รัน `.venv/bin/python scripts/build_db.py --input Datasets --output data/adidur.db` จาก repository root อ่าน Excel/CSV แล้วสร้างฐานใหม่แบบ atomic ไม่เขียนต้นฉบับ สร้าง CSV BOM ใน data/processed และ manifest เก็บ SHA schema null key duplicates จำนวนแถว coverage และ mapping ทุกรายงาน

AIID Incidents header=2; นับ incident_id ไม่ซ้ำ; deepfake จาก title/description/Implicated Systems; misinformation จาก Risk Domain. AFNC เก็บทุก post_id หัวข้อซ้ำไม่ลบ; Fake+Distorted Verdict เท่านั้นค้น AI; ลบ HTML URL เก็บ matched_terms snippet rule_version; data/ai_rule_audit.json ระบุผลตรวจความกำกวมและ candidate Ai. หากได้ Datasets/afnc_items.csv เต็ม pipeline เลือกใช้แทน Excel และเพิ่ม hash ลง manifest ต้องตรวจ expected อีกครั้ง

EU DD-MM-YYYY แยก 8522 debunks กับ 18249 articles และ 29842 keywords; theme ตาม dictionary 7 ประเด็น ไม่ทำให้ตัวนับฐานเพิ่มจาก join. FOTN 940 country-years 72 ประเทศ ตรวจ total=sum(25/35/40) แยก report edition. ACSC 48 รายงานและ weekly calendar409 แถว mapping ด้วย source_url มี 51 ช่องในช่วง ACSC และขาด3 ไม่เติม0. suspect เพียง1 แถว note3 แถวไม่ถูกตัดตาม toggle

ผล E01–E24 ที่มีในเอกสาร (ไม่มี E09/E16) อยู่ data/expected_results.json รัน `python scripts/expected_values.py data/adidur.db` ได้ exit1 เมื่อมี mismatch ห้ามมองว่า fail เป็นผ่าน ห้ามเปลี่ยน reference โดยไม่มีหลักฐาน ไฟล์ data/*.db และ CSV processed เป็นผลสร้างซ้ำและถูก gitignore แต่มีอยู่ในเครื่องและ archive ส่งมอบ
