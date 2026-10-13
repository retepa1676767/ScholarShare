"""Generate the two cross-assignment materials required by the submission list.

  * 修改说明与版本记录表  (附录C format; landscape so the 7 columns fit)
  * AI 使用声明

Both are produced with python-docx - no LibreOffice.
"""

from __future__ import annotations

from pathlib import Path

from docx import Document
from docx.enum.section import WD_ORIENT
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor

ROOT = Path(__file__).resolve().parent.parent.parent      # 02_作业2/
OUT = ROOT / '提交版'
BODY, HEAD = '宋体', '黑体'
NAVY = RGBColor(0x24, 0x36, 0x4B)
GREY = RGBColor(0x5D, 0x71, 0x83)


def cjk(obj, font: str) -> None:
    obj.font.name = font
    rPr = obj._element.get_or_add_rPr()
    rf = rPr.find(qn('w:rFonts'))
    if rf is None:
        rf = OxmlElement('w:rFonts'); rPr.append(rf)
    for a in ('w:ascii', 'w:hAnsi', 'w:eastAsia', 'w:cs'):
        rf.set(qn(a), font)


def new_doc(landscape: bool = False) -> Document:
    doc = Document()
    st = doc.styles['Normal']
    st.font.size = Pt(10.5)
    cjk(st, BODY)
    st.paragraph_format.line_spacing = 1.3
    st.paragraph_format.space_after = Pt(5)
    for i, (size, bold) in enumerate([(20, True), (14, True), (12, True)], 1):
        h = doc.styles[f'Heading {i}']
        h.font.size = Pt(size); h.font.color.rgb = NAVY; cjk(h, HEAD)
        h.paragraph_format.space_before = Pt(12 if i == 1 else 9)
        h.paragraph_format.space_after = Pt(5)
    sec = doc.sections[0]
    if landscape:
        sec.orientation = WD_ORIENT.LANDSCAPE
        sec.page_width, sec.page_height = sec.page_height, sec.page_width
        sec.left_margin = sec.right_margin = Cm(1.8)
        sec.top_margin = sec.bottom_margin = Cm(1.8)
    else:
        sec.left_margin = sec.right_margin = Cm(2.4)
        sec.top_margin = sec.bottom_margin = Cm(2.2)
    return doc


def title(doc: Document, text: str, sub: str | None = None) -> None:
    p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p.add_run(text); cjk(r, HEAD); r.font.size = Pt(19); r.bold = True; r.font.color.rgb = NAVY
    if sub:
        q = doc.add_paragraph(); q.alignment = WD_ALIGN_PARAGRAPH.CENTER
        s = q.add_run(sub); cjk(s, BODY); s.font.size = Pt(10); s.font.color.rgb = GREY
    doc.add_paragraph().paragraph_format.space_after = Pt(2)


def borders(table, color='9AB3C7') -> None:
    b = OxmlElement('w:tblBorders')
    for edge in ('top', 'left', 'bottom', 'right', 'insideH', 'insideV'):
        el = OxmlElement(f'w:{edge}')
        el.set(qn('w:val'), 'single'); el.set(qn('w:sz'), '6')
        el.set(qn('w:space'), '0'); el.set(qn('w:color'), color)
        b.append(el)
    table._tbl.tblPr.append(b)


def shade(cell, fill: str) -> None:
    el = OxmlElement('w:shd')
    el.set(qn('w:val'), 'clear'); el.set(qn('w:color'), 'auto'); el.set(qn('w:fill'), fill)
    cell._tc.get_or_add_tcPr().append(el)


def table(doc: Document, headers: list[str], rows: list[list[str]],
          widths: list[float] | None = None, size: float = 9) -> None:
    t = doc.add_table(rows=1, cols=len(headers))
    t.style = 'Table Grid'; t.alignment = WD_TABLE_ALIGNMENT.CENTER
    borders(t)
    for i, h in enumerate(headers):
        c = t.rows[0].cells[i]; shade(c, 'EAF1F8')
        p = c.paragraphs[0]; p.paragraph_format.space_after = Pt(1)
        r = p.add_run(h); cjk(r, HEAD); r.bold = True; r.font.size = Pt(size)
    for row in rows:
        cells = t.add_row().cells
        for i, val in enumerate(row[:len(headers)]):
            p = cells[i].paragraphs[0]; p.paragraph_format.space_after = Pt(1)
            r = p.add_run(val); cjk(r, BODY); r.font.size = Pt(size)
    if widths:
        for row in t.rows:
            for i, w in enumerate(widths):
                row.cells[i].width = Cm(w)
    doc.add_paragraph().paragraph_format.space_after = Pt(2)


def para(doc: Document, text: str, size: float = 10.5, italic=False, color=None) -> None:
    p = doc.add_paragraph()
    r = p.add_run(text); cjk(r, BODY); r.font.size = Pt(size)
    r.italic = italic
    if color is not None:
        r.font.color.rgb = color


# ---------------------------------------------------------------- 表 1
def change_log() -> Path:
    doc = new_doc(landscape=True)
    title(doc, '修改说明与版本记录表',
          '《软件系统分析与设计》课程实践 · 作业 1／作业 2 · 学术成果分享平台 · 更新至 2026-10-13')
    para(doc, '依据：课程《课堂展示与提交要求》附录 C。表 A 如实记录展示前的组内迭代；'
              '表 B 在 2026-10-14 第 5 讲研讨课的教师点评与小组互评后逐条填写，未采集到的意见不代填。'
              '修改人一栏使用组内分工代号（A1—A5／B1—B5）；提交前请替换为成员姓名。', 9.5, color=GREY)

    doc.add_heading('表 A  展示前组内迭代记录（已完成）', 2)
    table(doc,
          ['序号', '修改项', '反馈来源', '修改内容', '修改人', '修改日期', '验证方式'],
          [
           ['1', '作业 1 缺独立的数据源清单', '用户指示',
            '新增《数据源清单》独立文件：31 个编号来源，逐条标实测状态、可得字段与证据文件；'
            '单列第 6 节合规红线（8 条）', 'A1', '2026-10-12',
            '26 个引用 URL 逐条回溯到既有走查记录／截图／竞品矩阵／任务书'],
           ['2', 'A 组目录文件平铺混放（38 个文件一层）', '组内自查',
            '按交付物性质分入 01-需求与设计文档／02-模型图／03-模型说明与记录／04-构建脚本与样本；'
            '同步改写文档间相对路径', 'A1', '2026-10-12',
            '链接审计：图片引用 8/8 可解析；脚本从新位置运行产物落位正确'],
           ['3', 'CodeArts 活动图泳道方向', '组内自查（人工核对导入结果）',
            '第一版 `shape=swimlane;horizontal=0` 导入后按横排渲染；改为 `type="Partition"` 普通矩形，'
            '让出标题条宽度并重排节点', 'A2', '2026-10-12',
            '在 CodeArts 导入并导出 SVG，渲染核对为三条竖向分区'],
           ['4', '三张流程／状态图与 SPEC 图缺 CodeArts 导出图', '组内自查（对照提交要求附录 D 第 6—8 项）',
            '新增 4 个 CodeArts 模型工程 ZIP；用户在平台导入后导出 7 张 SVG', 'A2', '2026-10-12',
            '逐张核对节点、判定、连线与全部守卫标签齐全；活动图主线不再穿越分支框'],
           ['5', 'SRS／SPEC 无图位', '组内自查',
            'SRS 2.2 与 3.1 节、SPEC 1—4 节插入图位占位；图导出后回填为图片引用',
            'A2', '2026-10-12', '8 处图片链接脚本校验可解析；占位行已全部删除'],
           ['6', 'SRS／SPEC 仅有 Markdown，提交清单要求 Word', '组内自查（对照提交材料清单第 4、5 项）',
            '由 Markdown 生成同名 .docx，保留标题层级、表格与插图，并加页码与表格边框',
            'A1', '2026-10-12', '结构与源文件逐项比对：标题 60／表 8／图 4 与源一致'],
           ['7', '汇报稿 8 页、无建模图、缺 AI 使用说明页', '组内自查（对照展示材料要求）',
            '扩为 14 页合并汇报稿（作业 1＋作业 2），内嵌 8 张导出图，新增 AI 使用与人工验证页、'
            '封面补课程／项目／团队字段', 'A1', '2026-10-12',
            '用 macOS Quick Look 逐页渲染核对；程序化溢出与重叠审计通过'],
           ['8', '汇报稿第 11 页图注与页脚重叠', '组内自查（渲染核对发现）',
            '收缩两图高度、上移图注与灰色注释行', 'A1', '2026-10-12', '重新渲染确认无重叠'],
           ['9', 'SRS／SPEC 中插入的插图没有图号与图名', '用户反馈',
            '8 张图补「图 X-Y　图名（来源：CodeArts Modeling 导出；对应 UC／FR／AT 条款）」图注；'
            'Word 版将图注渲染为居中、9pt、深灰色', 'A1', '2026-10-13',
            '图注 8 处与插图一一对应；渲染核对居中显示'],
           ['10', 'SRS 第 3 章分 3.1／3.2 但未说明划分依据', '用户反馈',
            '章首补分节依据：按「功能需求来源」分节而非按功能主题；FR 编号全章连续（FR-01—FR-29），'
            '跨文档引用一律用 FR 编号。两节标题改为「来自用户故事的功能需求（FR-01—FR-24）」与'
            '「任务书必做但故事未覆盖的功能需求（FR-25—FR-29）」', 'B1', '2026-10-13',
            '与附录 A「统计及采集在故事中覆盖不足」一行交叉核对；FR 编号未变动，引用不受影响'],
           ['11', 'SPEC 缺任务书明确要求的交付证据与「怎么做（接口／约束）」',
            '用户反馈 + 对照任务书三（一）',
            '新增 §0.1 统一阈值与约束汇总（19 项，逐项标「已确认／设计规则／设计目标／未确认」）、'
            '§6.1 规范评审记录（4 行待评）、§7 规范—代码对应关系表（18 条，实现状态一律「待实现」）、'
            '§8 接口契约与错误码（建议稿）；SPEC 表格由 4 张增至 8 张', 'A1', '2026-10-13',
            '逐项对照任务书「做什么／怎么做／做到什么程度」与「交付证据：SPEC 目录、规范—代码对应关系表」；'
            'Word 版重生成并渲染核对'],
          ],
          widths=[1.2, 4.0, 3.4, 7.4, 1.4, 2.2, 5.0])

    doc.add_heading('表 B  展示后修改记录（2026-10-14 研讨课后填写）', 2)
    para(doc, '以下各行按《课堂展示与提交要求》第三部分「展示后完善迭代要求」填写：必改项（事实性错误、交付遗漏、'
              '图与文字不一致等）必须修改并留痕；建议项须说明采纳或暂不采纳的理由。', 9.5, color=GREY)
    table(doc,
          ['序号', '修改项', '反馈来源（教师/互评）', '修改内容', '修改人', '修改日期', '验证方式'],
          [[str(i), '', '', '', '', '', ''] for i in range(1, 9)],
          widths=[1.2, 4.0, 3.4, 7.4, 1.4, 2.2, 5.0])
    para(doc, '说明：本表 B 待课堂点评与互评记录整理后填写；未收到的意见不代填、不虚构。'
              '展示初评为过程性评价，最终成绩以迭代后的终稿为准。', 9, italic=True, color=GREY)

    path = OUT / '作业2-修改说明与版本记录表.docx'
    doc.save(path)
    return path


# ---------------------------------------------------------------- 表 2
def ai_statement() -> Path:
    doc = new_doc()
    title(doc, 'AI 使用声明', '《软件系统分析与设计》课程实践 · 作业 1／作业 2 · 学术成果分享平台')

    doc.add_heading('一、总体原则', 2)
    para(doc, '遵守课程 AI 使用政策「声明、理解、责任」：本作业中 AI 生成的内容全部经过人工审查与验证；'
              '需要判断的阈值、边界与业务规则以已确认文档为准；关键判断与最终决策由团队成员负责。'
              'AI 生成内容未经人工验证的部分不作为成果展示，相关结论一律标注证据等级或「待验证」。')

    doc.add_heading('二、使用环节、生成内容与人工验证', 2)
    table(doc,
          ['环节', '工具', 'AI 生成或辅助的内容', '人工验证方式'],
          [
           ['作业 1 需求调研（A 组）', 'Codex',
            '走查记录与失败清单的整理、报告章节文本组织、问卷统计脚本的辅助编写',
            '逐张截图与原始记录核对；结论限定在样本范围内，不以外推方式写全量结论'],
           ['作业 1 需求调研（B 组）', 'CodeArts 智能体（glm-5.3-flash）',
            '教师角色 10 条、管理员角色 8 条诉求推演，以及对推演的 9 条反方评审',
            '明确标注为「推演」，不冒充真实访谈；进入报告时保留「待验证」标识，未裁定项不写成已批准需求'],
           ['作业 2 需求建模（A 组）', 'Codex',
            '六份用例规约的整理、追溯矩阵、SPEC 合稿、CodeArts 模型工程 ZIP 的生成脚本',
            '与 B1 SRS 条款逐条对齐（FR／IF／DR／NFR／AT 编号）；图面几何与守卫文字人工核对'],
           ['作业 2 建模图导出', 'CodeArts Modeling（平台）+ 无头 Chrome',
            '7 张模型图（活动图、两张状态机图、SPEC 四张流程图）的 SVG→PNG 转换',
            '用户在平台导入并导出 SVG；逐张核对节点、判定、连线与全部守卫标签；再转 2× PNG 供 Word／PPT 使用'],
           ['作业 2 文档与汇报', 'Codex',
            'SRS／SPEC 的 Word 版生成、汇报稿生成与版面修正',
            '与 Markdown 源文件逐项比对（标题／表／图数量一致）；汇报稿逐页渲染核对并做溢出与重叠审计'],
          ], widths=[3.6, 3.4, 4.6, 5.4])

    doc.add_heading('三、AI 未参与的部分', 2)
    for t in ['数据来源的实测与截图（知网走查、学院官网、科研院门户、教师主页、课题组主页、researchr 等）'
              '全部由成员人工执行，截图与导出文件为原始证据；',
              '模型图中的业务语义——状态名称、守卫条件、用例边界与权限口径——来自 B1 SRS 与 A 组用例规约的人工判断；',
              '所有验收项与性能指标均为「设计目标、待执行」，本作业不填写任何虚构的测试通过记录；',
              '合规判断（收费库不批量抓取、不采集隐私与无授权全文、未发表手稿排除）由成员依据任务书与法规人工确定。']:
        p = doc.add_paragraph(style='List Bullet')
        r = p.add_run(t); cjk(r, BODY); r.font.size = Pt(10.5)

    doc.add_heading('四、已知局限与保留', 2)
    for t in ['B5 的教师／管理员诉求来自 AI 角色推演，不是访谈结果；报告与 SRS 中均已标注来源为推演（SRC-B5）；',
              '作业 1 走查样本范围有限：学生问卷 20 份，无教师与管理员答卷，结论不外推；',
              '作业 2 的追溯矩阵是设计追溯，不等于实现或测试通过；',
              '活动图的动作节点在 CodeArts 中显示 `<<State>>` 构造型，属平台外观差异，经人工判断不影响图意与追溯。']:
        p = doc.add_paragraph(style='List Bullet')
        r = p.add_run(t); cjk(r, BODY); r.font.size = Pt(10.5)

    doc.add_heading('五、与其他文档的一致性', 2)
    para(doc, '本声明与各文档内嵌的 AI 使用说明保持一致，包括：作业 1 需求调研报告附录 C、'
              'B1《SRS》第 1.3 节（SRC-B5）与第 6.2 节数据来源说明、'
              '《核心模块开发规范 SPEC》末节「AI 使用记录」、《A2 CodeArts 图集导入与占位说明》末节。'
              '如各处表述有冲突，以本声明为准，并同步修订相应文档。')

    doc.add_heading('六、签名', 2)
    table(doc, ['团队名称', '成员（姓名／学号）', '签署日期'], [['', '', ''], ['', '', ''], ['', '', '']],
          widths=[4.0, 8.0, 4.0])

    path = OUT / '作业2-AI使用声明.docx'
    doc.save(path)
    return path


if __name__ == '__main__':
    for f in (change_log(), ai_statement()):
        print(f'{f.name}  ({f.stat().st_size // 1024} KB)')
