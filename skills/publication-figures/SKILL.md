---
name: publication-figures
description: 为 R 或 Python 真实数据选择、绘制、返工和审查发表级统计图、数据图，包括森林图、生存曲线、ROC、热图和模型诊断，并控制尺寸、字体、配色与多面板。任何 ggplot/matplotlib 统计出图均使用；流程、机制、框架和技术路线转 research-visuals。上游为 biostat-principles。
---
# 发表级图件规范

**核心目标**：一次出图即可直接投稿，不再因字号、分辨率、配色、字体缺失被退回。

**一句话记忆**：尺寸用 mm、字体 sans-serif 嵌入、字号 6–10 pt、PDF + 300 DPI PNG 双存、既有项目视觉语法优先、目标期刊风格在全项目内一致。

**范围边界**：本技能处理统计图、数据图和含坐标/尺度映射的论文结果图。流程图、技术路线、结构图、包含关系、概念框架、机制示意和其它非统计视觉默认调用 `research-visuals`，由其优先使用 imagegen，并仅在明确矢量要求、工具不可用或全部适用生成路径耗尽后最终回退 `svg-diagrams`；不再用 ggplot、ggflowchart、DiagrammeR 或 R 包默认样式绘框。混合图分别生成统计面板与非统计视觉面板，再统一字体、配色和边距拼装。

---

## 0. 出图工作流（先定复杂度层级 → 检索配方 → 落规范 → 自检）

### 0.0 先锁定图前合同

新图、重大重绘或多面板图在写代码前锁定：`科学问题 / 一句核心结论 / 数据与结果来源 / 每个面板的独立贡献 / 最终载体和物理尺寸 / 统计与审稿风险`。单张明确图型或轻量改色只执行缩略合同，不增加固定用户确认；只有分组、终点、纳排、主方法、变量映射或来源确有歧义时才问。

每个面板必须回答一个独立问题。两个面板若使用相同数据回答相同问题、一个可由另一个直接推导，或删除其中一个不影响核心结论，则合并或删除。图型和面板数量由科学问题决定，不由配方数量、期刊风格或版面空位决定。

**先区分内容更新与样式重设计**：只更新数值、术语、标签、精度或注释时，除非存在明确不合规问题，否则保持原图的视觉语法，不借内容更新擅自改成另一套模板。视觉语法包括图型、布局、低对比底纹或交替行、配色角色、字体层级、线型、符号、图例位置与留白；技术性的白色导出画布不等于图内必须纯白。若用户明确对图形样式不满，或现有样式妨碍表达、比较或最终尺寸可读性，则主动重新设计，不得以“保留原风格”为由拒绝必要改进。

重设计时先读取同一项目已有图件与模板，尽量统一目标期刊风格体系，包括字体、配色角色、线宽、图例、背景或底纹逻辑与信息密度；不同图型可使用不同布局，不为形式一致牺牲表达清晰度。用户指定目标期刊，但本地没有适用样式模板或已验证样例时，先用 `evidence-research` 的快速核验流程在 PubMed 检索至少 2 篇该期刊近期相同或相近图型论文，再查看 PubMed Central（PMC）或出版社全文中的实际图件，记录布局、字体层级、配色、底纹或分区、图例和信息密度后再设计。不得只根据摘要或搜索结果摘要推断图形风格，也不得复制论文数据。

### 0.1 先定复杂度层级（简单图使用基础模板，复杂图使用配方库）

| 层级 | 何时 | 怎么做 |
|---|---|---|
| **T1 基础图** | 用户没要"高级"；标准统计图（散点/箱/小提琴/KM/ROC/森林/列线/RCS/火山/PCA） | 有既有项目时沿用已锁定主题；从零且无参考时才用 `scripts/fig_setup.R` 的 `theme_pub()`+`save_fig()` 作为起点。代码起点查常用 50（见 0.2）；**不开进阶宝库**，不堆元素，也不把纯白背景当作投稿要求 |
| **T2 优雅升级** | 朴素图信息损失/同质化，或用户要"好看点" | 查 `chart-gallery.md` 速查表选替代（云雨/山脊/哑铃/棒棒糖/桑基…）→ grep catalog 取对应配方。**升级必须比朴素图多传达信息**（分布形状/配对方向/层级/流量），否则退回 T1 |
| **T3 顶刊复现** | 用户明说"顶刊同款/Nature 风/复杂高级"，或数据本身需要（多重注释热图/circos/系统发育/合图/网络） | **必走 0.2 检索**，打开命中配方的 work.R + 预览 + 教程，借技法/配色/拼接 + eyedroppeR 复刻配色，再按 §1–§12 重写 |

### 0.2 检索配方（先查后写要求，违反 = 没用好资源）

- **非平凡图开画前必先检索，禁止凭记忆从零手写而绕过 169 套配方**：
  1. `references/recipes_catalog.md` 是**单一检索面**——按意图关键词（热图/森林/云雨/桑基/网络/生存/ROC/火山/哑铃/circos/系统发育…）grep，命中行给「关键包 + 技法 + 资料 + 路径」。
  2. 命中后打开「路径」下的 work.R；进阶配方同目录常带 `.md` 教程 + 渲染预览（PDF/PNG），**先 Read 预览看效果**再决定借鉴。
- **T2/T3 必须打开 ≥1 个匹配配方，并说明借鉴了什么**（技法/配色/拼接），不可空手手写。
- **不要求精确同款**：找不到完全对应的图，就取**最接近的**配方；或从**相邻配方**借可迁移技法——分面布局（`facet_*`/ggh4x/reorder_within）、合图拼接（patchwork/cowplot/无缝拼图）、注释（双箭头/曲形文本/显著性标记/发光点强调）、配色与排版。多个配方的技法可**组合**（见 `recipes_advanced_index.md` 的"创新/合并思路示例"，如云雨图+曲形文本、热图+边际折线）。意图相近即可充分参考，技法可跨图型迁移。
- 配方脚本是**技法参考**（base `pdf()`+硬编码路径+默认尺寸，不达发表级）；落地一律按 §1–§12 重写。
- 配方库中的 `install.packages()`、`BiocManager::install()`、`devtools::install_*()` 等行是上游环境准备痕迹，只能识别依赖，**不得执行或复制进主流程**。当前环境缺包时报告包名、用途与影响，让用户自行准备后再继续。
- 库维护：`scripts/build_catalog.R` 重生成 catalog（扫 skill 自带配方重建索引；维护者可用 `PUBLICATION_FIGURES_SOURCE` 指定只读全库并同步教程/预览，**普通使用者无需此源**——skill 已自带 work.R+教程+预览，未设置时自动跳过同步，仅重建索引）。

### 0.3 落规范 → 自检 → Read 验证（§1–§12 + §10 清单 + §12ter 三查）

> **优雅 ≠ 炫技**：新意服务表达。一张图只讲一个核心关系；能朴素讲清就不堆元素（默认 T1）；升级图型必须比朴素图多传达信息，否则退回朴素图。
> 配方与画廊来自本机 R 可视化库，已随 skill 落地到 `references/`（work.R + 教程 + 预览），不依赖外部路径。

---

## 1. 物理尺寸（按最终印刷宽度画图，不要事后缩放）

| 版面类型    | 宽度           | 最大高度 | 说明                    |
| ----------- | -------------- | -------- | ----------------------- |
| 单栏        | 约 88–90 mm   | 170 mm   | Nature/Lancet/NEJM 通用 |
| 1.5 栏      | 约 120–140 mm | 170 mm   | 中等宽度                |
| 双栏 / 全幅 | 约 180 mm      | 225 mm   | 多面板主图              |

- **CRITICAL**：绘图时必须显式传入 **mm** 宽高；不得用 `width = 8, height = 6` 这类未说明单位的默认尺寸替代。
- 多面板图按"主面板填满双栏"排版，宁空白、不压字。
- 图题、图注一律走正文 / docx 图注，**不嵌入 PNG 内部**。

## 2. 分辨率与文件格式

- **统计图默认同时输出 PDF（矢量）+ PNG（300 DPI 位图）**，`04_figures/` 内同名不同后缀；非统计视觉按 `research-visuals` 输出最终 PNG，只有走矢量回退时才保留 SVG + 同名 PNG。
- PDF 投稿主交付；PNG 用于 docx 插图、汇报、预览。
- 位图 DPI：照片/灰度 ≥ 300，含线条+灰度混合 ≥ 600，纯线稿 1200（NEJM 等期刊要求）。
- **NEVER** 只存 JPEG 作最终交付；**NEVER** 用 `dpi < 300`。

## 3. 字体

- **默认字体**：Arial（首选跨平台）或 Helvetica；中文一律 **思源黑体 / 苹方 / 微软雅黑** 统一一种。
- **字号**（按最终印刷尺寸）：
  - 坐标轴刻度 6–7 pt
  - 坐标轴标题、图例 7–8 pt
  - 面板标签 (a, b, c) 8 pt **bold 小写**
  - 图内注释 ≥ 6 pt
- **字体嵌入硬要求**（否则换机器乱版）：
  - R：`ggsave(..., device = cairo_pdf)`
  - Python：`mpl.rcParams['pdf.fonttype'] = 42` 与 `rcParams['ps.fonttype'] = 42`

### 3.1 中文图件必须显式注册中文字体

**否则 PDF 中文变方块或缺字。** Windows 默认做法（脚本头部一次性）：

```r
library(sysfonts); library(showtext)
cn_font_path <- Sys.glob("C:/Windows/Fonts/msyh.ttc")
if (length(cn_font_path) == 0) cn_font_path <- Sys.glob("C:/Windows/Fonts/simhei.ttf")
if (length(cn_font_path) > 0) sysfonts::font_add("zh_sans", regular = cn_font_path[[1]])
showtext::showtext_auto(); showtext::showtext_opts(dpi = 300)
plot_family <- if (length(cn_font_path) > 0) "zh_sans" else "sans"
```

所有 `theme_classic(base_family = plot_family)` 与 `geom_text(family = plot_family)` 用同一变量驱动。
`ggsave(..., device = cairo_pdf)` + `ggsave(..., device = ragg::agg_png, dpi = 300)` 双存。
Mac/Linux 平台改 `Sys.glob` 路径（`/System/Library/Fonts/PingFang.ttc`、`/usr/share/fonts/**/SourceHanSans*.otf`）。

**REQUIRED**：中文图件导出后，必须把 PDF 第一页转 PNG 并 Read 验证（中文不是方块、未被裁切），核验完删除 preview。

```python
# PDF 第一页转 PNG 验证中文
import fitz
fitz.open('x.pdf').load_page(0).get_pixmap(dpi=200).save('preview.png')
```

## 4. 配色

- **默认顺位**：项目已锁定的语义色 → 目标期刊或模板已验证配色 → Okabe-Ito / viridis 等色觉友好调色板。ggsci 仅在对比度、灰度和色觉模拟核验通过后使用，不因期刊名称自动选择。
- 分类变量按组数和语义选择离散色，并辅以线型、形状或直接标签，不只依赖颜色。
- 连续变量热图默认 `viridis` / `cividis`；**NEVER** 红绿对比做连续映射。
- **同一论文所有图同分组颜色必须完全一致**。

## 5. 主题打底

**ggplot2**：`theme_classic(base_size = 8, base_family = "Arial")` 或 `theme_bw()` 仅是从零且无既有风格证据时的起点，不是纯白强制。已有图只更新内容时优先保留其视觉语法；表格式森林图等需要跨列追踪时可保留或使用低对比交替行。删次要网格线，保留必要主网格线；**若保留标题，标题居中加粗**；图例**优先右侧/底部**，仅当明显更差时才放顶部，不压数据。

**matplotlib 基线 rcParams**：

```python
import matplotlib as mpl
mpl.rcParams.update({
    "figure.dpi": 150, "savefig.dpi": 300,
    "pdf.fonttype": 42, "ps.fonttype": 42, "svg.fonttype": "none",
    "font.family": "Arial",
    "font.sans-serif": ["Arial", "Microsoft YaHei", "SimHei", "DejaVu Sans"],
    "axes.unicode_minus": False,
    "font.size": 8, "axes.titlesize": 9, "axes.labelsize": 8,
    "xtick.labelsize": 7, "ytick.labelsize": 7, "legend.fontsize": 7,
    "axes.linewidth": 0.6, "xtick.major.width": 0.6, "ytick.major.width": 0.6,
    "axes.spines.top": False, "axes.spines.right": False,
    "lines.linewidth": 1.0, "lines.markersize": 4,
})
```

## 6. 结构与元素

- 坐标轴标题：变量名 + 单位（例：`Tumor volume (mm³)`）。
- 数值轴范围必须匹配估计目标且不制造视觉夸大；非零基线、局部放大或断轴必须在图注清楚披露，必要时用全范围主图加局部 inset。
- 误差条 / 置信区间必须说明（SD / SE / 95% CI）。
- *P* 值斜体 "*P* = 0.013"；星号 `*` 阈值在图注定义。
- 图例：标题可省，类别名清楚；**无边框、无填充灰底**。
- 同分类层多组共坐标必须 dodge / offset / 形状区分；**禁止完全重叠交付**。
- 点、线、分布或柱形按问题选择。柱形可用于计数、比例或汇总量，但连续数据比较应尽量同时呈现分布、个体点或不确定性。
- KM 曲线用于正式生存推断或删失较多时通常附风险表；小尺寸概览只有在风险集信息由相邻表或正文可靠提供且不影响解释时可省略，并说明理由。
- 森林图选择能准确对齐标签、估计值和区间且可复现的实现；`forestploter`、`forestplot` 或一致的 ggplot 实现均可。

## 7. 多面板

- R：`patchwork`；面板标签 `plot_annotation(tag_levels = "A") & theme(plot.tag = element_text(face = "bold"))`。
- Python：`fig, axes = plt.subplots(..., constrained_layout=True)`；`ax.text(-0.1, 1.05, "a", transform=ax.transAxes, fontweight="bold", fontsize=9)`。
- 面板对齐优先 `patchwork` 自动对齐；坐标轴标题能合并就合并。
- 排版前逐对核对面板的数据、问题和信息贡献，删除重复证据。核心证据确有优先级时才扩大主面板；等权比较、诊断矩阵和对称实验保持等权，不强制设置“英雄面板”。
- 面板顺序服从研究叙事：总体模式或研究对象在前，关键差异与关系居中，验证、敏感性或解释在后；共享坐标和可直接比较的面板相邻放置。

## 8. R 导出最小模板

```r
library(ggplot2); library(patchwork)

p <- ggplot(dat, aes(x, y, colour = group)) +
  geom_point(size = 1.2) +
  scale_colour_viridis_d(end = 0.85) +
  labs(x = "Follow-up (months)", y = "Tumor volume (mm³)", colour = NULL) +
  theme_classic(base_size = 8, base_family = "Arial") +
  theme(plot.title = element_text(face = "bold", hjust = 0.5),
        legend.position = "right",
        axis.line = element_line(linewidth = 0.4),
        axis.ticks = element_line(linewidth = 0.4))

# 路径经 config.R 的 fig_path() 取（registry，编号不写死；见 project-init references/registry.md）
ggsave(fig_path("volume", "pdf"), p,
       width = 88, height = 70, units = "mm", device = cairo_pdf)
ggsave(fig_path("volume", "png"), p,
       width = 88, height = 70, units = "mm", dpi = 300, bg = "white")
```

## 9. Python 导出最小模板

```python
from pathlib import Path
import matplotlib.pyplot as plt

fig, ax = plt.subplots(figsize=(88/25.4, 70/25.4))  # mm → inch
ax.scatter(dat["x"], dat["y"], s=6)
ax.set_xlabel("Follow-up (months)")
ax.set_ylabel("Tumor volume (mm³)")
fig.tight_layout()

# 路径经 config 的 fig_path() 取（registry，编号不写死）
fig.savefig(fig_path("volume", "pdf"))
fig.savefig(fig_path("volume", "png"), dpi=300, bbox_inches="tight", facecolor="white")
plt.close(fig)
```

## 10. 自检清单（每张最终图必须过）

- [ ] 已锁定科学问题、一句核心结论、数据与结果来源、面板独立贡献、最终尺寸和审稿风险
- [ ] **已定复杂度层级（§0.1）并按层级检索**：T1 用 `fig_setup.R` 出；T2/T3 已 grep `references/recipes_catalog.md` 命中配方、打开 work.R/预览借鉴（非凭记忆从零写）；图型按 `chart-gallery.md` 选型（不无脑柱/箱，新意服务表达）
- [ ] 宽度按 mm 指定（88 / 120 / 180）
- [ ] 同时输出 PDF + 300 DPI PNG
- [ ] 字体 Arial/Helvetica + 中文统一一种，字号 6–10 pt
- [ ] PDF 用 `cairo_pdf`（R）或 `pdf.fonttype=42`（Python）
- [ ] 含中文图件已 `sysfonts::font_add` + `showtext_auto()` 注册中文字体，并 Read PNG 验证
- [ ] 配色语义一致并通过对比度与色觉可达性核验，不只依赖颜色传递含义
- [ ] 无 3D、无高对比装饰性大面积底纹、无彩虹色、无单独 JPEG；低对比交替行或分区底纹仅在帮助对齐、分组或阅读时使用
- [ ] 坐标轴有单位；置信区间/误差条含义在图注写明
- [ ] 图题图注不嵌入图内
- [ ] KM 风险集信息与载体需求匹配；森林图标签、点估计和区间严格对齐并可复现
- [ ] 多面板 patchwork/constrained_layout，标签 bold 小写
- [ ] 若保留标题，已居中加粗
- [ ] 图例默认优先右侧/底部
- [ ] 同层级多组点位/误差线没完全重叠
- [ ] **color/fill 映射无 NA / 未匹配分类**（映射表覆盖全部取值，新类别同步补，映射后断言 `!anyNA`）
- [ ] **多面板共享图例 = 单一 facet 图**（每面板独立排序用 reorder_within），不用 patchwork 各面板分类子集不同 + `guides="collect"`（会出重复图例）
- [ ] 多面板已完成两两去冗余；每个面板删除后都会损失一项独立证据或必要解释
- [ ] 图注或伴随记录明确 n 的定义、中心与离散/区间统计量、检验、多重比较校正及源文件/源列
- [ ] **标签为领域可读名**，无内部变量名 / 列前缀 / 单位后缀（`traj_`、`_ms2`、`_bpm`）
- [ ] 只更新内容时已保持原图视觉语法；样式重设计时已主动改善并统一项目的目标期刊风格；无本地模板时已完成 PubMed → 全文图件核验
- [ ] **同一论文各图风格体系一致**；每张图覆盖其预设问题所需结局，完整结局集合由整组表图共同覆盖，不为“全放一张”牺牲可读性

## 11. 各图类型尺寸经验值（mm）

| 图类型                   | 推荐尺寸 (宽×高 mm)       | 备注                               |
| ------------------------ | -------------------------- | ---------------------------------- |
| ROC / 校准曲线（单图）   | 88 × 85                   | 方形；base_size = 8                |
| ROC + 校准并排           | 180 × 85                  | patchwork 拼图                     |
| 森林图                   | 160 × (5–8 × 行数 + 20) | 行高 5–8 mm；标题预留 20 mm       |
| 列线图（≤ 6 变量）      | 180 × 110                 | 每变量约 12 mm                     |
| 列线图（≥ 7 变量）      | 180 × 150–180            | 必要时纵版 150 × 200              |
| RCS / 剂量反应曲线       | 120 × 85                  | 图例顶部；中文 title 拆两行        |
| SEM 路径图               | 180 × 115                 | `coord_cartesian(expand=F)` 填满 |
| 相关热图 / 矩阵          | 130 × 130                 | 方形                               |
| 缺失模式                 | 180 × 135                 | 横版                               |
| KM 生存（含 risk table） | 120 × 120                 | risk table 约 30% 高度             |

- **DEFAULT**：出图前先按行/列数估算尺寸，不要统一 88×85。
- 画布严重偏离内容密度（如 11 行 nomogram 塞 150mm 高）必须增大高度或减少行数。

## 12. 致丑陋陷阱（硬禁止，违反图件不合格）

- **NEVER** 用 `plot.margin = margin(..., l = 60)` 硬塞 >40mm 左空白；改用 `scale_y_discrete` / `axis.text.y` / `annotation_custom`。
- **NEVER** 在 ≤ 88×66mm 小画布用 `base_size = 12`；小画布必须 `base_size = 7–8`，中文压到 7。
- **NEVER** 中文长标题（> 12 字）不换行；超过 12 字必须 `str_wrap(title, 14)` 或拆两行。
- **NEVER** 让图例（含图例文字/色块/边框）压住任何数据曲线、散点、柱、误差棒或注释——图例与数据重叠 = 图件不合格，必返工。默认 `"right"` / `"bottom"` 外嵌最稳；仅当绘图区内确有大片空白且经 Read 验证图例完全不压数据时，才可用 `legend.position = c(x, y)` 内嵌，并加半透明白底（`legend.background = element_rect(fill = alpha("white", .7), colour = NA)`）保证可读；一旦内嵌后发现压线，立即改外嵌或换到空白象限重渲。
- **NEVER** 同分类层多组完全重叠交付；必须显式错位。
- **NEVER** 在论文图直接用 `rms::calibrate()` / `pROC::plot.roc()` / `rms::nomogram()` 的 base R 默认绘图；从对象取数据用 ggplot2 重绘。
- **校准曲线保持解释尺度**：默认显示目标概率的完整临床相关范围并保留 45° 参考线。确需放大高概率区时使用清楚标注的 inset 或显式披露相同的 x/y 限制；不得通过各面板独立裁剪隐藏失校准或制造优良外观。
- **NEVER** `theme_bw()` 不带 `base_size` 覆盖；默认 11pt 对 88mm 画布过大。
- **NEVER** nomogram / forest / 相关矩阵高度与行数不匹配。
- **NEVER** `ggsave(..., width = 8, height = 6)` 英寸默认值带进最终图；**一律 `units = "mm"`**。
- **NEVER** 含中文图把 `base_family` 留作 `"Arial"` / `"sans"` 不注册中文字体；必须 `sysfonts::font_add` + `showtext::showtext_auto()`。
- **NEVER** 只看 PNG 就宣称 PDF 没问题；PNG 走 `ragg::agg_png`、PDF 走 `cairo_pdf`，两条字体路径独立；中文图必须额外把 PDF 第一页转 PNG 复核。

### 12bis 分类映射 / 多面板 / 标签 / 一致性（强制要求，违反即返工）

1. **映射零 NA**：任何 color/fill/group 由查表得到时，表必须覆盖全部取值；新增类别（如新特征族）立即补表；映射后 `stopifnot(!anyNA(x))`。图例出现 "NA"/灰色未命名组 = 漏映射，必修。
2. **共享图例用单 facet 图**：N 个面板共享一个图例时，**优先单个 `facet_wrap`/`facet_grid`**（每面板独立排序用 reorder_within 手法：唯一 y 键 + `scale_y_discrete(labels=)` 还原显示名）。**NEVER** 用 patchwork 拼 N 子图 + `guides="collect"` 当各子图分类子集不同——会出上下重复图例；必须用 patchwork 时显式统一各面板因子 `levels` + `drop=FALSE`。
3. **标签领域化 + 随论文语言**：轴/图例/注释/分面标题/因子水平**只用领域可读名**，**NEVER** 暴露内部变量名、列前缀、单位后缀（`traj_`、`seq_`、`_ms2`、`_bpm`、`subject_id`）；维护"列名→标签"映射并**按语言键存中英对照**（`label_zh` / `label_en`），出图按当前论文语言取标签。**英文稿 NEVER 沿用中文标签的图**——切到英文键重出图；中文稿同理。新变量必补中英两条（呼应全局 `CLAUDE.md` §6 的术语合同）。
4. **全文风格体系一致 + 结局覆盖可审计**：同一论文统一字体、配色角色、线宽、图例和背景逻辑，不为形式一致牺牲表达。多结局由整组预设表图完整覆盖；单图只放回答该图问题且最终尺寸可读的结局。亚组森林按有意义类别组织，避免无结构列表。
5. **图与正文命名字面一致**：自定义分期/分组/变量命名（如 `IA_TLG`、`TNM_TLG`，或带括号/下标/上标的写法）在图（轴/图例/图例标题/列线图行名/森林行名/DCA 图例）与正文/表格中必须**用同一字面后缀写法**，不可正文 `IA_TLG`（下标）而图里 `IA(TLG)`（括号）。出图前确认与正文采用的写法一致；正文若用下标，图内因绘图引擎难排下标可用同字符的行内式（`IA_TLG`），但**后缀本身（`_TLG` 还是 `(TLG)`）两边必须统一**。改了正文写法要同步重出图。

### 12ter 每张图出后强制「美观 + 合理性」自检（每生成/重渲一张图都必做，任一不过 = 返工）

**先 Read PNG/PDF 看，再逐条过——不只看好不好看，更看数字对不对：**

1. **数值可溯源、不过时**：图上每个数字都能在分析产物、表或 `07_paper/results.yaml` 找到，并与派生 `0_result_summaries.md` **完全一致**；schematic / 标注里的数字**禁止硬编码**（硬编码必随结果更新而过时，如设计图 AUC 未随主结果重跑而停在旧值）；与全文 headline 不矛盾。
2. **无统计假象 / 不合常理**：警惕「所有格子同值 / 全为同一常数 / 全 ±同一数」——多是计算 bug（典型：对仅 2 组做标准化 `scale()` 恒得 ±0.707，热图全 ±0.7 是假象不是信号）；检查量级、方向、分布、趋势是否符合常识与已知结论（如校准 slope>1 应表现为预测向中部压缩、不该出现矛盾形状）。**发现可疑模式 = 疑点，先判定是画图 / 原数据 / 方法哪一层的问题再出图**。
3. **表达正确**：分类映射无 NA、图例不重复不缺、**图例不压任何数据曲线/点/柱/注释（重叠即返工，改外嵌或挪到空白象限）**、标签无内部变量名、坐标/标签/标题无裁切、图型匹配数据（AUC 用点+CI 而非截断柱）、本图覆盖其预设问题所需结局且整组表图覆盖完整结局集合、与同篇其它图 theme/配色/布局一致。

**未做完这三条自检 = 图未完成**；任一条触发即回到代码层定位根因（画图 bug / 数据陈旧 / 方法错误）后重出，不带病交付。
