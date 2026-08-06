# 正式科研流程图的无图标边界与图像型例外

本规范用于流程图、研究设计、技术路线、病例流转、方法架构、机制示意和图形摘要。论文、学位论文、开题报告、基金标书、研究报告与正式 PPT 中的研究流程均按正式科研流程处理。正式科研流程默认采用 L0：只用准确文字、编号、边界、节点和箭头，不使用 emoji、pictogram、clip-art、装饰性小图标或图标化阶段标签。图形摘要、机制示意和科普/教学插图只有在大型图形对象承担真实内容编码时才使用图像型例外。

## 目录

1. 调研依据
2. 正式流程图的强制边界
3. 方法图元与小图标的区别
4. 图像型例外
5. 版式与配色
6. 提示词字段
7. 交付前检查

## 1. 调研依据

| 来源 | 可迁移原则 |
| --- | --- |
| [PLOS Computational Biology: Ten Simple Rules for Better Figures](https://journals.plos.org/ploscompbiol/article?id=10.1371/journal.pcbi.1003833) | 图形服从受众和核心消息；元素在最终尺寸下清楚；颜色必须有明确用途 |
| [PLOS Biology: Creating clear and informative image-based figures](https://journals.plos.org/plosbiology/article?id=10.1371/journal.pbio.3001161) | 检查灰度与色觉缺陷可读性；颜色与形状、线型或标签双重编码 |
| [W3C Images Tutorial](https://www.w3.org/WAI/tutorials/images/) | 区分信息型与装饰型图像；装饰元素过多会增加噪声，复杂图需要等价文字说明 |
| [W3C G207: Contrast for icons](https://www.w3.org/WAI/WCAG22/Techniques/general/G207) | 只有理解内容所必需的图形符号才进入信息层，并与背景保持足够对比 |
| [Microsoft Fluent 2 Iconography](https://fluent2.microsoft.design/iconography) | 图标要使用可识别的字面隐喻，小尺寸必须减少细节；本规范只把这一原则用于合法图像型例外 |
| [IBM Pictogram Usage](https://www.ibm.com/design/language/iconography/pictograms/usage/) 与 [Design](https://www.ibm.com/design/language/iconography/pictograms/design/) | pictogram 需要统一网格、留白、笔画和色彩；正式科研流程不因能够统一而自动需要 pictogram |
| [GOV.UK Design System: Images](https://design-system.service.gov.uk/styles/images/) | 多数情况下避免无必要图标；一个图标不能同时代表多个概念 |

以下 L0 边界是 EpiAgentKit 对正式科研流程图的本地交付规则，不是期刊通则。用户、学校、期刊或机构的明确模板优先，但不能用装饰图标替代科学内容和关系。

## 2. 正式流程图的强制边界

下列图默认且通常保持 L0：

- 论文、学位论文和开题报告中的研究流程、研究设计和技术路线；
- 基金标书、研究报告与正式 PPT 中的研究实施路径；
- CONSORT、病例筛选、病例流转、样本纳排和分析集流程；
- 数据链接、清洗、缺失核查、质量控制、暴露评估和统计分析路径；
- 方法架构、模型流程和验证路线中的阶段与容器层。

L0 使用文字、编号、矩形或其它有关系含义的形状、分组边界、线型和箭头。禁止：

1. emoji 或把 Unicode 表情符号当作阶段标记、项目符号或结果标记；
2. 数据库、表格、清单、漏斗、文档、人物、医院、显微镜、试管、芯片、奖杯等小图标；
3. icon、pictogram、clip-art、贴纸、徽章、装饰圆点或图标化序号；
4. 在左侧阶段栏、节点标题前、结果框内或每个分支旁机械放置小图标；
5. 用图标重复“数据源、质量控制、统计分析、结果输出”等已经由文字清楚表达的标签。

阶段识别使用编号、标题层级、边界、位置、明度和有限语义色。结果输出写明实际产物名称，不放文档、论文或奖杯图标。无图标后的空白通过调整节点、间距和分组解决，不用新装饰填补。

## 3. 方法图元与小图标的区别

方法图元是研究内容本身，不是 icon。只有同时满足以下条件才可进入正式方法架构：

1. 对应来源材料中真实存在的输入、变换或输出，例如波形、矩阵、网格、时间轴、特征图、序列、关系网络或真实设备轮廓；
2. 删除后会损失方法含义，而不只是降低页面“丰富度”；
3. 与具体节点直接结合并有准确标签，不作为阶段栏装饰或独立悬浮符号；
4. 在最终尺寸下能够辨认，不缩成类似小图标的噪声；
5. 不使用伪统计图、随机热图、假坐标、通用 AI 脑或抽象科研符号代替真实方法。

数据库圆柱、漏斗、勾选清单和文档轮廓若只表示字面阶段名称，属于小图标而不是方法图元，必须删除。

## 4. 图像型例外

以下场景可以使用大型图形对象，但不能回流到正式流程图的小图标规则：

- 图形摘要中的研究对象、器官、暴露场景、机制过程或主要输出；
- 机制示意中的真实实体、组织层级或作用路径；
- 科普/教学插图中的对象结构和操作步骤；
- 网页内容插图、卡片插图和空状态；界面控制图标继续复用项目既有图标系统。

图像型例外必须满足：用户要求或最终使用位置确实需要图像表达；对象承担真实内容编码；采用少量大型主体而不是重复小图标；图形与标签、箭头和证据边界一致。即使属于例外，也不使用 emoji、贴纸、clip-art、奖杯、火箭或通用“科研/创新”符号。

## 5. 版式与配色

- 正式流程依靠一条明确阅读方向、同层对齐、自然字宽、稳定间距和清楚分组建立秩序。
- 默认使用两类语义主色；只有真实警示、失败、异常、不良结局或关键状态才增加第三类。黑、白、灰等中性色不计入主色相。
- 颜色承担阶段、状态或重点等明确功能，不能把每个阶段涂成不同颜色来补偿无图标版式。
- 必须同时用文字、编号、位置、形状或线型编码；颜色不是唯一线索。
- 按最终显示尺寸检查对比度：理解内容所必需的方法图元或大型图形对象与相邻背景至少 3:1，普通文字尽量达到 4.5:1；同时检查灰度与常见色觉缺陷条件下的可辨认性。
- 不使用渐变、霓虹、金属、发光、塑料 3D、黏土或儿童卡通效果装饰普通流程节点。

## 6. 提示词字段

正式流程、研究设计、技术路线、病例流转或方法架构固定加入：

```text
Icon strategy: none (L0)
Icon constraints: no emoji, pictogram, clip-art, decorative small icon, stage icon, node icon, result-document icon, badge, sticker, or icon used as a bullet
Hierarchy: use text, numbering, boundaries, position, shape, line style and arrows
Method micro-visuals: none, unless a verified waveform/matrix/grid/timeline/feature representation encodes actual input, transformation or output and remains readable at final size
```

图形摘要、机制示意或科普/教学插图需要图像型例外时，改用：

```text
Image-object exception: <large object | verified content role | why text and geometry alone are insufficient>
Object budget: <少量大型对象，不重复为小图标>
Constraints: no emoji, sticker, clip-art, decorative science symbol, icon wall or object without a label/content role
```

## 7. 交付前检查

- [ ] 正式研究流程、研究设计、技术路线、病例流转与方法架构采用 L0
- [ ] 图内无 emoji、pictogram、clip-art、贴纸、徽章、阶段栏小图标、节点小图标、结果文档图标或图标化项目符号
- [ ] 数据库、清单、漏斗、文档等字面隐喻没有重复已经清楚的文字标签
- [ ] 层级由文字、编号、边界、位置、形状、线型和箭头建立
- [ ] 保留的方法微型图元对应真实输入、变换或输出，删除后会损失方法含义，且最终尺寸可辨认
- [ ] 图形摘要、机制示意或科普/教学例外使用少量大型内容对象，没有退化成重复小图标
- [ ] 主色相不超过三种，颜色有明确职责且不是唯一信息线索
- [ ] 无灯泡、奖杯、火箭、脑、芯片、发光 DNA 或通用“科研/创新”符号
