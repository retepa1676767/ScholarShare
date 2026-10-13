"""Render the assignment-2 activity/state models as submission PNGs.

The editable Mermaid definitions alongside the PNGs are the semantic source.
This script lays out the same transitions for print-friendly review.
"""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import math

HERE = Path(__file__).resolve().parent
OUT_DIR = HERE.parent / '02-模型图' / '流程与状态图'
OUT_DIR.mkdir(parents=True, exist_ok=True)
FONT_PATH = '/System/Library/Fonts/Hiragino Sans GB.ttc'
FONT = ImageFont.truetype(FONT_PATH, 28)
SMALL = ImageFont.truetype(FONT_PATH, 22)
TITLE = ImageFont.truetype(FONT_PATH, 48)
BOLD = ImageFont.truetype(FONT_PATH, 31)
INK = '#24364b'
LINE = '#43637d'
BLUE = '#eaf3fb'
GREEN = '#e8f6ee'
AMBER = '#fff2dc'
RED = '#fbe9e7'
WHITE = '#ffffff'
BG = '#f7fafc'


def canvas(size, title, subtitle):
    im = Image.new('RGB', size, BG)
    d = ImageDraw.Draw(im)
    d.text((size[0]//2, 58), title, font=TITLE, fill=INK, anchor='mm')
    d.text((size[0]//2, 112), subtitle, font=SMALL, fill='#587087', anchor='mm')
    d.line((65, 145, size[0]-65, 145), fill='#c9d9e5', width=3)
    return im, d


def box(d, cx, cy, w, h, lines, fill=BLUE, radius=23, font=FONT):
    x0,y0,x1,y1 = cx-w//2,cy-h//2,cx+w//2,cy+h//2
    d.rounded_rectangle((x0,y0,x1,y1), radius=radius, fill=fill, outline=LINE, width=3)
    for i,line in enumerate(lines):
        d.text((cx, cy+(i-(len(lines)-1)/2)*38), line, font=font, fill=INK, anchor='mm')


def decision(d,cx,cy,w,h,lines):
    d.polygon([(cx,cy-h//2),(cx+w//2,cy),(cx,cy+h//2),(cx-w//2,cy)], fill=AMBER)
    d.line([(cx,cy-h//2),(cx+w//2,cy),(cx,cy+h//2),(cx-w//2,cy),(cx,cy-h//2)], fill=LINE,width=3,joint='curve')
    for i,line in enumerate(lines):
        d.text((cx,cy+(i-(len(lines)-1)/2)*34),line,font=SMALL,fill=INK,anchor='mm')


def arrow(d, points, label=None, label_at=None, color=LINE, width=4):
    d.line(points, fill=color, width=width, joint='curve')
    x0,y0=points[-2]; x1,y1=points[-1]
    a=math.atan2(y1-y0,x1-x0); L=18; ang=.48
    p1=(x1-L*math.cos(a-ang),y1-L*math.sin(a-ang))
    p2=(x1-L*math.cos(a+ang),y1-L*math.sin(a+ang))
    d.polygon([(x1,y1),p1,p2],fill=color)
    if label:
        lx,ly=label_at or ((x0+x1)//2,(y0+y1)//2)
        b=d.textbbox((lx,ly),label,font=SMALL,anchor='mm')
        d.rounded_rectangle((b[0]-8,b[1]-4,b[2]+8,b[3]+4),radius=7,fill=BG)
        d.text((lx,ly),label,font=SMALL,fill=color,anchor='mm')


def state(d,cx,cy,lines,fill=BLUE,w=300,h=100):
    box(d,cx,cy,w,h,lines,fill=fill)


def activity():
    im,d=canvas((2180,2560),'门户认领审核活动图','基于 B1 SRS §2.2 / FR-27 · A4 UC02—UC03')
    lanes=[(80,700,'申请人'),(730,1430,'平台系统'),(1460,2100,'授权管理员')]
    for x0,x1,name in lanes:
        d.rounded_rectangle((x0,175,x1,2460),radius=20,fill=WHITE,outline='#d4e2eb',width=2)
        d.rounded_rectangle((x0,175,x1,250),radius=20,fill='#dcebf7')
        d.text(((x0+x1)//2,213),name,font=BOLD,fill=INK,anchor='mm')
    # Edges first, under nodes.
    arrow(d,[(390,310),(390,350)])
    arrow(d,[(390,450),(390,510)])
    arrow(d,[(545,565),(935,565)])
    arrow(d,[(1090,640),(1090,710)],'通过',(1155,675))
    arrow(d,[(950,565),(670,565),(670,700),(390,700)],'不通过',(600,650))
    arrow(d,[(390,650),(390,600)],'修正后重交',(300,625))
    arrow(d,[(1090,810),(1090,875)])
    arrow(d,[(1090,975),(1090,1030)])
    arrow(d,[(1260,1100),(2040,1100),(2040,1875),(1945,1875)],'否：证据不足',(1530,1065))
    arrow(d,[(1090,1170),(1090,1255)],'是',(1140,1215))
    arrow(d,[(1255,1320),(1450,1320),(1450,1220),(1575,1220)],'是：存在争议',(1360,1280))
    arrow(d,[(1090,1385),(1090,1420),(1575,1420)],'否',(1360,1380))
    arrow(d,[(1925,1220),(1990,1220),(1990,1780),(1750,1780),(1750,1825)],'暂停直接通过',(1880,1510))
    arrow(d,[(1750,1470),(1750,1550)])
    arrow(d,[(1600,1630),(1090,1630),(1090,1825)],'批准',(1280,1580))
    arrow(d,[(1750,1710),(1750,1825)],'驳回',(1840,1760))
    arrow(d,[(1090,1925),(1090,2080),(390,2080),(390,2150)])
    arrow(d,[(1750,1925),(1750,2080),(390,2080),(390,2150)])
    arrow(d,[(390,2250),(390,2320)])
    # Nodes.
    d.ellipse((367,267,413,313),fill=INK)
    box(d,390,400,310,100,['定位本人门户'])
    box(d,390,560,310,100,['填写材料并提交'])
    box(d,390,700,310,100,['按错误提示修正'],fill=AMBER)
    decision(d,1090,565,340,150,['必填/格式/重复','校验通过？'])
    box(d,1090,760,340,100,['保存编号与快照','状态 submitted'])
    box(d,1090,925,340,100,['核验证据','状态 verifying'])
    decision(d,1090,1100,340,140,['证据充分且','归属可判定？'])
    decision(d,1090,1320,330,130,['已有管理人','或并发争议？'])
    box(d,1750,1220,350,100,['转争议核验','不得覆盖原管理人'],fill=AMBER)
    box(d,1750,1420,350,100,['审核当前申请版本'])
    decision(d,1750,1630,310,150,['批准？'])
    box(d,1090,1875,420,100,['原子记录 approved','授予目标门户权限'],fill=GREEN)
    box(d,1750,1875,390,100,['记录 rejected','说明理由并允许补证'],fill=RED)
    box(d,390,2200,390,100,['通知申请人结果'])
    d.ellipse((364,2320,416,2372),outline=INK,width=4)
    d.ellipse((375,2331,405,2361),fill=INK)
    d.text((1090,2470),'同名仅生成候选；审核版本、理由、操作者和时间均须留痕。',font=SMALL,fill='#587087',anchor='mm')
    im.save(OUT_DIR/'A1-认领审核活动图.png',dpi=(200,200))


def collection():
    im,d=canvas((2200,1450),'数据采集任务状态图','基于 B1 SRS §2.2 / FR-25—26 · A4 UC01')
    # Edges and transition labels.
    arrow(d,[(150,350),(315,350)],'创建合法任务',(230,305))
    arrow(d,[(615,350),(855,350)],'启动/调度',(735,305))
    arrow(d,[(1155,315),(1505,245)],'批次完成',(1340,225))
    arrow(d,[(1155,385),(1505,555)],'执行失败',(1335,500))
    arrow(d,[(900,405),(695,405),(695,875),(615,875)],'管理员停止',(580,660))
    arrow(d,[(1505,610),(1155,855)],'允许重试，次数 < 3',(1390,750))
    arrow(d,[(1005,825),(1005,405)],'退避结束/幂等续跑',(1180,650))
    # Terminal circles.
    d.ellipse((100,325,150,375),fill=INK)
    state(d,465,350,['queued','待执行'])
    state(d,1005,350,['running','运行中'])
    state(d,1655,245,['succeeded','成功'],fill=GREEN)
    state(d,1655,560,['failed','失败'],fill=RED)
    state(d,1005,875,['retrying','重试中'],fill=AMBER)
    state(d,465,875,['stopped','已停止'],fill=AMBER)
    arrow(d,[(855,875),(615,875)],'管理员停止',(735,925))
    arrow(d,[(1805,560),(1980,560)],'放弃或达到上限',(1900,515))
    arrow(d,[(1805,245),(1980,245)])
    arrow(d,[(465,925),(465,1060)])
    for x,y in ((1980,560),(1980,245),(465,1060)):
        d.ellipse((x-16,y-16,x+16,y+16),outline=INK,width=3)
        d.ellipse((x-9,y-9,x+9,y+9),fill=INK)
    box(d,1100,1280,1850,130,['失败保留错误与批次计数；合法零条可为成功，但不能把失败显示为零结果。','初版最多重试 3 次；停止、重试均不得重复创建已入库数据。'],fill=WHITE,font=SMALL)
    im.save(OUT_DIR/'A1-采集任务状态图.png',dpi=(200,200))


def claim():
    im,d=canvas((2200,1530),'门户认领申请状态图','基于 B1 SRS §2.2 / FR-27 · A4 UC02—UC03')
    arrow(d,[(150,350),(350,350)],'保存申请与证据',(250,305))
    arrow(d,[(650,350),(870,350)],'进入核验队列',(760,305))
    arrow(d,[(1170,320),(1510,220)],'批准并授权',(1345,225))
    arrow(d,[(1170,390),(1510,530)],'驳回并说明理由',(1350,500))
    arrow(d,[(500,405),(500,930)],'申请人取消',(365,665))
    arrow(d,[(1020,405),(1020,930),(650,930)],'终局前取消',(850,870))
    arrow(d,[(1810,220),(2000,220),(2000,920),(1810,920)],'批准后争议/撤销错误关联',(1980,600))
    arrow(d,[(1660,585),(1660,700),(220,700),(220,350),(350,350)],'补证重提：新轮次',(900,660))
    d.ellipse((100,325,150,375),fill=INK)
    state(d,500,350,['submitted','已提交'])
    state(d,1020,350,['verifying','核验中'])
    state(d,1660,220,['approved','已批准'],fill=GREEN)
    state(d,1660,530,['rejected','已驳回'],fill=RED)
    state(d,500,980,['cancelled','已取消'],fill=AMBER)
    state(d,1660,920,['disputed','争议中'],fill=AMBER)
    arrow(d,[(500,1030),(500,1120)])
    d.ellipse((484,1104,516,1136),outline=INK,width=3)
    d.ellipse((491,1111,509,1129),fill=INK)
    box(d,1100,1240,1890,180,['批准前不得授予门户管理权；同名匹配不自动通过。','驳回补证作为新处理轮次；B1 未定义 disputed 后续恢复转移。','每次状态变化均保存版本、审核人、时间、理由和权限变更审计。'],fill=WHITE,font=SMALL)
    im.save(OUT_DIR/'A1-认领申请状态图.png',dpi=(200,200))


if __name__ == '__main__':
    activity(); collection(); claim()
    print('rendered 3 diagrams')
