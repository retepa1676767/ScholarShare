# -*- coding: utf-8 -*-
"""A1 问卷统计分析 + 图表生成（一键复现）

用法：
    python A1-统计分析脚本.py

输入：同目录下的 A1-问卷原始数据.csv（腾讯问卷导出件）
输出：同目录下 统计明细.txt、图表/*.png

配色遵循 dataviz 规范：单系列 = slot1 blue #2a78d6，浅灰收敛网格，发丝轴线。
注：腾讯问卷导出件为 UTF-8 with BOM；第 12、23 列带前导制表符，读取时需 strip。
"""
import csv, io, os, math
from collections import Counter
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import font_manager

SRC = 'A1-问卷原始数据.csv'
OUTDIR = '图表'

# ---------- 中文字体 ----------
for f in ['C:/Windows/Fonts/msyh.ttc', 'C:/Windows/Fonts/simhei.ttf',
          'C:/Windows/Fonts/simsun.ttc']:
    if os.path.exists(f):
        font_manager.fontManager.addfont(f)
plt.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei', 'SimSun']
plt.rcParams['axes.unicode_minus'] = False

# ---------- 配色（dataviz 参考调色板 · light）----------
SERIES, SURFACE = '#2a78d6', '#fcfcfb'
INK1, INK2, MUTED = '#0b0b0b', '#52514e', '#898781'
GRID, BASE = '#e1e0d9', '#c3c2b7'

os.makedirs(OUTDIR, exist_ok=True)

# ---------- 读取 ----------
rows = list(csv.reader(io.StringIO(open(SRC, encoding='utf-8-sig').read())))
hdr, data = rows[0], rows[1:]
s = lambda x: x.strip()
N = len(data)

PLAT = [('ResearchGate', 5), ('Google Scholar', 6), ('CNKI/知网', 7),
        ('GitHub（代码/数据）', 8), ('arXiv', 9), ('其他', 10)]
FN = [('文献检索与下载', 13), ('成果发布与共享', 14), ('学术社交与关注', 15),
      ('引用与影响力统计', 16), ('问答与讨论区', 17)]
PR = [('操作简洁易用', 18), ('资源丰富全面', 19), ('加载速度快', 20),
      ('隐私与权限控制', 21), ('多端同步支持', 22)]

Q1 = [s(r[4]) for r in data]
Q2 = {k: sum(1 for r in data if s(r[i])) for k, i in PLAT}
Q3 = [int(s(r[12])) for r in data]
Q4 = {k: [int(s(r[i])) for r in data] for k, i in FN}
Q5 = {k: [int(s(r[i])) for r in data] for k, i in PR}
Q6 = [int(s(r[23])) for r in data]
Q7 = [s(r[24]) for r in data if s(r[24])]
DUR = [int(s(r[3])) for r in data]
PROV = [s(r[29]) for r in data]
PC = lambda v: v / N * 100

# ---------- 统计明细 ----------
L = []
p = L.append
p('有效答卷 n = %d' % N)
p('答题时长(秒): min=%d max=%d mean=%.1f median=%.1f' %
  (min(DUR), max(DUR), sum(DUR) / N, sorted(DUR)[N // 2]))
for name, d in [('Q1 身份', Q1)]:
    p('\n[%s]' % name)
    for k, v in Counter(d).most_common():
        p('  %-16s %2d (%.1f%%)' % (k, v, PC(v)))
p('\n[Q2 平台提及率]')
for k, v in sorted(Q2.items(), key=lambda x: -x[1]):
    p('  %-18s %2d (%.1f%%)' % (k, v, PC(v)))
p('  人均提及 %.2f' % (sum(Q2.values()) / N))
p('\n[Q3 满意度]')
for k in sorted(Counter(Q3)):
    p('  %d分: %2d (%.1f%%)' % (k, Counter(Q3)[k], PC(Counter(Q3)[k])))
p('  均值 %.2f' % (sum(Q3) / N))
p('\n[Q4 功能重要性 均值]')
for k, v in sorted(Q4.items(), key=lambda x: -sum(x[1]) / N):
    p('  %-18s %.2f  %s' % (k, sum(v) / N, dict(sorted(Counter(v).items()))))
p('\n[Q5 优先级 平均位次（越小越优先）]')
for k, v in sorted(Q5.items(), key=lambda x: sum(x[1]) / N):
    p('  %-18s %.2f  %s' % (k, sum(v) / N, dict(sorted(Counter(v).items()))))
bad = [i for i, r in enumerate(data)
       if sorted(int(s(r[j])) for j in range(18, 23)) != [1, 2, 3, 4, 5]]
p('  非合法排列的答卷: %s' % (bad or '无'))
p('\n[Q6 费力程度]')
for k in sorted(Counter(Q6)):
    p('  %d分: %2d (%.1f%%)' % (k, Counter(Q6)[k], PC(Counter(Q6)[k])))
p('  区间 %d-%d 均值 %.2f' % (min(Q6), max(Q6), sum(Q6) / N))
p('\n[Q7 开放题] 有作答 %d/%d' % (len(Q7), N))
for t in Q7:
    p('   · %s' % t)

p('\n[数据质量]')
sl = [s(data[i][0]) for i in range(N) if len(set(Q4[k][i] for k, _ in FN)) == 1]
p('  Q4 五项全同（疑似直线作答）: %s (%.1f%%)' % (sl, len(sl) / N * 100))
p('  非北京答卷: %s' % [s(data[i][0]) for i in range(N) if PROV[i] != '北京市'])
non = [i for i in range(N) if s(data[i][0]) not in sl]
p('  剔除后 n=%d；功能重要性均值:' % len(non))
for k, v in Q4.items():
    p('    %-18s %.2f' % (k, sum(v[i] for i in non) / len(non)))

open('统计明细.txt', 'w', encoding='utf-8').write('\n'.join(L))
print('n=%d  统计明细.txt 已生成' % N)


# ---------- 图表 ----------
def style(ax, grid_axis='x'):
    ax.set_facecolor(SURFACE)
    for sp in ('top', 'right'):
        ax.spines[sp].set_visible(False)
    for sp in ('left', 'bottom'):
        ax.spines[sp].set_color(BASE); ax.spines[sp].set_linewidth(0.8)
    ax.grid(True, axis=grid_axis, color=GRID, linewidth=0.8, linestyle='-', zorder=0)
    ax.set_axisbelow(True)
    ax.tick_params(colors=MUTED, length=0, labelsize=9)


def save(fig, name):
    fig.patch.set_facecolor(SURFACE)
    fig.savefig(os.path.join(OUTDIR, name), dpi=200, bbox_inches='tight',
                facecolor=SURFACE, pad_inches=0.28)
    plt.close(fig)
    print('  ->', name)


def title(ax, head, sub):
    ax.text(0, 1.145, head, transform=ax.transAxes, color=INK1,
            fontsize=12.5, fontweight='bold', va='baseline')
    ax.text(0, 1.04, sub, transform=ax.transAxes, color=INK2,
            fontsize=9, va='baseline')


def dotplot(rows, fname, head, sub, xlab):
    """点图：全宽浅色轨道 + 圆点，避免柱图零基线问题"""
    labels = [k for k, _ in rows]; means = [m for _, m in rows]
    fig, ax = plt.subplots(figsize=(6.8, 3.2))
    y = list(range(len(labels)))
    for i in y:
        ax.plot([1, 5], [i, i], color=GRID, linewidth=2.6, zorder=2,
                solid_capstyle='round')
    ax.axvline(3, color=BASE, linewidth=0.9, zorder=1)
    ax.scatter(means, y, s=95, color=SERIES, zorder=4, edgecolors=SURFACE,
               linewidths=1.6)
    for i, m in enumerate(means):
        ax.text(m + 0.14, i, '%.2f' % m, va='center', color=INK2, fontsize=9.5)
    ax.set_yticks(y); ax.set_yticklabels(labels, color=INK1, fontsize=10)
    ax.invert_yaxis(); ax.set_xlim(1, 5); ax.set_xticks([1, 2, 3, 4, 5])
    ax.set_xticklabels(xlab, color=INK1, fontsize=9)
    style(ax, grid_axis='x')
    title(ax, head, sub)
    save(fig, fname)


# 图1 样本构成
cats = ['本科生', '硕士研究生', '博士研究生']
vals = [sum(1 for x in Q1 if c in x) for c in cats]
fig, ax = plt.subplots(figsize=(6.4, 2.9))
ax.barh(range(len(cats)), vals, height=0.52, color=SERIES, zorder=3)
ax.set_yticks(range(len(cats))); ax.set_yticklabels(cats, color=INK1, fontsize=10)
ax.invert_yaxis()
for i, v in enumerate(vals):
    ax.text(v + 0.35, i, '%d 人（%.1f%%）' % (v, PC(v)), va='center',
            color=INK2, fontsize=9.5)
ax.set_xlim(0, max(vals) * 1.30); ax.set_xticks([])
style(ax, grid_axis='x'); ax.grid(False, axis='x')
title(ax, '样本构成：本科生占 90.0%', 'Q1 受访者身份分布（n=%d）' % N)
save(fig, '图1_样本构成.png')

# 图2 平台使用率
it = sorted(Q2.items(), key=lambda x: x[1])
fig, ax = plt.subplots(figsize=(6.8, 3.4))
ax.barh(range(len(it)), [v for _, v in it], height=0.55, color=SERIES, zorder=3)
ax.set_yticks(range(len(it)))
ax.set_yticklabels([k for k, _ in it], color=INK1, fontsize=10)
for i, (_, v) in enumerate(it):
    ax.text(v + 0.3, i, '%d（%.1f%%）' % (v, PC(v)), va='center',
            color=INK2, fontsize=9.5)
ax.set_xlim(0, max(Q2.values()) * 1.24); ax.set_xticks([])
style(ax, grid_axis='x'); ax.grid(False, axis='x')
title(ax, '平台使用率：GitHub 居首（90.0%），CNKI/知网 45.0%',
      'Q2 使用过的学术成果分享平台（多选，n=%d；人均提及 2.50 个）' % N)
save(fig, '图2_平台使用率.png')

# 图3 / 图6 频数柱（单系列）
for q, lv, fname, head, sub, xlabel in [
    (Q3, [1, 2, 3, 4, 5], '图3_整体满意度.png',
     '整体满意度：以 4 分（50.0%）为主，均值 3.75',
     'Q3 对当前所用平台的整体满意度（1–5 分，n=%d）' % N, None),
    (Q6, list(range(min(Q6), max(Q6) + 1)), '图6_费力程度.png',
     '查找费力程度：3–5 分合计占 70.0%，均值 4.30',
     'Q6 使用现有平台查找学术成果的费力程度评分（n=%d）' % N,
     '费力程度评分（数值越大表示越费力）'),
]:
    vv = [sum(1 for x in q if x == k) for k in lv]
    fig, ax = plt.subplots(figsize=(6.4, 3.0))
    ax.bar(range(len(lv)), vv, width=0.5, color=SERIES, zorder=3)
    ax.set_xticks(range(len(lv)))
    ax.set_xticklabels(['%d 分' % k if q is Q3 else '%d' % k for k in lv],
                       color=INK1, fontsize=10)
    for i, v in enumerate(vv):
        if v:
            ax.text(i, v + 0.18, '%d（%.1f%%）' % (v, PC(v)), ha='center',
                    color=INK2, fontsize=9)
    ax.set_ylim(0, max(vv) * 1.28); ax.set_yticks([])
    style(ax, grid_axis='y'); ax.grid(False, axis='y')
    if xlabel:
        ax.set_xlabel(xlabel, color=INK2, fontsize=9.5, labelpad=6)
    title(ax, head, sub)
    save(fig, fname)

# 图4 功能重要性
dotplot(sorted(((k, sum(v) / len(v)) for k, v in Q4.items()), key=lambda x: x[1]),
        '图4_功能重要性.png',
        '功能重要性：文献检索与下载评分最高（均值 4.10）',
        'Q4 平台功能重要性评分（1–5 分均值；竖线 3.0 为量表中点，n=%d）' % N,
        ['1\n很不重要', '2', '3', '4', '5\n很重要'])

# 图5 建设优先级
dotplot(sorted(((k, sum(v) / len(v)) for k, v in Q5.items()), key=lambda x: x[1]),
        '图5_建设优先级.png',
        '建设优先级：资源丰富全面平均位次最前（1.60）',
        'Q5 平台特性优先级排序（平均位次，数值越小优先级越高；竖线 3.0 为位次中点，n=%d）' % N,
        ['1\n最优先', '2', '3', '4', '5\n最不优先'])

print('完成')
