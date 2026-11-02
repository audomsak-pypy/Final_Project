import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from app.state import display_date,be
from scripts.rules import THEMES
SCALE=['#FFF4D6','#FCD97A','#F5A23A','#DD5A1A','#A81F0C','#4A0A04']
COLORS=['#B8300E','#D9700C','#6B5244','#2E6B5C','#8D4718','#4A0A04','#B66338']
LABELS={'mention':'กล่าวถึง AI','media_evidence':'มีคำบ่งชี้ว่าใช้ AI สร้างสื่อ · ต้องตรวจสอบ'}
def theme(fig,dark=False):
    bg='#1E120C' if dark else '#FFFDF7';ink='#FBEFD9' if dark else '#1C0F08';line='#3B2719' if dark else '#E8D6BF'
    fig.update_layout(template='plotly_dark' if dark else 'plotly_white',paper_bgcolor=bg,plot_bgcolor=bg,font=dict(family='Sarabun, Tahoma, sans-serif',color=ink,size=12),margin=dict(l=48,r=25,t=32,b=65),height=390,autosize=True,clickmode='event+select',hovermode='closest',legend=dict(orientation='h',y=-.2,itemclick=False,itemdoubleclick=False),modebar=dict(bgcolor=bg),separators=',.')
    fig.update_xaxes(gridcolor=line,automargin=True);fig.update_yaxes(gridcolor=line,automargin=True)
    return fig

def timeline_index(s):
    if s.get('month'):return [s['month']]
    if s.get('year'):return [f"{s['year']}-{m:02d}" for m in range(1,13)]
    return list(range(s['y0'],s['y1']+1))
def counts(frame,s,coverage=(2015,2026)):
    idx=timeline_index(s);field='month' if s.get('year') or s.get('month') else 'year'
    grouped=frame.groupby(field).size() if not frame.empty else pd.Series(dtype=float)
    vals=[]
    for x in idx:
        yy=int(str(x)[:4]);end=str(x) if field=='month' else str(x)
        available=coverage[0]<=yy<=coverage[1]
        if coverage[1]==2026 and field=='month' and str(x)>'2026-10':available=False
        if coverage[1]==2023 and field=='month' and str(x)>'2023-08':available=False
        vals.append(int(grouped.get(x,0)) if available else None)
    return idx,vals

def timeseries(frame,s,name,dark=False,coverage=(2015,2026)):
    xs,ys=counts(frame,s,coverage)
    return theme(go.Figure(go.Scatter(x=[display_date(x) for x in xs],y=ys,mode='lines+markers',name=name,customdata=[[x] for x in xs],connectgaps=False,line=dict(color=COLORS[0],width=3))),dark)
def paired(ai,af,s,dark=False):
    fig=make_subplots(rows=2,cols=1,shared_xaxes=True,vertical_spacing=.14,subplot_titles=['AIID · เหตุการณ์ Deepfake','AFNC · โพสต์เกี่ยวกับ AI (ค่าขั้นต่ำ)'])
    xs,ys=counts(ai,s);labels=[display_date(x) for x in xs]
    fig.add_trace(go.Scatter(x=labels,y=ys,customdata=[[x] for x in xs],mode='lines+markers',name='Deepfake',line=dict(color=COLORS[0])),row=1,col=1)
    for n,level in enumerate(s['levels']):
        _,ys=counts(af[af.ai_level==level],s,(2019,2026))
        fig.add_trace(go.Scatter(x=labels,y=ys,customdata=[[x] for x in xs],mode='lines+markers',name=LABELS[level],line=dict(color=COLORS[n+1])),row=2,col=1)
    fig.update_xaxes(type='category');theme(fig,dark);fig.update_layout(height=530);return fig

def categories(frame,dark=False):
    g=frame.groupby('category_th').size().sort_values() if not frame.empty else pd.Series(dtype=int)
    return theme(go.Figure(go.Bar(x=g.values.tolist(),y=g.index.tolist(),orientation='h',customdata=[[x] for x in g.index],marker_color=COLORS[0])),dark)
def acsc_fig(panel,s,dark=False):
    fig=make_subplots(rows=2,cols=1,shared_xaxes=True,vertical_spacing=.14,subplot_titles=['ACSC · คดีที่แจ้ง','ACSC · ความเสียหาย (บาท)'])
    if not panel.empty:
        weekly=bool(s.get('acsc_month') or s.get('acsc_level')=='week')
        if weekly:
            p=panel[panel.month==s['acsc_month']] if s.get('acsc_month') else panel
            xs=[display_date(x) for x in p.week_start];raw=p.week_start.tolist();cs=p.cases.tolist();ls=p.loss_baht.tolist()
            colors=['#D9700C' if f=='suspect' else COLORS[0] for f in p.flag_type];symbols=['circle-open' if v=='rounded' else 'circle' for v in p.loss_precision]
        else:
            p=panel.groupby('month',as_index=False)[['cases','loss_baht']].sum(min_count=1)
            xs=[display_date(x) for x in p.month];raw=p.month.tolist();cs=p.cases.tolist();ls=p.loss_baht.tolist();colors=COLORS[0];symbols='circle'
        fig.add_trace(go.Bar(x=xs,y=cs,name='คดี',customdata=[[v,'week' if weekly else 'month'] for v in raw],marker_color=colors),row=1,col=1)
        fig.add_trace(go.Scatter(x=xs,y=ls,name='บาท · วงกลมกลวง = ปัดเลข (รายสัปดาห์)',customdata=[[v,'week' if weekly else 'month'] for v in raw],mode='lines+markers',connectgaps=False,line=dict(color=COLORS[1]),marker=dict(symbol=symbols,size=9,color=colors)),row=2,col=1)
    fig.update_xaxes(type='category');theme(fig,dark);fig.update_layout(height=540);return fig

def heatmap(frame,s,dark=False):
    years=list(range(s['y0'],s['y1']+1));ids=list(THEMES);z=[];texts=[];custom=[]
    for tid in ids:
        zz=[];tt=[];cc=[]
        for year in years:
            f=frame[(frame.year==year)&(frame.theme_id==tid)]
            if f.empty:zz.append(None);tt.append('ไม่มีข้อมูล');cc.append([year,tid,None,None])
            else:
                r=f.iloc[0];zz.append(r.pct);tt.append(f'{r.pct:.1f}%');cc.append([year,tid,int(r.n),int(r.denominator)])
        z.append(zz);texts.append(tt);custom.append(cc)
    labels=[THEMES[k][0]+(' · จัดกลุ่มต่างวิธี' if k in ('health','finance','politics') else '') for k in ids]
    fig=go.Figure(go.Heatmap(x=[be(x) for x in years],y=labels,z=z,zmin=0,zmax=100,colorscale=SCALE,customdata=custom,text=texts,texttemplate='%{text}',textfont=dict(color='#1C0F08'),hoverongaps=False,colorbar=dict(title='%',tickvals=[0,25,50,75,100],thickness=12),hovertemplate='%{y}<br>%{x}: %{customdata[2]} / %{customdata[3]} = %{z:.1f}%<extra></extra>'))
    # Missing values have their own hatch-like text; never borrow the zero color.
    for i,tid in enumerate(ids):
        for j,year in enumerate(years):
            if z[i][j] is None:fig.add_annotation(x=be(year),y=labels[i],text='╱ ไม่มีข้อมูล',showarrow=False,font=dict(size=10,color='#C9B09A' if dark else '#6B5244'))
            elif z[i][j]>=60:fig.add_annotation(x=be(year),y=labels[i],text=texts[i][j],showarrow=False,font=dict(color='white'))
    theme(fig,dark);fig.update_layout(height=450,margin=dict(l=20,r=20,t=25,b=55));return fig

def theme_line(e,a,s,dark=False):
    fig=go.Figure();years=list(range(s['y0'],s['y1']+1))
    for n,(name,f) in enumerate([('EUvsDisinfo',e),('AFNC',a)]):
        sel=f[f.theme_id==s['theme']].set_index('year')
        fig.add_trace(go.Scatter(x=[be(y) for y in years],y=[float(sel.loc[y,'pct']) if y in sel.index else None for y in years],customdata=[[y] for y in years],mode='lines+markers',connectgaps=False,name=name,line=dict(color=COLORS[n])))
    fig.update_yaxes(title='สัดส่วน (%)',range=[0,100]);return theme(fig,dark)
def stacked_categories(frame,s,dark=False):
    fig=go.Figure();field='month' if s.get('year') else 'year'
    if not frame.empty:
        for n,(cat,sub) in enumerate(frame.groupby('category_th')):
            g=sub.groupby(field).size();fig.add_trace(go.Bar(x=[display_date(v) for v in g.index],y=g.values.tolist(),name=cat,customdata=[[v,cat] for v in g.index],marker=dict(color=COLORS[n%len(COLORS)],pattern_shape=['','/','x','.'][n%4])))
    fig.update_layout(barmode='stack');return theme(fig,dark)
def ranking(frame,dark=False):
    f=frame.iloc[::-1];fig=go.Figure(go.Bar(x=f.total_score.tolist(),y=f.country_th.tolist(),orientation='h',customdata=[[v] for v in f.iso3],marker_color=[COLORS[0] if v=='THA' else COLORS[1] for v in f.iso3]))
    if not f.empty:fig.add_vline(x=float(f.total_score.median()),line_dash='dot',annotation_text=f'มัธยฐาน {f.total_score.median():g}')
    fig.update_xaxes(range=[0,100],title='คะแนนสูง = เสรีมาก');theme(fig,dark);fig.update_layout(height=max(400,min(1800,len(f)*28)));return fig

def score_components(frame,s,dark=False):
    fig=go.Figure();xs=[be(v) for v in frame.data_year] if s.get('iso3') else frame.country_th.tolist()
    for n,(col,label) in enumerate([('obstacles_to_access','การเข้าถึง /25'),('limits_on_content','เนื้อหา /35'),('violations_of_user_rights','สิทธิผู้ใช้ /40')]):
        fig.add_trace(go.Bar(x=xs,y=frame[col].tolist(),name=label,customdata=[[int(r.data_year),r.iso3,col] for r in frame.itertuples()],marker_color=COLORS[n]))
    fig.update_layout(barmode='stack');fig.update_yaxes(range=[0,100]);return theme(fig,dark)
def thai_pair(frame,dark=False):
    fig=make_subplots(rows=2,cols=1,shared_xaxes=True,vertical_spacing=.18,subplot_titles=['คะแนนเสรีภาพไทย /100','จำนวนคำตัดสิน Verdict ทั้งหมด AFNC'])
    for row,col,name in [(1,'total_score','คะแนนไทย'),(2,'afnc_verdicts','คำตัดสิน AFNC')]:
        fig.add_trace(go.Scatter(x=[be(v) for v in frame.data_year],y=frame[col].tolist(),customdata=[[int(v)] for v in frame.data_year],mode='lines+markers',name=name,line=dict(color=COLORS[row-1])),row=row,col=1)
    fig.update_xaxes(type='category');theme(fig,dark);fig.update_layout(height=520);return fig
