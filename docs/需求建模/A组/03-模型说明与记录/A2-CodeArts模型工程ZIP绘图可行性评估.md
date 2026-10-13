# A2 CodeArts 模型工程 ZIP 绘图可行性评估

## 结论

**可行，但交付格式应改为 CodeArts 模型工程 ZIP；原 XMI 不能承载所需图视图。** 用户提供的 `../04-构建脚本与样本/test1_master_20261012184125.zip` 含原生图记录、画布 XML、元素、连线及视图类型定义，足以作为生成 A2 用例图的结构样本。是否能被 CodeArts 成功导入及正确渲染，仍须以新文件的实际导入检查为准。

已据此生成两份 A2 ZIP：UML 用例图试验版及沿用样本 4+1 类型的备选版。文件选择、导入顺序和本地校验见 `A2-CodeArts-ZIP交付说明.md`。

## 样本中已确认的结构

| 文件/字段 | 作用 | 样本证据 |
| --- | --- | --- |
| 外层 `define.json` | 工程导出清单，指向 `1_meta.zip`、`2_data.zip`，保存其 SHA-512 摘要 | 摘要重算后与两份内层 ZIP 均匹配 |
| `1_meta/3_view_types.json` | 图视图类型定义 | `yl` 使用 4+1 View 的 `Usecase View / Usecase Model`；还存在 UML 的 `Use Case Diagram` 类型定义 |
| `2_data/1_package/0/package.json` | 工程树中的包 | “用例图”包 UUID 与原 XMI 的包 `xmi:id` 一致 |
| `2_data/4_diagram/0/diagrams.json` | 图视图记录及其包、类型、UUID | `yl` 视图 UUID `45c05e9b4f6d45a2bc6975ebb880c328`，所属“用例图”包 |
| `2_data/4_diagram/0/<图UUID>.xml` | mxGraph 画布，保存节点形状、位置、文字、连线和系统边界 | `yl.xml` 中有学生、三个用例、连线、维修系统 Boundary |
| `2_data/2_element/0/element.json` | 参与者/用例模型元素和图引用、坐标 | 4 个元素的 `diagram_uuid` 均指向 `yl`，UUID 与 XMI 元素 ID 一致 |
| `2_data/5_line/0/t_line.json` | 关联、include/extend 等连线记录 | `yl` 下有 4 条连线，分别指向画布上的对象 ID |

`yl` 画布 XML 共 10 个 `<object>`：4 个业务元素、4 条连线、1 个系统边界、1 个 Actor 文字挂载对象；其中系统边界和挂载文字只在画布 XML 中，不在 `element.json`。这说明仅补元素表仍不足以生成完整图面，必须同步构造 XML 与连线表。

`diagrams.json` 中只有一张属于“用例图”包的图：`yl`。没有名为“用例图”的图视图记录；“用例图”是包名。这个结论同时解释了 XMI 为什么只显示同名包，而完全没有 `yl`。

## 建议的 A2 生成方法

1. 以此 ZIP 为模板，保留 `1_meta.zip` 的视图类型定义，不修改用户原文件。
2. 在新包下建立“A2 学术成果分享平台系统用例图”图视图记录，选择 CodeArts 的 **UML → Use Case Diagram** 类型（更贴合课程“用例图”要求）；如该类型的画布样式兼容性出现问题，再以样本已验证的 4+1 用例模型类型作为备选。
3. 在图 XML 中放入 4 个 Actor、6 个 UseCase、系统边界和 7 条关联线；同步创建 `element.json`、`t_line.json` 的对应记录，并确保所有 UUID、source/target、diagram_uuid、packageuuid 一致。
4. 移除模板中的无关示例包、图、元素和连线；保留导入所需元数据及空 JSON 文件，重新压缩内层 ZIP，计算 SHA-512 后更新 `define.json`，形成新的模型工程 ZIP。
5. 本地检查 JSON/XML 可解析、ID 唯一、跨文件引用完整、摘要一致；随后在 CodeArts 以**新建模型工程**导入并检查画布、连线、图类型和可编辑性，再导出 PNG 和可编辑源文件。

## 风险与验证点

- ZIP 是平台内部导出格式；样本足以仿造结构，但平台可能额外校验版本、作者、工程类型或图类型组合。本地一致性检查不能替代实际导入。
- 样本 `yl` 是 **4+1 用例模型**，不是 UML 分类下的“Use Case Diagram”。若直接更换图类型 ID，需在 CodeArts 实测是否保留画布和工具箱功能。
- 原样本的 XMI 对 `extend` 的两端记录不可靠；A2 设计不需要 include/extend，不应照抄。
- 导入前应避免覆盖已有工程；建议导入到新工程核验，成功后再作为正式图源交付。
