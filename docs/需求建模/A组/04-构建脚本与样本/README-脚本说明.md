# 04-构建脚本与样本

本目录存放生成 A 组图件的脚本与原始样本。**目录内的脚本按需重跑，产物写到 `../02-模型图/` 对应目录**，不会留在本目录。

## 文件

| 文件 | 用途 | 产物位置 |
| --- | --- | --- |
| `build_codearts_diagrams.py` | 生成活动图、两张状态图与 SPEC 四图共四个 CodeArts 模型工程 ZIP | `../02-模型图/CodeArts待导入ZIP/` |
| `preview_codearts_layout.py` | 读取上述 ZIP 的画布 XML，画成本地布局预览 PNG 供交付前自检 | `../../.build_codearts/` |
| `build_a2_codearts_zip.py` | 生成用例图模型工程 ZIP（`uml` 模式＝试验版，`sample` 模式＝备选版） | `../02-模型图/用例图/` |
| `build_a2_codearts_xmi.py` | 生成 `A2-系统用例图.xmi` | `../02-模型图/用例图/` |
| `render_a1_diagrams.py` | 绘制三张流程/状态图的 PNG 参照图（语义源是同名 `.mmd`） | `../02-模型图/流程与状态图/` |
| `export_svg_png.py` | 把 CodeArts 导出的 `.svg` 批量转为 2× PNG（用无头 Chrome，因标签在 `foreignObject` 里，严格 SVG 渲染器会画成占位文字） | 与 `.svg` 同目录，同名 `.png` |
| `make_deck_pptx.py` | 生成 17 页作业 1＋作业 2 合并汇报稿；`--only N <输出>` 只生成第 N 页（供逐页预览） | `../../提交版/作业2-学术成果分享平台-汇报稿-v3.pptx` |
| `md_to_docx.py` | Markdown → Word（标题层级、GFM 表格、项目符号、引用块、插图、页码、显式表格边框） | 指定输出路径 |
| `make_docs.py` | 生成《修改说明与版本记录表》（横向 A4）与《AI 使用声明》 | `../../提交版/` |
| `test1_master_20261012184125.zip` | 用户提供的 CodeArts 导出样本，**未修改**。所有 ZIP 生成脚本都从它克隆结构与形状模板 | — |

## 运行方式

```bash
cd docs/需求建模/A组/04-构建脚本与样本
python3 build_codearts_diagrams.py      # 重建 4 个待导入 ZIP
python3 preview_codearts_layout.py      # 重建本地布局预览
python3 build_a2_codearts_zip.py uml    # 重建用例图试验版 ZIP
python3 build_a2_codearts_xmi.py        # 重建 A2-系统用例图.xmi
python3 render_a1_diagrams.py           # 重建三张流程/状态图 PNG
python3 export_svg_png.py               # 把 02-模型图/流程与状态图/*.svg 转成 2x PNG
python3 make_deck_pptx.py               # 重建 17 页合并汇报稿
python3 md_to_docx.py <in.md> <out.docx> [标题]   # Markdown 转 Word
python3 make_docs.py                    # 生成修改说明表与 AI 使用声明
python3 make_deck_pptx.py --only 6 /tmp/s6.pptx   # 只出第 6 页，供预览
python3 export_svg_png.py <目录>         # 指定其它目录
```

依赖：标准库 + `pillow`；`export_svg_png.py` 另需 `/Applications/Google Chrome.app`（无浏览器内核的机器上无法正确渲染 CodeArts 的 SVG 标签）。

### 逐页预览汇报稿（用 macOS 自带 Quick Look，不依赖 LibreOffice）

系统自带的 `Office.qlgenerator` 能按真实字体渲染 pptx，但一次只出一张（首页）。逐页预览的做法是「每页单独出一个 pptx，再各自 Quick Look」：

```bash
for i in $(seq 1 14); do
  python3 make_deck_pptx.py --only $i /tmp/one/s$i.pptx
done
qlmanage -t -s 1600 -o /tmp/one /tmp/one/*.pptx   # 产出 sN.pptx.png
```

预览图仅用于版面自检，不是交付物。

## 注意事项

1. **样本不要改**。`test1_master_20261012184125.zip` 是模型 ZIP 生成脚本的 CodeArts 格式依据。改样本会导致新生成的 ZIP 与已验证的用例图 ZIP 结构不一致。
2. **产物不是 CodeArts 导出物**。`preview_codearts_layout.py` 与 `render_a1_diagrams.py` 的输出是本地近似渲染，**不得作为 CodeArts 建模成果提交**；正式图必须在 CodeArts 中打开 ZIP 后导出。
3. **一致性自检**。`build_codearts_diagrams.py` 生成的每个 ZIP 都可用 `preview_codearts_layout.py` 复检；校验项包括外层/内层 SHA-512 匹配、JSON 与画布 XML 可解析、UUID 唯一、连线 `source`/`target` 可落到元素记录。本次四个新 ZIP 全部通过。
4. **历史脚本**。`build_a2_codearts_zip.py`、`build_a2_codearts_xmi.py` 是早期 XMI/模型工程方案的脚本，保留以便重新生成对应文件；其输出的用例图 ZIP 内部有少量悬空挂载引用（不影响 CodeArts 导入，用户已确认可导出 PNG）。新脚本 `build_codearts_diagrams.py` 的引用更干净。
