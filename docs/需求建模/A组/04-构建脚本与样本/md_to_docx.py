"""Convert the project's Markdown deliverables to Word (.docx).

The submission list asks for the SRS and the SPEC as Word documents, and the
Markdown originals are the single source of truth, so this renders them rather
than maintaining a second hand-edited copy.

Supported: ATX headings, GFM pipe tables, bullet/numbered lists, blockquotes,
fenced code blocks, images, and inline **bold** / `code` / [links](url).
Uses python-docx only - no LibreOffice or anything else external.

Usage: python3 md_to_docx.py <input.md> <output.docx> ["文档标题"]
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

from docx import Document
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor
from PIL import Image

BODY_FONT, HEAD_FONT, MONO_FONT = '宋体', '黑体', 'Consolas'
CONTENT_WIDTH_CM = 16.0
NAVY = RGBColor(0x24, 0x36, 0x4B)


def set_cjk(run_or_style, font: str) -> None:
    """python-docx only writes the latin typeface; CJK text needs w:eastAsia too."""
    target = run_or_style.font if hasattr(run_or_style, 'font') else run_or_style
    target.name = font
    rPr = (run_or_style._element.get_or_add_rPr() if hasattr(run_or_style, '_element')
           else run_or_style.element.get_or_add_rPr())
    rFonts = rPr.find(qn('w:rFonts'))
    if rFonts is None:
        rFonts = OxmlElement('w:rFonts'); rPr.append(rFonts)
    for attr in ('w:ascii', 'w:hAnsi', 'w:eastAsia', 'w:cs'):
        rFonts.set(qn(attr), font)


def init_styles(doc: Document) -> None:
    normal = doc.styles['Normal']
    normal.font.size = Pt(10.5)
    set_cjk(normal, BODY_FONT)
    normal.paragraph_format.space_after = Pt(4)
    normal.paragraph_format.line_spacing = 1.25
    for i, (size, font) in enumerate([(18, HEAD_FONT), (15, HEAD_FONT), (13, HEAD_FONT), (11.5, HEAD_FONT)], 1):
        st = doc.styles[f'Heading {i}']
        st.font.size = Pt(size)
        st.font.color.rgb = NAVY
        set_cjk(st, font)
        st.paragraph_format.space_before = Pt(12 if i <= 2 else 8)
        st.paragraph_format.space_after = Pt(5)


def add_page_number(doc: Document) -> None:
    para = doc.sections[0].footer.paragraphs[0]
    para.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = para.add_run()
    for instr, kind in (('begin', None), (None, 'PAGE'), ('end', None)):
        if kind:
            el = OxmlElement('w:instrText'); el.set(qn('xml:space'), 'preserve'); el.text = ' PAGE '
        else:
            el = OxmlElement('w:fldChar'); el.set(qn('w:fldCharType'), instr)
        run._r.append(el)


INLINE = re.compile(r'(\*\*[^*]+\*\*|\*[^*]+\*|`[^`]+`|\[[^\]]+\]\([^)]+\))')


def add_runs(para, text: str) -> None:
    for part in INLINE.split(text):
        if not part:
            continue
        if part.startswith('**') and part.endswith('**'):
            r = para.add_run(part[2:-2]); r.bold = True
        elif part.startswith('*') and part.endswith('*'):
            r = para.add_run(part[1:-1]); r.italic = True
        elif part.startswith('`') and part.endswith('`'):
            r = para.add_run(part[1:-1]); set_cjk(r, MONO_FONT); r.font.size = Pt(9.5)
        elif part.startswith('['):
            label, url = re.match(r'\[([^\]]+)\]\(([^)]+)\)', part).groups()
            r = para.add_run(label); r.font.underline = True; r.font.color.rgb = RGBColor(0x1F, 0x4E, 0x79)
            if not label.startswith('http'):
                r2 = para.add_run(f'（{url}）'); r2.font.size = Pt(8.5)
                r2.font.color.rgb = RGBColor(0x5D, 0x71, 0x83)
        else:
            r = para.add_run(part)
        set_cjk(r, r.font.name or BODY_FONT)


def add_image(doc: Document, path: Path) -> None:
    iw, ih = Image.open(path).size
    width = Cm(CONTENT_WIDTH_CM)
    if ih / iw > 1.15:                       # tall figures: cap the height too
        width = Cm(min(CONTENT_WIDTH_CM, 12.0))
    p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.add_run().add_picture(str(path), width=width)
    p.paragraph_format.space_after = Pt(10)



def set_table_borders(table) -> None:
    """Write explicit borders: some renderers ignore the Table Grid style."""
    tblPr = table._tbl.tblPr
    borders = OxmlElement('w:tblBorders')
    for edge in ('top', 'left', 'bottom', 'right', 'insideH', 'insideV'):
        el = OxmlElement(f'w:{edge}')
        el.set(qn('w:val'), 'single'); el.set(qn('w:sz'), '6')
        el.set(qn('w:space'), '0'); el.set(qn('w:color'), '9AB3C7')
        borders.append(el)
    tblPr.append(borders)


def shade(cell, fill: str) -> None:
    tcPr = cell._tc.get_or_add_tcPr()
    el = OxmlElement('w:shd')
    el.set(qn('w:val'), 'clear'); el.set(qn('w:color'), 'auto'); el.set(qn('w:fill'), fill)
    tcPr.append(el)


def add_table(doc: Document, rows: list[list[str]]) -> None:
    header, body = rows[0], rows[1:]
    t = doc.add_table(rows=1, cols=len(header))
    t.style = 'Table Grid'
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    set_table_borders(t)
    for i, cell in enumerate(header):
        shade(t.rows[0].cells[i], 'EAF1F8')
        para = t.rows[0].cells[i].paragraphs[0]
        para.paragraph_format.space_after = Pt(2)
        add_runs(para, cell)
        for r in para.runs:
            r.bold = True
            r.font.size = Pt(9.5)
    for row in body:
        cells = t.add_row().cells
        for i, cell in enumerate(row[:len(header)]):
            para = cells[i].paragraphs[0]
            para.paragraph_format.space_after = Pt(2)
            add_runs(para, cell)
            for r in para.runs:
                r.font.size = Pt(9.5)
    doc.add_paragraph().paragraph_format.space_after = Pt(2)


def split_row(line: str) -> list[str]:
    return [c.strip() for c in line.strip().strip('|').split('|')]


def is_sep(line: str) -> bool:
    return bool(re.fullmatch(r'\|[\s:|-]+\|', line.strip())) and '-' in line


def convert(src: Path, dst: Path, title: str | None = None) -> None:
    lines = src.read_text(encoding='utf-8').split('\n')
    doc = Document()
    init_styles(doc); add_page_number(doc)
    for s in doc.sections:
        s.top_margin = s.bottom_margin = Cm(2.2)
        s.left_margin = s.right_margin = Cm(2.5)

    i, first_h1 = 0, True
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        if stripped.startswith('```'):                       # fenced code
            i += 1; buf = []
            while i < len(lines) and not lines[i].strip().startswith('```'):
                buf.append(lines[i]); i += 1
            i += 1
            p = doc.add_paragraph()
            p.paragraph_format.left_indent = Cm(0.6)
            p.paragraph_format.space_after = Pt(8)
            r = p.add_run('\n'.join(buf)); set_cjk(r, MONO_FONT); r.font.size = Pt(9)
            continue

        if stripped.startswith('|') and i + 1 < len(lines) and is_sep(lines[i + 1]):
            rows = [split_row(stripped)]; i += 2
            while i < len(lines) and lines[i].strip().startswith('|'):
                rows.append(split_row(lines[i])); i += 1
            add_table(doc, rows); continue

        if stripped.startswith('!'):
            m = re.match(r'!\[[^\]]*\]\(([^)\s]+)\)', stripped)
            if m:
                img = (src.parent / m.group(1)).resolve()
                if img.exists():
                    add_image(doc, img)
                else:
                    doc.add_paragraph(f'[缺图：{m.group(1)}]')
                i += 1; continue

        if stripped.startswith('#'):
            level = len(stripped) - len(stripped.lstrip('#'))
            text = stripped[level:].strip()
            if level == 1 and first_h1:
                h = doc.add_heading(title or text, 0)
                for r in h.runs:
                    set_cjk(r, HEAD_FONT)
                first_h1 = False
            else:
                doc.add_heading(text, min(level, 4))
            i += 1; continue

        if re.fullmatch(r'\*(图|表)\s*[^ ]*\*', stripped):
            p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            p.paragraph_format.space_before = Pt(2)
            p.paragraph_format.space_after = Pt(10)
            r = p.add_run(stripped.strip('*'))
            set_cjk(r, BODY_FONT); r.font.size = Pt(9)
            r.font.color.rgb = RGBColor(0x44, 0x55, 0x66)
            i += 1; continue

        if stripped.startswith('>'):
            buf = []
            while i < len(lines) and lines[i].strip().startswith('>'):
                buf.append(lines[i].strip().lstrip('>').strip()); i += 1
            p = doc.add_paragraph()
            p.paragraph_format.left_indent = Cm(0.8)
            p.paragraph_format.space_after = Pt(6)
            add_runs(p, ' '.join(x for x in buf if x))
            for r in p.runs:
                r.font.color.rgb = RGBColor(0x44, 0x55, 0x66); r.italic = True
                r.font.size = Pt(9.5)
            continue

        if re.match(r'^[-*]\s+', stripped):
            p = doc.add_paragraph(style='List Bullet')
            add_runs(p, re.sub(r'^[-*]\s+', '', stripped))
            i += 1; continue

        if re.match(r'^\d+\.\s+', stripped):
            p = doc.add_paragraph(style='List Number')
            add_runs(p, re.sub(r'^\d+\.\s+', '', stripped))
            i += 1; continue

        if stripped in ('---', '***', '___'):
            p = doc.add_paragraph(); p.paragraph_format.space_after = Pt(2)
            pPr = p._p.get_or_add_pPr(); bd = OxmlElement('w:pBdr'); bot = OxmlElement('w:bottom')
            bot.set(qn('w:val'), 'single'); bot.set(qn('w:sz'), '6')
            bot.set(qn('w:color'), 'C9D9E5'); bd.append(bot); pPr.append(bd)
            i += 1; continue

        if not stripped:
            i += 1; continue

        add_runs(doc.add_paragraph(), stripped)
        i += 1

    dst.parent.mkdir(parents=True, exist_ok=True)
    doc.save(dst)
    print(f'{dst.name}  ({len(doc.paragraphs)} 段, {len(doc.tables)} 表, {dst.stat().st_size // 1024} KB)')


if __name__ == '__main__':
    convert(Path(sys.argv[1]), Path(sys.argv[2]), sys.argv[3] if len(sys.argv) > 3 else None)
