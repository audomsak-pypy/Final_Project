"""landing.py — หน้าเปิด (Landing Page) ตาม wireframe ใน 01 ข้อ 6.4"""
from dash import html, dcc

def layout():
    return html.Div([
        html.Div("ผู้จัดทำ: [ชื่อผู้จัดทำ]", className="landing-author"),
        html.H1("Adidur", className="landing-brand"),
        html.Div([
            html.Span("จริง", className="landing-word"),
            html.Span("หรือ", className="landing-word"),
            html.Span("เฟค", className="landing-word"),
        ], className="landing-word-group"),
        html.H2("AI ข่าวปลอม และภัยออนไลน์: มองโลก เปรียบเทียบไทย", className="landing-subheading"),
        html.P(
            "สำรวจแนวโน้มภัยออนไลน์และข้อมูลบิดเบือนจาก 5 แหล่งข้อมูลสถิติระดับโลกและระดับประเทศ "
            "บนแกนเวลาเดียวกัน พร้อมระบบตรวจสอบหลักฐานต้นฉบับรายข่าวและรายคดี",
            className="landing-desc"
        ),
        html.Div([
            dcc.Link("สำรวจ Dashboard →", href="/?tab=1", className="btn-cta-explore")
        ], className="landing-cta-wrapper"),
        html.Div([
            html.P("รายวิชา: Basic Programming for Data Scientist and Data Visualization", className="landing-course")
        ])
    ], className="landing-hero")
