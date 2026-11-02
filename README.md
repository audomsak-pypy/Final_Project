# Adidur — จริงหรือเฟค

แดชบอร์ดภาษาไทยเรื่อง **AI ข่าวปลอม และภัยออนไลน์: มองโลก เปรียบเทียบไทย**
รายวิชา Basic Programming for Data Scientist and Data Visualization (Final Project กลุ่ม 7)

สร้างด้วย Python (Dash) + Plotly + SQLite ใช้ข้อมูลจริง 5 ชุด วางบนแกนเวลาเดียวกัน กดดูหลักฐานต้นทางได้ และไม่สรุปเกินข้อมูล

## ตอบคำถามอะไรได้บ้าง

| แท็บ | คำถาม | แหล่งข้อมูล |
|---|---|---|
| 1 · AI และภัยออนไลน์ | Deepfake ที่บันทึกทั่วโลก ข่าวเท็จเกี่ยวกับ AI ในไทย และคดีหลอกลวงออนไลน์ ช่วงเดียวกันเป็นอย่างไร | AIID, AFNC, ACSC |
| 2 · ประเด็นต่างประเทศ | ประเด็นใดปรากฏร่วมกันใน EUvsDisinfo และข่าวเท็จของ AFNC | EUvsDisinfo, AFNC, AIID |
| 3 · เสรีภาพอินเทอร์เน็ต | ไทยมีคะแนนอยู่ตรงไหนเมื่อเทียบประเทศอื่น | Freedom on the Net, AFNC, EUvsDisinfo |

จุดเด่น:

- **กราฟเชื่อมกันจริง** แตะกราฟใดก็ได้ (ปี เดือน สัปดาห์ หมวด ประเด็น ประเทศ) แล้ว KPI กราฟ การ์ดข่าว และตารางหลักฐานทั้งแท็บเปลี่ยนตาม พร้อม breadcrumb และปุ่มย้อนระดับ
- **แชร์ลิงก์ได้** state ของแต่ละแท็บถูกเขียนลง URL เช่น `/?tab=1&level=month&year=2026`
- **โหมดสว่าง/มืด** ตามการตั้งค่าเครื่อง และรองรับมือถือ (360 px) ถึงจอใหญ่
- **ไม่สรุปเกินข้อมูล** ตัวกรองที่ไม่มีตัวเชื่อมระหว่างชุดข้อมูล (เช่น หมวดข่าว AI กับคดี ACSC) จะไม่กรองข้ามกัน และข้อจำกัดของข้อมูลพับไว้ในทุกแท็บ
- ดาวน์โหลด CSV (UTF-8 พร้อม BOM) ตามตัวกรองปัจจุบันท้ายแต่ละแท็บ

## ชุดข้อมูล

| ชุด | ผู้จัดทำ | 1 แถว = |
|---|---|---|
| AIID | Responsible AI Collaborative | เหตุการณ์ AI 1 เรื่อง |
| Freedom on the Net | Freedom House (ผ่าน QoG, ม.ค. 2026) | ประเทศ × ปีข้อมูล |
| EUvsDisinfo | EEAS (EU), Leite et al. (2024) | บทความที่ผูกกับการหักล้าง |
| AFNC | ศูนย์ต่อต้านข่าวปลอม กระทรวงดิจิทัลฯ | โพสต์ 1 ชิ้น |
| ACSC | ศูนย์ต่อต้านการฉ้อโกงออนไลน์ สำนักงานตำรวจแห่งชาติ | การแถลง 1 สัปดาห์ |

ไฟล์ต้นฉบับอยู่ใน [Datasets/](Datasets) (สำเนาที่ใช้สร้างฐานข้อมูลอยู่ที่ `adidur/data/raw/`) รายละเอียดและข้อจำกัดอยู่ใน [02_DATASET_DESCRIPTIONS.md](02_DATASET_DESCRIPTIONS.md)

ข้อควรระวัง: จำนวนข่าวเท็จที่เกี่ยวกับ AI (56 โพสต์) นับจากเนื้อหาที่ถูกตัดความยาวในไฟล์ จึงเป็นค่าขั้นต่ำ และทุกรายการยังต้องตรวจสอบ

## โครงสร้างโปรเจกต์

```text
.
├── 01_PROJECT_SPEC.md          สเปกโครงงาน คำถาม requirements ดีไซน์
├── 02_DATASET_DESCRIPTIONS.md  ความหมายข้อมูล เกณฑ์ข่าว AI พจนานุกรมประเด็น
├── 03_DATABASE_SCHEMA.md       ตาราง SQLite SQL ของทุกกราฟ ค่าคาดหวังสำหรับทดสอบ
├── 04_HANDOFF_PROMPT.md        brief สำหรับสร้างแอป
├── Datasets/                   ไฟล์ข้อมูลต้นฉบับ 4 ไฟล์
├── render.yaml                 ตั้งค่า deploy บน Render
└── adidur/                     แอปแดชบอร์ด
    ├── app/                    โค้ด Dash (state, queries, figures, pages, components, assets)
    ├── scripts/                build_db.py สร้างฐานข้อมูล, expected_values.py ค่าคาดหวัง
    ├── data/                   adidur.db และข้อมูลดิบ
    └── tests/                  pytest (17 รายการ)
```

รายละเอียดการทำงานภายในแอปอยู่ที่ [adidur/README.md](adidur/README.md)

## รันบนเครื่อง

ต้องใช้ Python 3.11 ขึ้นไป

```bash
cd adidur
pip install -r requirements.txt
python -m app.app
```

เปิด http://127.0.0.1:8050 (ฐานข้อมูล `adidur/data/adidur.db` อยู่ใน repo แล้ว)

สร้างฐานข้อมูลใหม่จากไฟล์ต้นฉบับและรันทดสอบ:

```bash
cd adidur
python scripts/build_db.py data/raw data/adidur.db
python scripts/expected_values.py data/adidur.db
pytest -q
```

## Deploy

Dash ต้องมีเซิร์ฟเวอร์ Python จึงขึ้น GitHub Pages ไม่ได้ repo นี้เตรียมไฟล์ [render.yaml](render.yaml) สำหรับ [Render](https://render.com) ไว้แล้ว

1. เข้า Render › **New** › **Blueprint** แล้วเลือก repo นี้ (branch `main`)
2. Render อ่าน `render.yaml` และสร้างบริการ `adidur` ให้เอง (แผน Free)
3. รอ build เสร็จ จะได้ลิงก์ `https://adidur-xxxx.onrender.com`

ตั้งค่าที่ใช้: root directory `adidur`, build `pip install -r requirements.txt`, start `gunicorn app.app:server --workers 2 --timeout 120`, Python 3.12 แผน Free จะหลับเมื่อไม่มีคนใช้ ครั้งแรกที่เปิดอาจรอประมาณ 1 นาที

## ผลการตรวจ

- `pytest -q` ผ่าน 17 รายการ: ค่า E01–E19 ตรงกับ `03_DATABASE_SCHEMA.md` และกติกาของสเปก (ตัวกรองข่าว AI ไม่เปลี่ยนค่า ACSC, ACSC 51 สัปดาห์ ว่าง 3, CSV มี BOM, state <-> URL)
- ทดสอบคลิกใน Chrome: drill ปี › เดือน › สัปดาห์ ทุกแท็บ และไม่มีการเลื่อนแนวนอนที่ 360 px

## การเปลี่ยนแปลงจากสเปกเดิม

- ตัดแท็บ "แหล่งข้อมูลและดาวน์โหลด" และแผนที่สถานะประเทศ ตามผลการทดสอบกับผู้ใช้ (ดาวน์โหลดย้ายไปท้ายแต่ละแท็บ)
- ช่วงเริ่มต้นแท็บ 2 เป็น พ.ศ. 2563–2565 เพราะ AFNC ปี 2562 ไม่ใช่ปีเต็ม
- ฐานข้อมูลเพิ่มดัชนีและตาราง `eu_debunk_link` เพื่อความเร็ว ไม่เปลี่ยนค่าที่นับ

## ผู้จัดทำ

[ชื่อผู้จัดทำ] · Final Group 7
