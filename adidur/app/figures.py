"""figures.py — สร้างกราฟ Plotly พร้อม template สว่าง/มืดจาก token เดียวกันตาม 01 ข้อ 6.1"""
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
from app.state import to_be, format_month_be

THEME_TOKENS = {
    'light': {
        'bg': '#FFF8EC',
        'surface': '#FFFDF7',
        'ink': '#1C0F08',
        'muted': '#6B5244',
        'line': '#E8D6BF',
        'accent': '#B8300E',
        'accent_2': '#D9700C',
        'glow': '#F7C33C',
        'fake': '#B42318',
        'distorted': '#9E5205',
        'true': '#2E6B5C',
    },
    'dark': {
        'bg': '#120A06',
        'surface': '#1E120C',
        'ink': '#FBEFD9',
        'muted': '#C9B09A',
        'line': '#3B2719',
        'accent': '#F2643A',
        'accent_2': '#F5A23A',
        'glow': '#FCD25A',
        'fake': '#F0614A',
        'distorted': '#F2A040',
        'true': '#6FC2AA',
    }
}

HEATMAP_COLORSCALE = [
    [0.0, '#FFF4D6'],
    [0.2, '#FCD97A'],
    [0.4, '#F5A23A'],
    [0.6, '#DD5A1A'],
    [0.8, '#A81F0C'],
    [1.0, '#4A0A04'],
]

FONT_FAMILY = "'Noto Sans Thai', 'Sarabun', 'Leelawadee UI', Tahoma, sans-serif"

def get_theme(is_dark=False):
    return THEME_TOKENS['dark'] if is_dark else THEME_TOKENS['light']

def apply_base_layout(fig, is_dark=False, title="", height=360):
    t = get_theme(is_dark)
    fig.update_layout(
        title={
            'text': title,
            'font': {'size': 15, 'family': FONT_FAMILY, 'color': t['ink']},
            'x': 0.02, 'xanchor': 'left'
        },
        paper_bgcolor=t['surface'],
        plot_bgcolor=t['surface'],
        font={'family': FONT_FAMILY, 'color': t['ink'], 'size': 12},
        margin=dict(l=45, r=25, t=45, b=40),
        height=height,
        clickmode='event+select',
        hoverlabel=dict(
            bgcolor=t['surface'],
            font_size=12,
            font_family=FONT_FAMILY,
            font_color=t['ink'],
            bordercolor=t['line']
        )
    )
    fig.update_xaxes(
        gridcolor=t['line'],
        zerolinecolor=t['line'],
        tickfont=dict(color=t['muted'], size=11),
        title_font=dict(color=t['muted'], size=12)
    )
    fig.update_yaxes(
        gridcolor=t['line'],
        zerolinecolor=t['line'],
        tickfont=dict(color=t['muted'], size=11),
        title_font=dict(color=t['muted'], size=12)
    )
    return fig

# -------------------------------------------------------------------------
# TAB 1 FIGURES
# -------------------------------------------------------------------------

def make_c1_1_2_figure(df_aiid, df_afnc, is_dark=False, state=None):
    """C1.1 (บน: Deepfake AIID) และ C1.2 (ล่าง: ข่าว AI AFNC) แกน x ร่วมกัน"""
    t = get_theme(is_dark)
    fig = make_subplots(
        rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.14,
        subplot_titles=("C1.1 เหตุการณ์ Deepfake ทั่วโลก (AIID)",
                        "C1.2 ข่าวเท็จเกี่ยวกับ AI ในไทย (AFNC)")
    )
    is_month = state and state.get('level') == 'month'

    # AIID Trace
    if not df_aiid.empty:
        x_aiid = [format_month_be(x) if is_month else f"พ.ศ. {to_be(x)}" for x in df_aiid['t']]
        fig.add_trace(
            go.Scatter(
                x=x_aiid, y=df_aiid['n'],
                mode='lines+markers',
                name='Deepfake (AIID)',
                line=dict(color=t['accent'], width=2.5),
                marker=dict(size=6, color=t['accent']),
                customdata=df_aiid['t'],
                hovertemplate="ช่วง: %{x}<br>เหตุการณ์: %{y:,} เรื่อง<extra></extra>"
            ), row=1, col=1
        )

    # AFNC Traces: media_evidence vs mention
    if not df_afnc.empty:
        piv = df_afnc.pivot(index='t', columns='ai_level', values='n').fillna(0).reset_index()
        x_afnc = [format_month_be(x) if is_month else f"พ.ศ. {to_be(x)}" for x in piv['t']]

        if 'media_evidence' in piv.columns:
            fig.add_trace(
                go.Scatter(
                    x=x_afnc, y=piv['media_evidence'],
                    mode='lines+markers',
                    name='มีคำบ่งชี้ว่าใช้ AI สร้างสื่อ (ต้องตรวจสอบ)',
                    line=dict(color=t['fake'], width=2.5),
                    marker=dict(size=6, color=t['fake']),
                    customdata=piv['t'],
                    hovertemplate="%{x}<br>มีคำบ่งชี้ว่าใช้ AI: %{y:,} โพสต์<extra></extra>"
                ), row=2, col=1
            )
        if 'mention' in piv.columns:
            fig.add_trace(
                go.Scatter(
                    x=x_afnc, y=piv['mention'],
                    mode='lines+markers',
                    name='กล่าวถึง AI',
                    line=dict(color=t['accent_2'], width=2, dash='dot'),
                    marker=dict(size=5, color=t['accent_2']),
                    customdata=piv['t'],
                    hovertemplate="%{x}<br>กล่าวถึง AI: %{y:,} โพสต์<extra></extra>"
                ), row=2, col=1
            )

    apply_base_layout(fig, is_dark, height=450)
    fig.update_layout(legend=dict(orientation="h", yanchor="bottom", y=-0.22, xanchor="center", x=0.5))
    fig.update_yaxes(title_text="เหตุการณ์", row=1, col=1)
    fig.update_yaxes(title_text="โพสต์", row=2, col=1)
    return fig

def make_c1_3_figure(df_cat, is_dark=False):
    """C1.3 แท่งแนวนอน: หมวดของข่าว AI"""
    t = get_theme(is_dark)
    fig = go.Figure()
    if not df_cat.empty:
        df_sorted = df_cat.sort_values('n', ascending=True)
        fig.add_trace(
            go.Bar(
                x=df_sorted['n'],
                y=df_sorted['category_th'],
                orientation='h',
                marker=dict(color=t['accent_2']),
                hovertemplate="หมวด: %{y}<br>จำนวน: %{x} ข่าว<extra></extra>",
                customdata=df_sorted['category_th']
            )
        )
    apply_base_layout(fig, is_dark, title="C1.3 ข่าว AI แยกตามหมวด (AFNC)", height=320)
    fig.update_xaxes(title_text="จำนวนข่าว (โพสต์)")
    return fig

def make_c1_5_6_figure(df_acsc, is_dark=False, state=None):
    """C1.5 แท่งคดีรายสัปดาห์ + C1.6 เส้นความเสียหายรายสัปดาห์"""
    t = get_theme(is_dark)
    fig = make_subplots(
        rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.15,
        subplot_titles=("C1.5 จำนวนคดีออนไลน์รายสัปดาห์ (ACSC)",
                        "C1.6 มูลค่าความเสียหาย (บาท)")
    )
    if not df_acsc.empty:
        x_dates = df_acsc['week_start']
        # Bar: cases
        fig.add_trace(
            go.Bar(
                x=x_dates, y=df_acsc['cases'],
                name='คดี',
                marker_color=t['accent_2'],
                customdata=df_acsc['week_start'],
                hovertemplate="สัปดาห์เริ่ม: %{x}<br>คดี: %{y:,.0f} คดี<extra></extra>"
            ), row=1, col=1
        )
        # Line: loss
        symbols = ['circle-open' if p == 'rounded' else 'circle' for p in df_acsc['loss_precision']]
        colors = [t['fake'] if f == 'suspect' else t['accent'] for f in df_acsc['flag_type']]
        fig.add_trace(
            go.Scatter(
                x=x_dates, y=df_acsc['loss_baht'],
                mode='lines+markers',
                name='ความเสียหาย',
                line=dict(color=t['accent'], width=2),
                marker=dict(symbol=symbols, color=colors, size=7),
                customdata=df_acsc['week_start'],
                hovertemplate="สัปดาห์เริ่ม: %{x}<br>ความเสียหาย: %{y:,.0f} บาท<extra></extra>"
            ), row=2, col=1
        )

    apply_base_layout(fig, is_dark, height=450)
    fig.update_layout(showlegend=False)
    fig.update_yaxes(title_text="คดี", row=1, col=1)
    fig.update_yaxes(title_text="บาท", row=2, col=1)
    return fig

# -------------------------------------------------------------------------
# TAB 2 FIGURES
# -------------------------------------------------------------------------

def make_c2_1_figure(df_eu, is_dark=False):
    """C2.1 Heatmap EUvsDisinfo: ปี × ประเด็น สัดส่วน %"""
    t = get_theme(is_dark)
    if df_eu.empty:
        fig = go.Figure()
        apply_base_layout(fig, is_dark, title="C2.1 สัดส่วนประเด็นใน EUvsDisinfo (ไม่มีข้อมูล)", height=320)
        return fig

    piv = df_eu.pivot(index='theme_th', columns='year', values='pct').fillna(0)
    years_be = [f"พ.ศ. {to_be(y)}" for y in piv.columns]

    fig = go.Figure(data=go.Heatmap(
        z=piv.values,
        x=years_be,
        y=piv.index,
        colorscale=HEATMAP_COLORSCALE,
        zmin=0, zmax=100,
        colorbar=dict(title="% ของการหักล้าง", ticksuffix="%"),
        hovertemplate="ประเด็น: %{y}<br>ปี: %{x}<br>สัดส่วน: %{z:.1f}%<extra></extra>"
    ))
    apply_base_layout(fig, is_dark, title="C2.1 สัดส่วนประเด็นใน EUvsDisinfo (0–100%)", height=340)
    return fig

def make_c2_2_figure(df_af, is_dark=False):
    """C2.2 Heatmap AFNC: ปี × ประเด็น สัดส่วน %"""
    t = get_theme(is_dark)
    if df_af.empty:
        fig = go.Figure()
        apply_base_layout(fig, is_dark, title="C2.2 สัดส่วนประเด็นในข่าวเท็จ AFNC (ไม่มีข้อมูล)", height=320)
        return fig

    piv = df_af.pivot(index='theme_th', columns='year', values='pct').fillna(0)
    # Add note for themes categorized by category
    labels = []
    for th in piv.index:
        rule_sub = df_af[df_af['theme_th'] == th]
        is_cat = False
        if not rule_sub.empty and 'afnc_rule' in rule_sub.columns:
            rule_str = str(rule_sub['afnc_rule'].iloc[0])
            if 'category_en' in rule_str:
                is_cat = True
        labels.append(f"{th} (จัดตามหมวด)" if is_cat else th)

    years_be = [f"พ.ศ. {to_be(y)}" for y in piv.columns]

    fig = go.Figure(data=go.Heatmap(
        z=piv.values,
        x=years_be,
        y=labels,
        colorscale=HEATMAP_COLORSCALE,
        zmin=0, zmax=100,
        colorbar=dict(title="% ของข่าวเท็จ", ticksuffix="%"),
        hovertemplate="ประเด็น: %{y}<br>ปี: %{x}<br>สัดส่วน: %{z:.1f}%<extra></extra>"
    ))
    apply_base_layout(fig, is_dark, title="C2.2 สัดส่วนประเด็นในข่าวเท็จ AFNC (0–100%)", height=340)
    return fig

def make_c2_3_figure(df_comp, theme_th="โควิด-19", is_dark=False):
    """C2.3 เส้นสัดส่วนของประเด็นที่เลือก เทียบ EU vs AFNC"""
    t = get_theme(is_dark)
    fig = go.Figure()
    if not df_comp.empty:
        x_years = [f"พ.ศ. {to_be(y)}" for y in df_comp['year']]
        fig.add_trace(go.Scatter(
            x=x_years, y=df_comp['eu_pct'],
            mode='lines+markers', name='EUvsDisinfo (%)',
            line=dict(color=t['accent'], width=2.5),
            hovertemplate="%{x}<br>EUvsDisinfo: %{y:.1f}%<extra></extra>"
        ))
        fig.add_trace(go.Scatter(
            x=x_years, y=df_comp['afnc_pct'],
            mode='lines+markers', name='AFNC ข่าวเท็จ (%)',
            line=dict(color=t['accent_2'], width=2.5, dash='dash'),
            hovertemplate="%{x}<br>AFNC: %{y:.1f}%<extra></extra>"
        ))
    apply_base_layout(fig, is_dark, title=f"C2.3 สัดส่วนประเด็น '{theme_th}' เปรียบเทียบ 2 แหล่ง", height=300)
    fig.update_yaxes(title_text="สัดส่วน (%)", range=[0, max(100, (df_comp[['eu_pct','afnc_pct']].max().max() or 0) + 10)])
    fig.update_layout(legend=dict(orientation="h", y=-0.25, x=0.5, xanchor="center"))
    return fig

def make_c2_4_figure(df_cat, is_dark=False):
    """C2.4 แท่งซ้อน: ข่าวเท็จ AFNC ตามหมวด รายปี"""
    t = get_theme(is_dark)
    fig = go.Figure()
    if not df_cat.empty:
        cats = df_cat['category_th'].unique()
        years = sorted(df_cat['t'].unique())
        x_labels = [f"พ.ศ. {to_be(y)}" if len(str(y)) == 4 else format_month_be(y) for y in years]
        for cat in cats:
            sub = df_cat[df_cat['category_th'] == cat].set_index('t')
            y_vals = [sub.loc[y, 'n'] if y in sub.index else 0 for y in years]
            fig.add_trace(go.Bar(
                name=cat, x=x_labels, y=y_vals,
                hovertemplate=f"หมวด: {cat}<br>ปี: %{{x}}<br>จำนวน: %{{y:,}} ข่าว<extra></extra>"
            ))
    apply_base_layout(fig, is_dark, title="C2.4 ข่าวเท็จ AFNC แยกตามหมวด", height=320)
    fig.update_layout(barmode='stack', legend=dict(orientation="h", y=-0.3, x=0.5, xanchor="center", font=dict(size=10)))
    fig.update_yaxes(title_text="จำนวนข่าว (โพสต์)")
    return fig

def make_c2_5_figure(df_mis, is_dark=False):
    """C2.5 แผงบริบท AIID Misinformation รายปี"""
    t = get_theme(is_dark)
    fig = go.Figure()
    if not df_mis.empty:
        x_years = [f"พ.ศ. {to_be(y)}" for y in df_mis['year']]
        fig.add_trace(go.Scatter(
            x=x_years, y=df_mis['n'],
            mode='lines+markers', name='Misinformation',
            line=dict(color=t['fake'], width=2),
            hovertemplate="%{x}<br>เหตุการณ์: %{y} เรื่อง<extra></extra>"
        ))
    apply_base_layout(fig, is_dark, title="C2.5 บริบท AIID หมวด Misinformation (เหตุการณ์)", height=280)
    fig.update_yaxes(title_text="เหตุการณ์")
    return fig

# -------------------------------------------------------------------------
# TAB 3 FIGURES
# -------------------------------------------------------------------------

def make_c3_1_figure(df_c, is_dark=False):
    """C3.1 แท่งแนวนอนเทียบประเทศในกลุ่มที่เลือก"""
    t = get_theme(is_dark)
    fig = go.Figure()
    if not df_c.empty:
        df_sorted = df_c.sort_values('total_score', ascending=True)
        colors = [t['accent'] if iso == 'THA' else t['accent_2'] for iso in df_sorted['iso3']]
        fig.add_trace(go.Bar(
            x=df_sorted['total_score'],
            y=df_sorted['name'],
            orientation='h',
            marker_color=colors,
            customdata=df_sorted['iso3'],
            hovertemplate="ประเทศ: %{y}<br>คะแนนเสรีภาพ: %{x} / 100<extra></extra>"
        ))
        # Median line
        med = df_sorted['total_score'].median()
        fig.add_vline(x=med, line_dash="dash", line_color=t['muted'],
                      annotation_text=f"มัธยฐาน: {med:.1f}", annotation_position="top right")

    apply_base_layout(fig, is_dark, title="C3.1 คะแนนเสรีภาพอินเทอร์เน็ต (เต็ม 100)", height=320)
    fig.update_xaxes(range=[0, 100], title_text="คะแนนรวม")
    return fig

def make_c3_2_figure(df_comp, is_dark=False, level="group"):
    """C3.2 แท่งซ้อน 3 องค์ประกอบ (/25, /35, /40)"""
    t = get_theme(is_dark)
    fig = go.Figure()
    if not df_comp.empty:
        if level in ('country', 'year'):
            x_labels = [f"พ.ศ. {to_be(y)}" for y in df_comp['data_year']]
        else:
            x_labels = df_comp['name']

        fig.add_trace(go.Bar(
            name='การเข้าถึง (/25)', x=x_labels, y=df_comp['obstacles_to_access'],
            marker_color=t['glow'], hovertemplate="%{x}<br>การเข้าถึง: %{y} / 25<extra></extra>"
        ))
        fig.add_trace(go.Bar(
            name='การจำกัดเนื้อหา (/35)', x=x_labels, y=df_comp['limits_on_content'],
            marker_color=t['accent_2'], hovertemplate="%{x}<br>การจำกัดเนื้อหา: %{y} / 35<extra></extra>"
        ))
        fig.add_trace(go.Bar(
            name='การละเมิดสิทธิผู้ใช้ (/40)', x=x_labels, y=df_comp['violations_of_user_rights'],
            marker_color=t['accent'], hovertemplate="%{x}<br>การละเมิดสิทธิ: %{y} / 40<extra></extra>"
        ))
    apply_base_layout(fig, is_dark, title="C3.2 สัดส่วน 3 องค์ประกอบคะแนนเสรีภาพ", height=320)
    fig.update_layout(barmode='stack', legend=dict(orientation="h", y=-0.25, x=0.5, xanchor="center"))
    fig.update_yaxes(range=[0, 100], title_text="คะแนนรวม")
    return fig

def make_c3_3_figure(df_tha, is_dark=False):
    """C3.3 สองแผง 2562–2567: คะแนนไทย กับคำตัดสิน AFNC"""
    t = get_theme(is_dark)
    fig = make_subplots(
        rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.15,
        subplot_titles=("คะแนนเสรีภาพอินเทอร์เน็ตของไทย (เต็ม 100)",
                        "จำนวนคำตัดสินของ AFNC (เรื่อง)")
    )
    if not df_tha.empty:
        x_years = [f"พ.ศ. {to_be(y)}" for y in df_tha['data_year']]
        fig.add_trace(
            go.Scatter(
                x=x_years, y=df_tha['total_score'],
                mode='lines+markers', name='คะแนนไทย',
                line=dict(color=t['accent'], width=2.5),
                hovertemplate="%{x}<br>คะแนน: %{y} / 100<extra></extra>"
            ), row=1, col=1
        )
        fig.add_trace(
            go.Bar(
                x=x_years, y=df_tha['afnc_verdicts'],
                name='คำตัดสิน AFNC',
                marker_color=t['accent_2'],
                hovertemplate="%{x}<br>คำตัดสิน: %{y:,} เรื่อง<extra></extra>"
            ), row=2, col=1
        )
    apply_base_layout(fig, is_dark, title="C3.3 ไทยเท่านั้น · แสดงคู่กันเพื่อเป็นบริบท ไม่ได้วัดความสัมพันธ์", height=420)
    fig.update_layout(showlegend=False)
    fig.update_yaxes(range=[0, 100], row=1, col=1, title_text="คะแนน")
    fig.update_yaxes(row=2, col=1, title_text="คำตัดสิน")
    return fig

def make_c3_4_figure(df_eu_yr, is_dark=False):
    """C3.4 บริบท EUvsDisinfo: การหักล้างรายปี"""
    t = get_theme(is_dark)
    fig = go.Figure()
    if not df_eu_yr.empty:
        x_years = [f"พ.ศ. {to_be(y)}" for y in df_eu_yr['year']]
        fig.add_trace(go.Bar(
            x=x_years, y=df_eu_yr['debunks'],
            marker_color=t['muted'],
            hovertemplate="%{x}<br>การหักล้าง: %{y:,} เรื่อง<extra></extra>"
        ))
    apply_base_layout(fig, is_dark, title="C3.4 บริบทการหักล้าง EUvsDisinfo รายปี (ทั่วโลก)", height=280)
    fig.update_yaxes(title_text="การหักล้าง (เรื่อง)")
    return fig

def make_c3_5_figure(df_map, is_dark=False):
    """C3.5 แผนที่สถานะแต่ละประเทศ (Choropleth)"""
    t = get_theme(is_dark)
    fig = go.Figure()
    if not df_map.empty:
        fig.add_trace(go.Choropleth(
            locations=df_map['iso3'],
            locationmode='ISO-3',
            z=df_map['total_score'],
            text=df_map['country_th'],
            colorscale=HEATMAP_COLORSCALE,
            zmin=0, zmax=100,
            colorbar_title="คะแนนเสรีภาพ",
            hovertemplate="<b>%{text}</b> (%{locations})<br>คะแนน: %{z} / 100<extra></extra>"
        ))
    apply_base_layout(fig, is_dark, title="C3.5 แผนที่เสรีภาพอินเทอร์เน็ตทั่วโลก", height=380)
    fig.update_geos(
        showframe=False, showcoastlines=True,
        projection_type='equirectangular',
        bgcolor=t['surface'],
        coastlinecolor=t['line'],
        countrycolor=t['line']
    )
    return fig
