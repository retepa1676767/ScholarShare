"""Rasterise the CodeArts SVG exports to PNG at 2x for Word/PPT insertion.

CodeArts writes HTML labels into <foreignObject> with a "[Not supported by
viewer]" <text> fallback, so a plain SVG rasteriser (rsvg/cairosvg) would
render the placeholder instead of the real label.  A Blink/WebKit engine
renders the foreignObject correctly, so this drives headless Chrome.

Usage: python3 export_svg_png.py [目录]
"""

from __future__ import annotations

import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

CHROME = Path('/Applications/Google Chrome.app/Contents/MacOS/Google Chrome')
SCALE = 2


def svg_size(svg: Path) -> tuple[int, int]:
    raw = svg.read_text(encoding='utf-8', errors='ignore')
    m = re.search(r'<svg[^>]*?width="(\d+(?:\.\d+)?)px"[^>]*?height="(\d+(?:\.\d+)?)px"', raw)
    if not m:
        m = re.search(r'<svg[^>]*?height="(\d+(?:\.\d+)?)px"[^>]*?width="(\d+(?:\.\d+)?)px"', raw)
        if m:
            return int(float(m.group(2))), int(float(m.group(1)))
        raise SystemExit(f'{svg.name}: 无法解析尺寸')
    return int(float(m.group(1))), int(float(m.group(2)))


def render(svg: Path, out: Path) -> None:
    w, h = svg_size(svg)
    with tempfile.TemporaryDirectory() as tmp:
        raw = svg.read_text(encoding='utf-8', errors='ignore')
        # a transparent background becomes black in some viewers; force white
        if 'background-color' not in raw:
            raw = raw.replace('<svg', '<svg style="background-color:#ffffff"', 1)
        tmp_svg = Path(tmp) / 'in.svg'
        tmp_svg.write_text(raw, encoding='utf-8')
        cmd = [str(CHROME), '--headless', '--disable-gpu', '--hide-scrollbars',
               f'--force-device-scale-factor={SCALE}',
               f'--screenshot={out}', f'--window-size={w},{h}',
               f'--virtual-time-budget=4000', tmp_svg.as_uri()]
        subprocess.run(cmd, check=True, capture_output=True)
    if not out.exists():
        raise SystemExit(f'{svg.name}: Chrome 未产出 PNG')


def main() -> None:
    if not CHROME.exists():
        raise SystemExit(f'未找到 Chrome：{CHROME}')
    target = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path(__file__).resolve().parent.parent / '02-模型图' / '流程与状态图'
    svgs = sorted(target.glob('*.svg'))
    if not svgs:
        raise SystemExit(f'{target} 下没有 .svg')
    for svg in svgs:
        out = svg.with_suffix('.png')
        render(svg, out)
        from PIL import Image
        w, h = Image.open(out).size
        print(f'  {svg.name}  ->  {out.name}  ({w}x{h}, {out.stat().st_size // 1024} KB)')


if __name__ == '__main__':
    main()
