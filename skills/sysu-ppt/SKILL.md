---
name: sysu-ppt
description: 中山大学学术汇报 PPT 制作技能。基于 officer R 包和官方模板生成可直接上台汇报的精美完整 PPT，覆盖组会汇报与开题/答辩/正式研究汇报两类体裁。触发场景：(1) 用户要求制作组会汇报/开题报告/答辩/学术报告 PPT；(2) 用户提供汇报主题/方向并需要生成演示文稿；(3) 用户要求创建新的汇报文件夹。组会默认 13-15 页，禁止目录页与任何章节分隔/过渡页；开题/答辩/正式汇报 20-40 页，按内容定。
---

# SYSU PPT Skill

用 R `officer` + 官方模板，代码化生成**可直接上台、精美完整**的学术汇报 PPT。**给定主题/内容/要求，按本文件流程即可产出合规 PPT。**

## 总原则（奥卡姆剃刀）

**精确实现每一条要求，不堆字、不过度设计。** 文字写到说清楚为止即可；版面"充实"靠**布局与元素尺寸**实现，不靠注水。允许留白——宁可干净留白，也不要为凑满而啰嗦。

## 体裁与结构蓝图（先认体裁再开写）

先判断属于哪类，套对应骨架——**两类的结构、篇幅、是否用章节分隔页都不同**：

| 体裁 | 篇幅 | 章节分隔页 | 骨架 | 蓝本 |
|---|---|---|---|---|
| 组会汇报 / 文献分享 / 方法讲解 | 13-15 页 | **不用** | 背景 → 概念 → 方法 → 对比 → 决策 → 收束 | `references/deck_skeleton.R` |
| 开题 / 中期 / 答辩 / 正式研究汇报 | 20-40 页 | **用**（每个一级章节前一张） | 封面 → 目录 → 立题依据 → 研究目的与内容 → 研究方法（主体）→ 技术路线图 → 创新点与可行性 → 进度安排 →（参考文献）→ 致谢 | `references/defense_blueprint.R` |

### 组会体裁门禁（CRITICAL，违反 = 未完成）

- **组会 PPT 禁止目录页**：不得出现“目录 / 汇报提纲 / 内容提要 / Agenda / Contents”等单独页面。
- **组会 PPT 禁止任何章节分隔页或过渡页**：封面后直接进入第一张实质内容页，主题切换直接用内容页标题编号表达，不插入只有章节名、序号或短副标题的空转页面。
- **组会生成脚本禁止调用 `sysu_add_section()`**。该函数只属于开题、答辩、中期和正式研究汇报。
- 组会必须用 `sysu_save(ppt, path, genre = "meeting")`；`meeting` 也是默认值，保存前会检测目录页与章节分隔页，命中即停止写出。正式体裁必须显式使用 `genre = "formal"`。

开题/答辩体裁的规范结构、规范用词库（章节名 / 段落标签 / 方法对比表头 / 封面署名 / 结尾语）、设计基调，全部在 `references/defense_blueprint.R` 顶部注释里——写这类 PPT 前先读它，按里面的顺序与措辞填内容，不要自创结构或口语化标签。

**设计基调（两类通用）**：主色中大深绿 `#014924`（章节号 / 标题竖条 / 表头）；强调用克制的红 `#C00000`，全篇仅 1-2 处关键结论，不滥用；每页优先用图（机制图 / 流程图 / 技术路线图）表达，研究方法页尽量配示意图。

## 工作流（复制即用）

```r
Sys.setlocale("LC_ALL", "Chinese (Simplified)_China.utf8")
skill_roots <- path.expand(c(
  Sys.getenv("EPIAGENTKIT_SKILLS"), Sys.getenv("EPICLAUDE_SKILLS"),
  "~/.claude/skills", "~/.agents/skills", "~/.codex/skills"
))
skill_dirs <- file.path(skill_roots[nzchar(skill_roots)], "sysu-ppt")
SKILL <- skill_dirs[dir.exists(skill_dirs)][1]
if (!length(SKILL) || is.na(SKILL)) stop("找不到 sysu-ppt；请设置 EPIAGENTKIT_SKILLS")
source(file.path(SKILL, "scripts", "sysu_toolkit.R"))

ppt <- sysu_init("default")          # 默认=原“模板2”中大医学版；旧公卫模板可用 sysu_init("模板2")
ppt <- sysu_add_cover(ppt, "主标题", "English Subtitle", "汇报人：姓名", "2026 组会")
ppt <- sysu_add_text(ppt, "1 背景", block_list( prose(bd("定义　"), tx("……")) ))
# ……更多内容页（见 API）……
sysu_save(ppt, "输出.pptx", genre = "meeting")  # 组会：强制禁目录/章节过渡页
```

完整骨架见 `references/deck_skeleton.R`；配图函数见 `references/figure_snippets.R`。

## 模板选择

- **未指明 / 模板1 / medical** → `sysu_init("default")` = `assets/template.pptx`（原模板2：中大医学棕榈实景封面 + 校徽 + 城市水印）。
- **用户说"模板2/模板二/公卫"** → `sysu_init("模板2")` = `assets/template-公卫学院.pptx`（原模板1：公卫学院绿色封面 + 标题绿竖条）。
- 也可传 `.pptx` 完整路径。两套模板内容页 API 完全一致，只改 `sysu_init` 参数。

## 硬性规范（每次必须满足）

1. **字体**：中文宋体、英文 Times New Roman，同段自动分流（`.fp()` 内置，无需手动切）。已在 slide XML 层校验 `<a:ea>=宋体`、`<a:latin>=Times New Roman`。
2. **字号**：正文 16pt、标题 24pt（默认值，勿改）。
3. **版式多样**：一份 PPT 混用 ≥4 种版式，不要整份纯文字。优先用图（流程图/示意图）表达结构与机制。
4. **充实靠布局，不靠堆字**：每页大致占满版面、不空半屏；做法是**选对版式 + 调元素尺寸**，文字保持精炼。卡片/图片留白可接受。
   - **正文有字数预算（officer 文本框不自动缩字，超出即溢到页脚/被截）**：左右图文 / 左文右表的**左栏 ≤ 5 个段落块、合计 ≤ ~12 行 / ~230 中文字**（每块 = 标签 + 1–2 句）；纯文字全宽页 ≤ 7 块 / ~340 字。**超了就删次要句或拆成两页，绝不靠缩小字号硬塞**。长英文全称放进正文句中、不要塞进 `num_item` 加粗小标题（标题一行写不下会换行挤占两行）。生成后必看每页最后一行是否压到底部横线/页码——压到即超，回去精简。
5. **编号体现层次（两级，编号只在内容页标题）**：**同主题的多页共用一个一级序号、用二级区分**——背景三页 = `1.1 / 1.2 / 1.3`，核心方法多页 = `2.1 … 2.8`，结语 = `4.1 / 4.2`。规划时先按主题分 3–5 个一级组，每组 ≥2 页；只用两级 `X.Y`，正文不写 `1.1.1`。编号用于内容页组织，**不得据此生成目录页或章节过渡页**。
6. **章节分隔页严格按体裁隔离**：组会汇报不得调用 `sysu_add_section()`，不得添加目录、汇报提纲或任何过渡页，封面后直接进内容；**仅开题/答辩/正式研究汇报可用** `sysu_add_section("一、立题依据")`，并配目录页与"请各位老师批评指正！"致谢页（见 `defense_blueprint.R`）。
7. **强调**：关键术语/结论用 `bd()`（加粗+主色）。
7bis. **数字单源取数**：汇报里的统计数字（估计值/CI/P/百分比/样本量）若项目有 `07_paper/results.yaml`，一律
   `val("07_paper/results.yaml", "key")` 取已渲染串（toolkit 已内置 `val()`），**禁止手敲**；改数字回 results.yaml 改再重生成。
8. **编号与圆点二选一**：用了 ①②③/123 就别再加 ●（用 `num_item`，不要 `bullet`）。
9. **学术书面、不口语（每页都查）**：
   - **标题用规范名词短语**，不用反问/口语标题。✗"一个高 AUC 的模型就是好模型吗"/"判别和校准是两回事"/"概率准不准" ✓"仅凭 AUC 能否判定模型优劣"/"判别和校准的区别"/"校准（Calibration）"。
   - **段落小标签用规范词**：解决问题 / 指标计算 / 检验 / 局限性 / 定义 / 说明 / 注意事项 / 方法 / 重要性 等。**禁用敷衍或口语标签**：✗"一句话""坑""怎么读""怎么办""通俗讲""回答"。
   - **英文缩写首次出现给全称**：首次写 `AUC（Area Under the Curve）`、`IDI（Integrated Discrimination Improvement）`、`NRI（Net Reclassification Improvement）`、`DCA（Decision Curve Analysis）` 等，后文再用缩写。
   - **删空话/敷衍句**：没有信息量的 `intro`/`note`（如"这几乎覆盖了最常见的误用""核心：…"）直接删，不靠它凑版面。
   - **不用网络口语**：✗ 净赚、听得懂、一验就掉、学过头、乱筛、当万能、迷信、纹丝不动、虚高… → 改书面表达（净获益、可理解、外部验证性能下降、过度拟合、随意筛选、过度依赖、偏高…）。
10. **当前版单一、旧版整组归档**：当前汇报目录只保留稳定命名的 `.pptx`、当前生成脚本和必要素材，不生成“完善版 / 最终版 / v2 / final”等并列文件。每次重生成前，把被替代 PPT、对应旧脚本、渲染页图与旧素材按原相对目录移入 `09_backup/YYYY-MM-DD_HHMM_<汇报主题>_<阶段>/`，写 `MANIFEST.md` 并登记 `09_backup/INDEX.md`；`sysu_save()` 始终写当前稳定文件名。

## API 速查

| 函数 | 版式 | 关键参数 |
|---|---|---|
| `sysu_init(tpl)` | 初始化、清空演示页 | "default"/"模板1"=中大医学；"模板2"=原公卫模板；或路径 |
| `sysu_add_cover(ppt,title,subtitle,author,date)` | 封面 | subtitle 用一行短副标题 |
| `sysu_add_text(ppt,title,blocks)` | 纯文字（全宽） | blocks=block_list(...) |
| `sysu_add_two_text(ppt,title,left,right)` | 双栏文字 | 两个 block_list |
| `sysu_add_text_image(ppt,title,blocks,img,img_w,img_h,side,caption)` | 左右图文 | side="right"/"left" |
| `sysu_add_image_caption(ppt,title,img,img_w,img_h,blocks,img_pos,caption)` | 上下图文 | img_pos="top"/"bottom"；caption="图N …" |
| `sysu_add_image(ppt,title,img,img_w,img_h,caption)` | 整图居中 | |
| `sysu_add_table(ppt,title,ft,left,top,note)` | 表格 | ft 用 `sysu_flextable()` |
| `sysu_add_text_table(ppt,title,blocks,ft)` | 左文右表 | |
| `sysu_add_code(ppt,title,code_lines,intro)` | 代码/示例 | code_lines=字符向量 |
| `sysu_add_cards(ppt,title,cards,cols,intro)` | 卡片网格(淡灰) | cards=list(list(tag,head,body)…) |
| `sysu_add_section(ppt,title,subtitle)` | 正式汇报章节页 | **组会禁止调用** |
| `sysu_save(ppt,path,genre)` | 保存 + 体裁门禁 + 顶端对齐修正 | 组会 `meeting`；正式汇报 `formal` |

**文本助手**：`tx()` 正文 / `bd()` 加粗主色 / `cd()` 等宽 / `prose(...)` 成段（优先，避免满屏列表）/ `num_item(num,head,body)` 编号条目（自带语义，不加圆点）/ `bullet()`+`sub_bullet()` 圆点列表（无编号时才用）/ `sp(h)` 间距。
**表格**：`sysu_flextable(df, widths, fsize, align)` — 绿表头 + 斑马行 + 三线表。

## 卡片约束

- 统一**淡灰底(#F4F5F7) + 绿色细左条 + 绿色标题**，**禁止彩色方块**（`color` 参数已忽略）。
- 卡片**贴合内容高度、紧跟 intro 顶端对齐**，**不拉满整页**——底部留白优于高卡内部空洞。
- **全篇克制：最多 2-3 页卡片**；用于真正并列的 3-4 项。其余并列点用 `prose`/`num_item`。

## 配图（结构/机制优先画图）

- **流程图、结构图、技术路线、包含关系图、概念框架和机制示意一律调用 `svg-diagrams` 原生生成 SVG**，优先直接用 `sysu_add_image*` 嵌入 SVG；同时保留同名 PNG 预览。不得再用 ggplot/ggflowchart/R 包默认矩形绘制这类图。统计图仍走 `publication-figures`，数据散点/曲线配方可参考 `references/figure_snippets.R`。
- SVG 对齐遵循 `svg-diagrams/references/design-system.md`：同层框共线等距；序号圆心与标题第一行视觉中心水平对齐；包含关系框共享中心且内边距递进；分支标题不小于正文；无语义圆点、英文眉题、副标题和深色顶部色块默认不生成。
- **图内不写标题、不写解释性句子**（最常被打回）：删掉 `labs(title=...)`、删掉像"偏离对角线 = 概率不准""模型净获益最高的阈值区间"这类**讲道理的 `annotate("text")`**。图里只保留坐标轴、图例、必要的**数据标签**（如曲线旁的"病例/非病例"、参考线旁的阈值数值）。解释一律写到 PPT 正文或题注。
- **每张图必须配"图N ……"题注**：黑色、小字号(13pt)、居中、置于图**下方**。用各 `sysu_add_image*` 的 `caption=` 参数（`sysu_add_text_image`/`sysu_add_image_caption`/`sysu_add_image` 都支持；toolkit 已把题注色设为近黑 `SYSU$col$text`）。图号 `图1/图2…`**按出现顺序连续**。
- **图例要短**：不要把整句解释当图例标签（如"过度极端 slope<1（概率太极端）"）；缩成"slope<1 概率太极端"这类短词，解释移正文。图例条目过长 + `coord_equal` 常导致图例与面板间出现大块空白——用 `coord_cartesian(expand=FALSE)` + 短标签修复。
- **图内字要够大（最常被打回的问题）**：统计图按接近嵌入尺寸渲染并放大字号；SVG 流程/框架图按实际占位比例设计，节点标题与组标题在缩略图上仍须清晰，分支标题不得缩成注脚。发现字小一律回到 SVG 源调整，不在 PPT 中拉伸补救。
- **图不能有多余留白/空边**：`ggsave` 的画布长宽比要贴合内容，否则四周留白。**ROC/校准等用 `coord_cartesian(expand=FALSE)` 让面板填满画布；少用 `coord_equal`**（它强制方形面板，常在另一维留出大块空白）。注释/图例尽量收紧，`plot.margin` 适当压小。自检发现某图上下/左右有空条 → 调画布比例或换 coord 重渲染。
- 中文用 `showtext` + SimHei：`font_add("simhei","C:/Windows/Fonts/simhei.ttf"); showtext_auto()`。
- 嵌入 `img_w/img_h` 只是**最大边界框**，`.fit()` 自动按 PNG 真实比例等比缩放，**不会变形**；给的比例不必精确。

## 自检（生成后必跑）

```powershell
$pp = New-Object -ComObject PowerPoint.Application
$pres = $pp.Presentations.Open("绝对路径.pptx", $true, $false, $false)
$pres.Export("png输出目录", "PNG", 1280, 720)
$pres.Close(); try { $pp.Quit() } catch {}
```
逐页读 PNG 检查（**每一项不合格都要改了重生成，不许将就**）：
⓪ **组会体裁门禁**：无目录/汇报提纲/Agenda 页，无章节分隔/过渡页；封面下一页即实质内容；生成脚本无 `sysu_add_section()`，并以 `genre = "meeting"` 保存。
① 字体对（宋体/Times）；② 不空半屏、不溢出（表格列不被截断）；③ **图内文字够大**——流程图/框架图框内字、坐标轴、注释在缩略图上仍清晰可读，偏小立即调大重渲染；④ **图无多余空边**——图四周没有明显空白条，有则调 SVG 画布或统计图输出比例重渲染；⑤ **SVG 对齐正确**——同行/同列/嵌套框共用锚点，序号与标题第一行垂直居中，分支标签不小于正文，无无语义圆点；⑥ **表格上下居中**——表格块在内容区垂直居中而非贴顶；⑦ 图居中不变形；⑧ 重点已加粗；⑨ 标题元素与模板设计对齐；⑩ **图内无标题、无解释性句子**（只剩坐标轴/图例/数据标签），讲道理的文字都在正文或题注；⑪ **每张图都有"图N ……"题注**，图号按出现顺序连续；⑫ **图例简短**；⑬ **学术书面**（见硬性规范 9）。
归档检查：当前目录仅保留一份稳定命名 PPT 与当前源；无“完善版 / 最终版 / v2 / final”等旧版；旧版批次可由 `09_backup/INDEX.md` 定位且含 `MANIFEST.md`。
> 图件大于 ~2000px 时图像读取工具可能报错，可先缩放到 ≤1280px 再读；或直接读 1280×720 的逐页导出 PNG。
> COM 偶发 `Quit()` 报错可忽略（导出已完成）；重跑前先 `Stop-Process -Name POWERPNT`，避免文件占用。

## 易踩的坑（已修复，勿回退）

- **标题对齐**：默认模板标题走 `Title and Content` 版式的绿竖条；标题框 x=0.92/y=0.50/h=0.575，底部横线与竖条齐平。**勿把标题放进 Blank 版式**（段落边框不渲染、竖条消失）。
- **默认模板设计在 layout 不在 master**：当前默认的中大医学模板封面/校徽/水印在**带设计的版式**里——`cover="1_空白"`、`content="3_空白"`。误用朴素 `标题和内容`/`空白` 会得到纯白页。
- **默认模板标题无竖条**：故 `.add_title` 对当前默认模板使用可靠的 flextable 横线；旧公卫模板继续使用版式自带绿竖条。
- **正文偏下**：部分版式文本框默认垂直居中；`sysu_save()` 按字节把空 `<a:bodyPr/>` 设 `anchor="t"`，故**用 `sysu_save` 而非 `print`**。
- **表格垂直居中**：`sysu_add_table` / `sysu_add_text_table` 的 `top` 默认 `NULL` = 按表实际高度在内容区(1.58~7.0)自动垂直居中（行数少的表不再贴顶）。需固定位置时显式传 `top=` 数值。单元格内文字已由 `sysu_flextable` 设 `valign="center"`。

## 参考文件

- `scripts/sysu_toolkit.R` — 核心工具库。
- `scripts/example_ppt.R` — 覆盖全部版式的可运行演示。
- `references/deck_skeleton.R` — 组会汇报骨架模板（13-15 页，无章节页）。
- `references/defense_blueprint.R` — 开题/答辩/正式研究汇报骨架（20-40 页，含章节页、目录、技术路线、进度表、致谢页 + 顶部规范用词库与设计基调）。
- `references/figure_snippets.R` — 数据散点/谱系等统计型配图示例；非统计流程与结构图改用 `svg-diagrams`。
- `assets/template.pptx`（默认中大医学）、`assets/template-公卫学院.pptx`（模板2）— 两套模板。
