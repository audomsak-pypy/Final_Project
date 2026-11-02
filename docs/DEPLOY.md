# เผยแพร่ Adidur เป็น Dashboard สาธารณะบน Render

แอปต้องใช้ Python server มีไฟล์ `render.yaml` บน branch **SU** ระบุแผน **Free** และ Gunicorn **1 worker** เพื่อจำกัดหน่วยความจำเมื่อส่งออกข้อมูลขนาดใหญ่

## วิธีผ่านบัญชี Render

1. เข้า [Render Dashboard](https://dashboard.render.com/) ด้วยบัญชีของคุณ
2. เลือก **New → Web Service** แล้วเชื่อม GitHub repository `audomsak-pypy/Final_Project` หากไม่พบ ให้ใช้ Public Git Repository URL `https://github.com/audomsak-pypy/Final_Project`
3. เลือก branch **SU** และ Language/Runtime **Python 3** ใช้ repository root
4. ตั้ง Build Command:
   ```bash
   pip install -r requirements.txt && python scripts/build_db.py --input Datasets --output data/adidur.db
   ```
5. ตั้ง Start Command:
   ```bash
   gunicorn app.app:server --bind 0.0.0.0:$PORT --workers 1 --timeout 120
   ```
6. เลือก instance **Free**, ตั้ง environment variable `PYTHON_VERSION=3.12.14` และ health-check path `/health`
7. กดสร้างบริการ รอ build/deploy สำเร็จ แล้วคัดลอก URL ที่ **Render ออกให้จริง** จากหน้าบริการ ห้ามเดาชื่อ `.onrender.com`
8. ตรวจ `/health` ว่าได้ `status=ok` และ `afnc_rows=17726`; เปิดหน้าแรก กดสำรวจ Dashboard แล้วทดสอบกราฟ/ดาวน์โหลดจาก URL สาธารณะ

หรือใช้ Blueprint จาก `render.yaml` ผ่าน **New → Blueprint** โดยต้องเลือก **SU** ก่อนอ่านไฟล์ configuration เพราะ branch อื่นอาจยังไม่มีไฟล์นี้

แผน Free อาจพักเมื่อไม่มีการใช้งาน การเปิดครั้งแรกหลังพักอาจใช้เวลา และการเริ่มบริการใหม่ไม่ควรพึ่งไฟล์ที่แก้หลัง build ฐานข้อมูลและ processed CSV ของโครงการสร้างระหว่าง build จึงสร้างซ้ำได้ ไม่ต้องใช้ persistent disk สำหรับข้อมูลอ่านอย่างเดียวนี้ ตรวจนโยบายและข้อจำกัดปัจจุบันในบัญชี Render ก่อนส่งลิงก์

## ให้ agent เผยแพร่ผ่าน API

ไม่มี Render credentials ในเครื่องเริ่มต้น การมีบัญชี Render อย่างเดียวไม่ได้ให้สิทธิ์ API กับ agent

- สร้าง API key ใน Render Account settings
- ใส่ผ่านช่องลับ `RENDER_API_KEY` ใน Environment settings ของ cloud นี้เท่านั้น ไม่ส่งค่าในแชต ไม่ใส่ใน GitHub และไม่ใส่ใน environment ของเว็บ Adidur (ตัวเว็บไม่ใช้ key นี้)
- ข้อกำหนดช่องลับผูกเฉพาะ `api.render.com` เพื่อใช้ REST API และเพิ่มโดเมนนี้ใน network draft แล้ว ต้องบันทึก/publish ตามหน้าตั้งค่าจึงจะใช้งานได้ การ save draft ยังไม่สร้างบริการหรือเผยแพร่เว็บไซต์
- หลังสิทธิ์พร้อม ให้ตรวจบัญชี/workspace และบริการเดิมก่อนสร้าง เพื่อไม่สร้างบริการซ้ำ ใช้เฉพาะแผน Free ตาม configuration

## การตรวจและสถานะ

ทดสอบ Gunicorn ภายในเครื่องแล้ว: `/health` ตอบข้อมูลจริง และ Dashboard แท็บ1แสดง3กราฟ ไม่มี page errors ใน Chromium ของการตรวจนี้ การทดสอบภายในยังไม่ยืนยัน public deployment

ยังไม่ได้รับ Render service URL หรือสิทธิ์ API จึงยังไม่อ้างว่ามี Dashboard สาธารณะสำเร็จ ต้องยืนยัน URL หลัง Render สร้างจริง

ผล regression เดิมยังมี4assertionsเกี่ยวกับข่าวAIไม่ตรงค่าอ้างอิง ดู [TEST_REPORT.md](TEST_REPORT.md) ไม่ถือว่าการ deploy ทำให้ความต่างนี้หายไป

## คำสั่ง API ที่เตรียมไว้

สคริปต์ตรวจ schema จาก [official Render CLI](https://github.com/render-oss/cli/blob/ccd220c88de25433f1e77fe1e66a64adefa41c43/pkg/client/types_gen.go) commit `ccd220c88de25433f1e77fe1e66a64adefa41c43` ใช้ REST endpoint `https://api.render.com/v1` โดยส่ง key ผ่าน Authorization header เท่านั้น ไม่บันทึกลงไฟล์ ไม่แสดง headers หรือ response ดิบที่อาจมีข้อมูลอ่อนไหว

```bash
# ตรวจ request ที่ตั้งใจใช้ ไม่เรียก API หรือใช้ credential
.venv/bin/python scripts/deploy_render.py --plan

# หลังใส่ key ในช่องลับและ runtime พร้อม
.venv/bin/python scripts/deploy_render.py --list-owners

# ถ้า key เห็น workspace เดียว เลือกให้อัตโนมัติ; ถ้ามีหลายที่ต้องระบุ --owner-id
.venv/bin/python scripts/deploy_render.py --create

# ตรวจสถานะด้วย service ID ที่ Render ตอบกลับจริง
.venv/bin/python scripts/deploy_render.py --status srv-REPLACEWITHACTUALID
```

Service ID ของ Render ใช้รูปแบบ `srv-...` ให้แทนตัวอย่างด้วย ID จริง ไม่ใช้ข้อความ placeholder ข้างต้น หากมีหลาย workspace ให้ใช้ `--create --owner-id <ID จาก list-owners>`

สคริปต์ค้นบริการ repository/branch เดิมก่อน ไม่สร้างซ้ำ ไม่เปลี่ยนบริการแบบเสียเงิน ไม่ส่ง Render key เข้า environment ของ Dashboard และไม่ถือว่า API สร้างบริการแล้วเท่ากับเว็บใช้งานได้ ต้องรอ deploy status `live` และตรวจ URL จริงอีกครั้ง

Unit tests ของ payload/free plan, credential missing, reuse, duplicate และ paid-plan protection ผ่าน6ข้อ เป็นการทดสอบด้วย fake API; ยังไม่ได้ทดสอบการสร้างบริการจริงเพราะ key ยังไม่พร้อม
