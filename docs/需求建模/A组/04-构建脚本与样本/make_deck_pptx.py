"""Build the combined assignment-1 + assignment-2 presentation deck.

作业 1（需求调研）与作业 2（需求建模）在同一份汇报稿中一次汇报，结构对应课程
《课堂展示与汇报结构与时间分配》：团队与分工 1 分钟、需求调研 4 分钟、需求建模
5 分钟、AI 使用 1 分钟、小结 1 分钟。7 张 CodeArts 导出图与系统用例图全部内嵌。

Output: 提交版/作业2-学术成果分享平台-汇报稿-v3.pptx
"""

from __future__ import annotations

from pathlib import Path

from PIL import Image
from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import PP_ALIGN
from pptx.oxml.ns import qn
from pptx.util import Emu, Pt

ROOT = Path(__file__).resolve().parent.parent.parent   # 02_作业2/
FIG = ROOT / 'A组' / '02-模型图'
OUT = ROOT / '提交版' / '作业2-学术成果分享平台-汇报稿-v3.pptx'

FONT = 'Hiragino Sans GB'
NAVY, BLUE, GRAY = RGBColor(0x24, 0x36, 0x4B), RGBColor(0x38, 0x5E, 0x7D), RGBColor(0x5D, 0x71, 0x83)
PALE, LINE = RGBColor(0xF7, 0xFA, 0xFC), RGBColor(0xC9, 0xD9, 0xE5)
PX = 9525                                            # EMU per px at 96 dpi
TOTAL = 17


def set_font(run, size, bold, color):
    run.font.name = FONT
    run.font.size = Pt(size * 0.75)                  # deck authored at 96 dpi
    run.font.bold = bold
    run.font.color.rgb = color
    rPr = run._r.get_or_add_rPr()
    for tag in ('a:ea', 'a:cs'):
        el = rPr.find(qn(tag))
        if el is None:
            el = rPr.makeelement(qn(tag), {}); rPr.append(el)
        el.set('typeface', FONT)


def tx(slide, text, x, y, w, h, size=25, bold=False, color=NAVY, align=PP_ALIGN.LEFT):
    box = slide.shapes.add_textbox(Emu(x * PX), Emu(y * PX), Emu(w * PX), Emu(h * PX))
    tf = box.text_frame
    tf.word_wrap = True
    tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
    for i, line in enumerate(text.split('\n')):
        para = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        para.alignment = align
        set_font(para.add_run(), size, bold, color)
        para.runs[0].text = line
    return box


def add_image(slide, path: Path, x, y, w, h):
    iw, ih = Image.open(path).size
    scale = min(w / iw, h / ih)
    nw, nh = int(iw * scale), int(ih * scale)
    left, top = x + (w - nw) // 2, y + (h - nh) // 2
    slide.shapes.add_picture(str(path), Emu(left * PX), Emu(top * PX), Emu(nw * PX), Emu(nh * PX))


def blank(prs):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    slide.background.fill.solid()
    slide.background.fill.fore_color.rgb = PALE
    return slide


def base(prs, title, n):
    slide = blank(prs)
    tx(slide, title, 60, 42, 1160, 65, 35, True)
    rule = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Emu(60 * PX), Emu(116 * PX),
                                  Emu(1160 * PX), Emu(2 * PX))
    rule.fill.solid(); rule.fill.fore_color.rgb = LINE; rule.line.fill.background()
    tx(slide, f'学术成果分享平台 · 作业 1＋作业 2                              {n}/{TOTAL}',
       60, 675, 1160, 26, 15, False, GRAY)
    return slide


def rows(slide, items, x=80, y=172, w=1120, gap=112, size=26):
    for i, t in enumerate(items):
        tx(slide, t, x, y + i * gap, w, gap - 12, size)


def figure_slide(prs, title, n, image, caption, points):
    """Figure on the left two thirds, key points stacked on the right."""
    slide = base(prs, title, n)
    add_image(slide, image, 60, 150, 760, 470)
    x = 850
    tx(slide, caption, x, 168, 380, 70, 20, True, BLUE)
    for i, t in enumerate(points):
        tx(slide, t, x, 250 + i * 92, 380, 88, 18, False, NAVY)
    return slide


def new_deck() -> Presentation:
    prs = Presentation()
    prs.slide_width, prs.slide_height = Emu(12192000), Emu(6858000)
    return prs


def blocks(slide, items, y=168, gap=150, hsize=25, bsize=19, hh=38, y2=42):
    """Heading + body pairs, used by every text slide."""
    for i, (h, b) in enumerate(items):
        tx(slide, h, 80, y + i * gap, 1120, hh, hsize, True, BLUE)
        tx(slide, b, 80, y + i * gap + y2, 1120, gap - y2 - 6, bsize)


def slide_01(prs):
    """封面 —— 作业 1 与作业 2 合并汇报"""
    s = blank(prs)
    tx(s, '《软件系统分析与设计》课程实践', 80, 92, 1120, 40, 22, False, GRAY)
    tx(s, '学术成果分享平台', 80, 146, 1120, 85, 55, True)
    tx(s, '作业 1 需求调研 ＋ 作业 2 需求建模 · 合并汇报', 82, 246, 1120, 58, 32, False, BLUE)
    tx(s, '团队名称：________组 · ________团队（待填）', 82, 348, 1120, 40, 22)
    tx(s, '成员与分工：A 组（一手走查与需求模型）／B 组（SRS 与用户故事）——名单与分工待填', 82, 394, 1120, 40, 22)
    tx(s, '两组路线：A 组一手走查 + CodeArts 建模；B 组桌面研究 + AI 角色推演', 82, 440, 1120, 40, 22)
    tx(s, '第 5 讲研讨课 · 2026 年 10 月 14 日', 82, 574, 1120, 40, 20, False, GRAY)


def slide_02(prs):
    """团队与分工 · 汇报结构"""
    s = base(prs, '团队与分工 · 汇报结构', 2)
    tx(s, '两组分工与路线', 80, 152, 1120, 38, 24, True, BLUE)
    tx(s, 'A 组：一手证据路线（问卷、知网与官网任务走查、六份用例规约、CodeArts 建模）', 80, 192, 1120, 34, 19)
    tx(s, 'B 组：桌面研究路线（竞品矩阵、存量抽样、SRS 与 24 条用户故事）＋ AI 角色推演', 80, 226, 1120, 34, 19)
    tx(s, '汇报结构（合计 15 分钟：汇报 12 分钟 + 问答 3 分钟）', 80, 296, 1120, 38, 24, True, BLUE)
    for i, t in enumerate([
        '一、团队与分工简介                                    约 1 分钟',
        '二、需求调研成果（作业 1）                              约 4 分钟',
        '三、需求建模成果（作业 2：SRS 基线、六个用例、三张模型图、SPEC）  约 5 分钟',
        '四、AI 使用与人工验证说明                              约 1 分钟',
        '五、小结与后续计划                                    约 1 分钟',
    ]):
        tx(s, t, 80, 340 + i * 58, 1120, 52, 22)


def slide_03(prs):
    """作业 1 调研方案"""
    s = base(prs, '调研方案（作业 1）', 3)
    blocks(s, [
        ('调研目标', '把平台定位转化为可评审的需求边界：普通用户能否找到并核对成果；科研人员能否在门户维护与认领；管理员如何处理来源、审核与更新'),
        ('调研对象', '主要——普通用户／学生、科研人员／教师、平台管理员；次要——机构科研管理人员、数据源提供方'),
        ('调研方法', '背景资料研读 · 数据源调研 · 同类平台竞品矩阵 · 在线问卷 · 任务式渠道走查 · AI 角色推演'),
        ('范围与时间', '一期以论文／专利／项目／获奖四类为基线，软著与课程材料为扩展候选，未发表手稿本轮排除；材料覆盖 2026-10-09 至 10-12'),
    ], y=162, gap=126, hsize=23, bsize=18, hh=34, y2=38)


def slide_04(prs):
    """作业 1 调研执行"""
    s = base(prs, '调研执行（作业 1）', 4)
    blocks(s, [
        ('数据源调研', '实测知网（收费库，仅人工核对与合法导出）、学院官网、科研院门户、教师主页、课题组主页、researchr、ORCID；任务书建议的 OpenAlex／DBLP 尚未实测，已列入待办'),
        ('领域分类方案', '本轮未制定具体领域树，报告以「四类成果为基线」限定范围并如实标注，不把未完成项写成结论'),
        ('版权与合规评估', '收费库不批量抓取；不采集个人隐私、无授权全文与登录后受限内容；未发表手稿排除；来源必须可核对公开或授权依据'),
        ('证据分级与实测发现', 'E1 一手（截图／导出文件）· E2 桌面研究 · H 推演假设；3 条具体检索式重复失败，记为「检索失败」而非零收录'),
    ], y=162, gap=126, hsize=23, bsize=18, hh=34, y2=38)


def slide_05(prs):
    """作业 1 三类用户核心诉求"""
    s = base(prs, '三类用户核心诉求（作业 1）', 5)
    blocks(s, [
        ('普通用户／学生（E1，20 份有效问卷）', '五项功能重要性均值均高于 3 分，文献检索与下载 4.10 最高；建设优先级首选「资源丰富全面」；样本仅 20 人、无教师与管理员答卷'),
        ('科研人员／教师（H，公开资料 + 推演 10 条）', '候选诉求如：认领通过后的署名通知、个人成果清单导出、门户信息的本人可维护范围'),
        ('平台管理员（H，公开门户 + 推演 8 条 + 9 条反方评审）', '候选诉求如：发布与下架的决策理由留痕、存量导入的合法来源与授权记录、争议处理的处理路径'),
        ('关键限定', '推演材料不冒充真实访谈，全部标注「待验证」；教师与管理员诉求进入验证清单，不写成已确认需求'),
    ], y=162, gap=126, hsize=23, bsize=18, hh=34, y2=38)


def slide_06(prs):
    """作业 1 需求边界与优先级"""
    s = base(prs, '需求边界与优先级（作业 1）', 6)
    tx(s, '必须（Must，6 条）', 80, 158, 1120, 36, 23, True, BLUE)
    tx(s, 'R01 四类成果与类型专属字段 · R02 组合检索与条件回显 · R03 来源 URL／获取时间／字段核验状态留痕 · '
          'R04 区分有结果／明确零结果／查询失败／权限不足／尚未采集 · R05 门户认领与管理员审核 · R06 采集清洗与增量更新',
       80, 198, 1120, 76, 18)
    tx(s, '应当（Should，2 条）', 80, 292, 1120, 36, 23, True, BLUE)
    tx(s, 'R07 按来源的引用格式导出与全文入口 · R08 DOI／关键词等字段允许为空并标记缺失与待核验',
       80, 332, 1120, 40, 18)
    tx(s, '一期范围外', 80, 392, 1120, 36, 23, True, BLUE)
    tx(s, '有偿成果转让、付费全文下载、专利交易、未授权收费库抓取、任意知网 TXT 自动解析、扫描件 OCR',
       80, 432, 1120, 40, 18)
    tx(s, '待验证（R10）', 80, 492, 1120, 36, 23, True, BLUE)
    tx(s, '教师成果 CSV 导出、复杂审核规则、扩展软著与课件类型——需教师与管理员确认，保留「待验证」，不因写入 SRS 变成已证实',
       80, 532, 1120, 60, 18)


def slide_07(prs):
    """作业 2 需求范围与交付边界"""
    s = base(prs, '需求建模范围与交付边界（作业 2）', 7)
    blocks(s, [
        ('七类成果', '论文、专利、软件著作权、获奖、项目、课程材料、未发表手稿——与作业 1 的四类走查样本分开表述，不把类型能力写成已收集到条目'),
        ('六个系统用例', '覆盖采集管理、认领申请与审核、检索查看、本人成果管理、统计分析'),
        ('首期必验创新', '专家合作网络由 UC06 的交互扩展流程承接，对应 FR-29、AT-17'),
    ], y=170, gap=165, hsize=29, bsize=25, hh=45, y2=55)


def slide_08(prs):
    """参与者与六个用例 + 用例图"""
    s = base(prs, '参与者与六个用例', 8)
    add_image(s, FIG / '用例图' / 'A2-系统用例图.png', 60, 150, 700, 470)
    x = 790
    for i, t in enumerate([
        '访客：UC04 检索并查看成果；UC06 查看成果统计',
        '科研人员申请人：UC02 申请认领学者门户',
        '已认领学者：UC05 管理本人已认领成果',
        '平台管理员：UC01 管理采集；UC03 审核认领；UC06 查看统计',
    ]):
        tx(s, t, x, 200 + i * 100, 430, 96, 18)
    tx(s, '图为 CodeArts Modeling 导出', x, 620, 430, 30, 15, False, GRAY)


def slide_09(prs):
    """六个用例要点"""
    s = base(prs, '六个用例要点', 9)
    for i, t in enumerate([
        'UC01 管理数据采集任务：合法来源、任务状态、限次重试与增量结果',
        'UC02 申请认领学者门户：提交本人佐证，审核通过前不授予管理权',
        'UC03 审核门户认领申请：核验证据与归属、记录理由、处理争议',
        'UC04 检索并查看成果：七类成果、权限过滤、来源、引用与导出',
        'UC05 管理本人已认领成果：本人权限、版本更新、公开变更重审',
        'UC06 查看成果统计：机构与年度口径、热点分析、专家合作网络',
    ]):
        tx(s, t, 80, 158 + i * 78, 1120, 66, 22)


def slide_10(prs):
    """认领审核活动图"""
    figure_slide(prs, '认领审核活动图（CodeArts 导出）', 10,
                 FIG / '流程与状态图' / 'A2-认领审核活动图.png',
                 '三条竖向分区', [
                     '申请人 / 平台系统 / 授权管理员 三条竖向分区',
                     '流程：提交申请 → 校验 → 核验 → 审核 → 通过／驳回',
                     '校验不通过回到补正；已有管理人或争议转人工核验',
                     '批准授予目标门户管理权；驳回后可按 B1 SRS 补证重提',
                 ])


def slide_11(prs):
    """两张状态机图并排"""
    s = base(prs, '两张状态图（CodeArts 导出）', 11)
    add_image(s, FIG / '流程与状态图' / 'A2-采集任务状态图.png', 50, 148, 580, 330)
    add_image(s, FIG / '流程与状态图' / 'A2-认领申请状态图.png', 650, 148, 580, 330)
    tx(s, '采集任务状态图', 50, 490, 580, 30, 18, True, BLUE)
    tx(s, 'queued → running → succeeded／failed／stopped；失败可重试（未满 3 次）后终止',
       50, 522, 580, 56, 16)
    tx(s, '认领申请状态图', 650, 490, 580, 30, 18, True, BLUE)
    tx(s, 'submitted → verifying → approved／rejected；可 cancelled；批准后争议标 disputed',
       650, 522, 580, 56, 16)
    tx(s, '两张图的状态命名与 B1 SRS 2.2 节一致；“成功”与“明确零结果”区分，“失败”不写作零收录',
       50, 606, 1180, 40, 16, False, GRAY)


def slide_12(prs):
    """SPEC 概览 + 清洗流程"""
    figure_slide(prs, '核心模块 SPEC（1/2）：清洗与字段标准化', 12,
                 FIG / '流程与状态图' / 'A2-SPEC-ETL-01-清洗与标准化流程.png',
                 'SPEC-ETL-01', [
                     '结构校验 → 类型映射（七类）→ 文本规范 → 日期分列 → 标识规范 → 字段状态',
                     '保留来源原值，规范值不覆盖原始值',
                     '未知年度留草稿；不自动译名、不编造 DOI',
                     '逐行隔离错误；批次幂等确认，不把失败伪报成功',
                 ])


def slide_13(prs):
    """去重与消歧"""
    s = base(prs, '核心模块 SPEC（2/2）：去重与消歧', 13)
    add_image(s, FIG / '流程与状态图' / 'A2-SPEC-DEDUP-01-成果去重流程.png', 60, 150, 540, 396)
    add_image(s, FIG / '流程与状态图' / 'A2-SPEC-DISAMB-01-学者消歧流程.png', 620, 150, 560, 396)
    tx(s, 'SPEC-DEDUP-01 成果去重', 60, 556, 540, 30, 17, True, BLUE)
    tx(s, 'SPEC-DISAMB-01 学者消歧', 620, 556, 560, 30, 17, True, BLUE)
    tx(s, '有效 DOI 阻止直接重复公开；相似题名只生成人工候选', 60, 590, 540, 28, 15, False, GRAY)
    tx(s, 'Person 与 User 分离；同名同单位不自动合并', 620, 590, 560, 28, 15, False, GRAY)


def slide_14(prs):
    """检索排序与分面"""
    figure_slide(prs, 'SPEC-SEARCH-01 检索排序与分面', 14,
                 FIG / '流程与状态图' / 'A2-SPEC-SEARCH-01-检索排序与分面流程.png',
                 '先鉴权，再计算', [
                     '先按身份建立可读集合，再执行匹配与分面统计',
                     '有效 DOI 精确命中置前，其后按相关度、年度、稳定 ID',
                     '默认每页 20、最大 100；未知年度单列，不当作 0',
                     '详情／附件／引用／导出再次鉴权；无权与不存在统一 404',
                 ])


def slide_15(prs):
    """非功能需求、接口数据与追溯"""
    s = base(prs, '非功能需求、接口数据与追溯一致性', 15)
    blocks(s, [
        ('非功能需求（NFR）', '性能（4 vCPU／8 GB、20 并发、P95 ≤ 2 秒为设计目标，未实测）· 安全与权限 · 可用性与恢复 · 交互与兼容 · 授权与数据质量'),
        ('接口与数据需求', '接口清单（检索／门户／认领／采集／统计）· 外部数据源接口 · REST 通用规则；数据需求含核心实体、数据字典与 8 项数据质量指标'),
        ('追溯一致性', 'R01—R10 → UC01—UC06 → FR／IF／DR／NFR → AT-01—AT-17 逐条有入口；图与文字的状态命名、权限口径已互相核对'),
    ], y=170, gap=158, hsize=26, bsize=19, hh=40, y2=48)


def slide_16(prs):
    """AI 使用与人工验证"""
    s = base(prs, 'AI 使用与人工验证', 16)
    for i, (h, b) in enumerate([
        ('A 组路线：一手走查 + CodeArts 建模',
         'AI 辅助整理走查记录与报告文本、六份用例规约、SPEC 合稿与 CodeArts 模型工程 ZIP；图面几何与守卫文字由人工核对'),
        ('B 组路线：桌面研究 + 角色推演',
         'B5 使用 CodeArts 智能体做教师／管理员角色推演与反方评审；推演材料不冒充真实访谈'),
        ('两组大模型路线对比',
         'A 组以实测页面与截图为准，结论受样本限制；B 组以公开资料与推演补充，未登录功能一律保留「未知」'),
        ('声明 · 理解 · 责任',
         '阈值与业务规则以 B1 已写明条款为准；关键判断与最终决策由团队成员负责；验收项为待执行标准，不写作已测试通过'),
    ]):
        tx(s, h, 80, 152 + i * 132, 1120, 40, 25, True, BLUE)
        tx(s, b, 80, 194 + i * 132, 1120, 84, 19)


def slide_17(prs):
    """小结与后续计划"""
    s = base(prs, '小结与后续计划', 17)
    blocks(s, [
        ('本阶段结论', '需求基线已建立（B1 SRS V1.0）；六个用例与六份规约、三张模型图、SPEC 五个模块成形；8 张图由 CodeArts 导出并回填文档'),
        ('待完成事项', '领域分类方案 · OpenAlex／DBLP 接口与许可实测 · 教师与管理员访谈 · 软著登记号与项目编号核验 · 性能与验收实测'),
        ('下一步工作', '需求分析（核心业务类图与关键用例交互模型）→ 架构设计 → 构件设计 → 功能实现'),
        ('请老师与同学指正的重点', '一期范围裁定是否合理；三张图的状态与流转是否符合任务书；SPEC 的阈值与验收方式是否可执行'),
    ], y=170, gap=118, hsize=24, bsize=18, hh=36, y2=40)


SLIDES = [slide_01, slide_02, slide_03, slide_04, slide_05, slide_06, slide_07,
          slide_08, slide_09, slide_10, slide_11, slide_12, slide_13, slide_14,
          slide_15, slide_16, slide_17]


def build(path: Path, only: int | None = None) -> Presentation:
    prs = new_deck()
    for i, fn in enumerate(SLIDES, 1):
        if only is None or i == only:
            fn(prs)
    path.parent.mkdir(parents=True, exist_ok=True)
    prs.save(path)
    return prs


def main() -> None:
    import sys
    if len(sys.argv) > 2 and sys.argv[1] == '--only':
        out = Path(sys.argv[3])
        build(out, only=int(sys.argv[2]))
        print(f'{out}  (只含第 {sys.argv[2]} 页)')
        return
    prs = build(OUT)
    print(f'{OUT.name}  ({len(prs.slides._sldIdLst)} slides, {OUT.stat().st_size // 1024} KB)')


if __name__ == '__main__':
    main()
