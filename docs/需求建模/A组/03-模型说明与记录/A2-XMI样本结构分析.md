# A2：CodeArts XMI 样本结构分析与模型视图问题

## 用户样本逐项解释

样本：`/Users/hjl/Downloads/用例图.xmi`。这是 CodeArts 从已有用例图所在包导出的 XMI。其 XML 树如下：

| XML 部分 | 含义 | 是否是图视图 |
| --- | --- | --- |
| `<?xml version="1.0" encoding="UTF-8"?>` | XML 声明和编码 | 否 |
| `<xmi:XMI>` 与 `xmlns:xmi`、`xmlns:uml` | XMI 容器和 UML 类型命名空间 | 否 |
| `<xmi:Documentation exporter="Modeling" .../>` | 导出工具元信息 | 否 |
| `<uml:Model xmi:type="uml:Model" name="CM_Model">` | UML 模型根；`CM_Model` 是模型名 | 否 |
| `<packagedElement ... name="用例图" xmi:type="uml:Package">` | 名为“用例图”的**包/工程树目录**，不是 Diagram 或图画布 | 否 |
| `xmi:type="uml:Actor"` 的“学生” | 参与者模型元素 | 否 |
| `xmi:type="uml:UseCase"` 的“提交保修单”“保修”“反馈意见” | 用例模型元素 | 否 |
| “保修”内的 `<include addition="提交保修单ID" includingCase="保修ID" .../>` | 保修包含提交保修单的 UML 语义关系；ID 指向两个用例元素 | 否 |
| “反馈意见”内的 `<extend extendedCase="自身ID" extension="自身ID" .../>` | UML 扩展关系，但样本中两端都是同一个用例，不能据此推断真实跨用例关系；可能是导出瑕疵 | 否 |
| `xmi:id` | 模型元素及关系的唯一标识，供引用 | 否 |

样本中没有 `Diagram`/`UMLDiagram`、图形节点、坐标、尺寸、系统边界框或画布中的“Use”关联线。由此可判断：**该导出文件只能说明模型元素及部分语义关系，不能还原原图的视觉布局或图视图节点。** 这与用户成功导入新版 XMI 后只看到 Actor 和 UseCase、没有图视图的结果一致。

用户曾描述 CodeArts 原工程中存在同名“用例图”空视图和“yl”视图。仅看 XMI 时无法核对：全文没有 `yl` 字符串，也没有任何 Diagram/View 类型节点或“元素→图”的引用。XMI 中唯一名为“用例图”的节点明确是 `xmi:type="uml:Package"`。

**后续验证**：用户已提供模型工程 ZIP。其 `diagrams.json` 明确记录名为 `yl` 的视图及所属“用例图”包；对应 XML 保存了 4 个业务元素、4 条连线、系统边界和坐标。XMI 元素 ID 与 ZIP 中业务元素 UUID 一致。该 ZIP 的 `diagrams.json` **没有名为“用例图”的图视图记录**，因此目前证据显示“用例图”是包名，`yl` 才是该包下的图；可能是界面上的包/图层级被误认为两张图。见 `A2-CodeArts模型工程ZIP绘图可行性评估.md`。

## 对 A2 文件的结论

`A2-系统用例图.xmi` 已经按照样本支持的结构重写，且用户已确认成功导入 4 个参与者和 6 个用例。将包改名“用例图”只会改工程树目录名，不会创建图视图。把自造的 `uml:Diagram`、UMLDI 或 CodeArts 未公开的节点硬塞进 XMI，无法由样本证明 CodeArts 会识别，且可能再次触发“文件校检失败”。因此目前没有证据支持生成“导入 XMI 后自动出现图视图”的文件。

华为官方产品功能说明分别列出“导出 XMI”和“导出模型工程”，后者明确包含“包、图、元素、连线”。如需要可导入的 CodeArts 原生图视图，应取得一份**同一工程导出的模型工程 ZIP**，检查其中图、节点、连线和坐标的 JSON 结构，再评估能否用该格式生成 A2 图。官方常见问题中的导入示例也采用 ZIP，并提供检查与冲突处理步骤。

参考：

- <https://support.huaweicloud.com/productdesc-codeartsmodeling/modeling_pdtd_0003.html>
- <https://support.huaweicloud.com/codeartsmodeling_faq/modeling_faq_0000_6.html>

> **文件状态提示（2026-10-12 整理）**：本文引用的 `A2-系统用例图.xmi` 在本文件撰写时存在于 `A组/`，但在本次目录整理时**已不在工作区**。请在提交前确认是有意删除还是需要恢复（两处 XMI 与「备选」模型工程 ZIP 均可由 `../04-构建脚本与样本/` 下的脚本重新生成）。
