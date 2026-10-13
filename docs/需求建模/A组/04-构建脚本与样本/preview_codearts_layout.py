"""Local layout preview for the generated CodeArts canvases.

This is a build-time sanity check, not a deliverable: it reads the mxGraph
canvas XML straight out of the generated ZIPs and draws a rough approximation
so overlaps and broken routing are visible before the user imports anything.
The output must never be presented as a CodeArts export.
"""

from __future__ import annotations

import io
import json
import math
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent
A_GROUP = HERE.parent
ASSIGNMENT = A_GROUP.parent
ZIP_DIR = A_GROUP / '02-模型图' / 'CodeArts待导入ZIP'
OUT = ASSIGNMENT / '.build_codearts'
FONT_PATH = '/System/Library/Fonts/Hiragino Sans GB.ttc'
F = ImageFont.truetype(FONT_PATH, 15)
FS = ImageFont.truetype(FONT_PATH, 13)
FT = ImageFont.truetype(FONT_PATH, 26)

INK, LINE, BLUE, AMBER, GREY, LANE = '#24364b', '#43637d', '#eaf3fb', '#fff2dc', '#f3f3f3', '#f7fbfe'


def parse(canvas: bytes):
    root = ET.fromstring(canvas)
    verts, edges, lanes, titles = [], [], [], []
    for o in root.findall('./root/object'):
        cell = o.find('mxCell')
        geo = cell.find('mxGeometry')
        style = cell.get('style') or ''
        rec = {
            'id': o.get('id'), 'type': o.get('type') or '', 'style': style,
            'x': int(float(geo.get('x', 0))), 'y': int(float(geo.get('y', 0))),
            'w': int(float(geo.get('width', 0))), 'h': int(float(geo.get('height', 0))),
            'label': (o.get('label') or cell.get('value') or ''),
        }
        if cell.get('edge') == '1':
            pts = [(int(float(p.get('x'))), int(float(p.get('y'))))
                   for p in cell.findall('./mxGeometry/Array/mxPoint')]
            edges.append({'src': cell.get('source'), 'tgt': cell.get('target'),
                          'waypoints': pts, 'label': rec['label']})
        elif o.get('type') == 'Partition':
            (lanes if rec['w'] > 100 else titles).append(rec)
        else:
            verts.append(rec)
    return lanes, titles, verts, edges



def plain(html: str) -> str:
    txt = html.replace('&lt;', '<').replace('&gt;', '>').replace('&quot;', '"')
    out, keep = [], False
    for ch in txt:
        if ch == '<':
            keep = False
        elif ch == '>':
            keep = True
        elif keep:
            out.append(ch)
    s = ''.join(out)
    for tag in ('<<State>>', '<<Action>>', '<<Decision>>', '<<Partition>>', '<<Final>>'):
        s = s.replace(tag, '')
    return s.strip()


def centre(v):
    return v['x'] + v['w'] // 2, v['y'] + v['h'] // 2


def arrow(d, pts, color=LINE):
    d.line(pts, fill=color, width=2, joint='curve')
    (x0, y0), (x1, y1) = pts[-2], pts[-1]
    a = math.atan2(y1 - y0, x1 - x0)
    L = 11
    d.polygon([(x1, y1),
               (x1 - L * math.cos(a - .45), y1 - L * math.sin(a - .45)),
               (x1 - L * math.cos(a + .45), y1 - L * math.sin(a + .45))], fill=color)


def label_anchor(pts):
    """Midpoint of the longest segment - where mxGraph would put the label."""
    best, at = -1, pts[0]
    for i in range(1, len(pts)):
        (x0, y0), (x1, y1) = pts[i - 1], pts[i]
        seg = math.hypot(x1 - x0, y1 - y0)
        if seg > best:
            best, at = seg, ((x0 + x1) // 2, (y0 + y1) // 2)
    return at


def route(src, tgt, waypoints):
    """Approximate mxGraph's orthogonal routing for layout review."""
    sx, sy = centre(src)
    tx, ty = centre(tgt)
    pts = [(sx, sy)] + list(waypoints) + [(tx, ty)]
    out = [pts[0]]
    for i in range(1, len(pts)):
        px, py = out[-1]
        x, y = pts[i]
        if px != x and py != y:
            out.append((x, py))          # single elbow
        out.append((x, y))
    return out


def render(zip_path: Path, out_dir: Path):
    with zipfile.ZipFile(zip_path) as z:
        root = z.namelist()[0].split('/')[0]
        data = z.read(f'{root}/2_data.zip')
    with zipfile.ZipFile(io.BytesIO(data)) as d:
        dias = json.loads(d.read('2_data/4_diagram/0/diagrams.json'))
        canvases = {n.rsplit('/', 1)[-1][:-4]: d.read(n)
                    for n in d.namelist() if n.endswith('.xml')}
    made = []
    for dia in dias:
        canvas = canvases.get(dia['uuid'])
        if canvas is None:
            continue
        lanes, titles, verts, edges = parse(canvas)
        g = ET.fromstring(canvas)
        W = int(g.get('pageWidth', 1200))
        H = int(g.get('pageHeight', 900))
        pad = 40
        im = Image.new('RGB', (W + pad * 2, H + pad * 2 + 40), 'white')
        dr = ImageDraw.Draw(im)
        dr.text((pad, 18), f"{dia['name']}  · 本地布局预览（非 CodeArts 导出）", font=FT, fill=INK)
        off = (pad, pad + 40)

        def T(v):
            return v['x'] + off[0], v['y'] + off[1]

        for lane in lanes:
            x, y = T(lane)
            dr.rectangle((x, y, x + lane['w'], y + lane['h']),
                         fill=LANE, outline='#9AB3C7', width=1)
        for title in titles:
            x, y = T(title)
            dr.rectangle((x, y, x + title['w'], y + title['h']),
                         fill='#e4eef6', outline='#9AB3C7', width=1)
            # label is one character per line -> draw the glyphs stacked
            chars = [c for c in plain(title['label']) if not c.isspace()]
            step = 20
            top = y + title['h'] // 2 - (len(chars) - 1) * step // 2
            for i, ch in enumerate(chars):
                dr.text((x + title['w'] // 2, top + i * step), ch, font=F,
                        fill='#1F4E79', anchor='mm')

        byid = {v['id']: v for v in verts}
        pending = []
        for e in edges:
            s, t = byid.get(e['src']), byid.get(e['tgt'])
            if not s or not t:
                continue
            pts = [(px + off[0], py + off[1]) for px, py in route(s, t, e['waypoints'])]
            arrow(dr, pts)
            if e['label']:
                pending.append((label_anchor(pts), plain(e['label'])))

        for v in verts:
            x, y = T(v)
            box = (x, y, x + v['w'], y + v['h'])
            if 'startState' in v['style']:
                dr.ellipse(box, fill='#4D4D4D')
            elif 'endState' in v['style']:
                dr.ellipse(box, fill='white', outline='#4D4D4D', width=2)
                dr.ellipse((x + 8, y + 8, x + v['w'] - 8, y + v['h'] - 8), fill='#4D4D4D')
            elif 'rhombus' in v['style']:
                dr.polygon([(x + v['w'] // 2, y), (x + v['w'], y + v['h'] // 2),
                            (x + v['w'] // 2, y + v['h']), (x, y + v['h'] // 2)],
                           fill=AMBER, outline=LINE)
                label = plain(v['label'])
                dr.multiline_text((x + v['w'] // 2, y + v['h'] // 2), label, font=FS,
                                  fill=INK, anchor='mm', align='center')
            else:
                dr.rounded_rectangle(box, radius=10, fill=BLUE, outline=LINE, width=2)
                label = plain(v['label'])
                dr.multiline_text((x + v['w'] // 2, y + v['h'] // 2), label, font=FS,
                                  fill=INK, anchor='mm', align='center')
        for (lx, ly), text in pending:
            b = dr.textbbox((lx, ly), text, font=FS, anchor='mm')
            dr.rectangle((b[0] - 4, b[1] - 2, b[2] + 4, b[3] + 2), fill='white',
                         outline='#e0c9c4')
            dr.text((lx, ly), text, font=FS, fill='#8a2b1f', anchor='mm')
        out = out_dir / (zip_path.stem + '--' + dia['name'].replace('/', '_') + '.png')
        im.save(out)
        made.append(out)
    return made


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    for f in sorted(ZIP_DIR.glob('A2-*.zip')):
        for p in render(f, OUT):
            print(p.relative_to(ASSIGNMENT))


if __name__ == '__main__':
    main()
