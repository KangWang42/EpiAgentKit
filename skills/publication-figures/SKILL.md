---
name: publication-figures
description: 发表级图件标准 + 图类型选型画廊 (R + Python 通用)。包含①图类型选型与开创思路画廊（~180 种图按分析意图编目 + 优雅升级建议 + 50 套常用配方代码 references/）②物理尺寸 / 字体嵌入 / 配色 / 主题 / 多面板 / 各图类型经验值 / 致丑陋陷阱清单 / 出图前后自检。触发场景：(1) 用户要求出图、画图、做图、生成 Fig；(2) 任何 ggplot / matplotlib 出图任务；(3) 论文图件返工、答辩 PPT 出图；(4) 答辩 / 投稿前的图件审查；(5) 不知道该用什么图 / 想让图更有新意更优雅时。上游依赖：biostat-principles（口径与可复现规则）。
---
# 发表级图件规范

**核心目标**：一次出图即可直接投稿，不再因字号、分辨率、配色、字体缺失被退回。

**一句话记忆**：尺寸用 mm、字体 sans-serif 嵌入、字号 6–10 pt、PDF + 300 DPI PNG 双存、ggsci/科研配色、theme_bw/theme_classic 打底。

---

## 0. 出图工作流（先定复杂度层级 → 检索配方 → 落规范 → 自检）

### 0.1 先定复杂度层级（简单图别开宝库，顶刊图必开宝库）

| 层级 | 何时 | 怎么做 |
|---|---|---|
| **T1 朴素默认** | 用户没要"高级"；标准统计图（散点/箱/小提琴/KM/ROC/森林/列线/RCS/火山/PCA） | 用 `scripts/fig_setup.R` 的 `theme_pub()`+`save_fig()` 零调参出图；代码起点查常用 50（见 0.2）。**不开进阶宝库**，不堆元素 |
| **T2 优雅升级** | 朴素图信息损失/同质化，或用户要"好看点" | 查 `chart-gallery.md` 速查表选替代（云雨/山脊/哑铃/棒棒糖/桑基…）→ grep catalog 取对应配方。**升级必须比朴素图多传达信息**（分布形状/配对方向/层级/流量），否则退回 T1 |
| **T3 顶刊复现** | 用户明说"顶刊同款/Nature 风/复杂高级"，或数据本身需要（多重注释热图/circos/系统发育/合图/网络） | **必走 0.2 检索**，打开命中配方的 work.R + 预览 + 教程，借技法/配色/拼接 + eyedroppeR 复刻配色，再按 §1–§12 重写 |

### 0.2 检索配方（先查后写门禁，违反 = 没用好资源）

- **非平凡图开画前必先检索，禁止凭记忆从零手写而绕过 169 套配方**：
  1. `references/recipes_catalog.md` 是**单一检索面**——按意图关键词（热图/森林/云雨/桑基/网络/生存/ROC/火山/哑铃/circos/系统发育…）grep，命中行给「关键包 + 技法 + 资料 + 路径」。
  2. 命中后打开「路径」下的 work.R；进阶配方同目录常带 `.md` 教程 + 渲染预览（PDF/PNG），**先 Read 预览看效果**再决定借鉴。
- **T2/T3 必须打开 ≥1 个匹配配方，并说明借鉴了什么**（技法/配色/拼接），不可空手手写。
- **不要求精确同款**：找不到完全对应的图，就取**最接近的**配方；或从**相邻配方**借可迁移技法——分面布局（`facet_*`/ggh4x/reorder_within）、合图拼接（patchwork/cowplot/无缝拼图）、注释（双箭头/曲形文本/显著性标记/发光点强调）、配色与排版。多个配方的技法可**组合**（见 `recipes_advanced_index.md` 的"创新/合并思路示例"，如云雨图+曲形文本、热图+边际折线）。意图相近即可充分参考，技法可跨图型迁移。
- 配方脚本是**技法参考**（base `pdf()`+硬编码路径+默认尺寸，不达发表级）；落地一律按 §1–§12 重写。
- 库维护：`scripts/build_catalog.R` 重生成 catalog（扫 skill 自带配方重建索引；其顶部 `SRC_ADV` 指向维护者本地全库用于同步教程/预览，**普通使用者无需此源**——skill 已自带 work.R+教程+预览，源不存在时自动跳过同步仅重建索引）。

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

- **CRITICAL**：绘图时必须显式传入 **mm** 宽高；不要靠 `width = 8, height = 6` 这种"英寸默认值"糊弄。
- 多面板图按"主面板填满双栏"排版，宁空白、不压字。
- 图题、图注一律走正文 / docx 图注，**不嵌入 PNG 内部**。

## 2. 分辨率与文件格式

- **默认同时输出 PDF（矢量）+ PNG（300 DPI 位图）**，`04_figures/` 内同名不同后缀。
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

- **DEFAULT 医学期刊配色顺位**：`ggsci::pal_lancet()` → `pal_nejm()` → `pal_jco()` → `pal_nature()`。Python 用 `seaborn.color_palette` 或复制 ggsci 十六进制列表。
- 分类组 ≤ 5 时首选 **色盲友好调色板**：`viridis::viridis_d` / `RColorBrewer::Set2` / Okabe-Ito 8 色。
- 连续变量热图默认 `viridis` / `cividis`；**NEVER** 红绿对比做连续映射。
- **同一论文所有图同分组颜色必须完全一致**。

## 5. 主题打底

**ggplot2**：默认 `theme_classic(base_size = 8, base_family = "Arial")` 或 `theme_bw()`；删次要网格线，保留必要主网格线；**若保留标题，标题居中加粗**；图例**优先右侧/底部**，仅当明显更差时才放顶部，不压数据。

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
- 数值轴 **从 0 或合理基线**；必须截断画破折号 `//` 并图注说明。
- 误差条 / 置信区间必须说明（SD / SE / 95% CI）。
- *P* 值斜体 "*P* = 0.013"；星号 `*` 阈值在图注定义。
- 图例：标题可省，类别名清楚；**无边框、无填充灰底**。
- 同分类层多组共坐标必须 dodge / offset / 形状区分；**禁止完全重叠交付**。
- 点 vs 线 vs 柱：组数少用点+误差条或 violin/box；**柱图仅用于计数类**。
- KM 曲线必须带 risk table（`survminer::ggsurvplot(..., risk.table = TRUE)` 或 `ggsurvfit::add_risktable()`）。
- 森林图优先 `forestploter` 或 `forestplot`，**不用 ggplot 手糊**。

## 7. 多面板

- R：`patchwork`；面板标签 `plot_annotation(tag_levels = "A") & theme(plot.tag = element_text(face = "bold"))`。
- Python：`fig, axes = plt.subplots(..., constrained_layout=True)`；`ax.text(-0.1, 1.05, "a", transform=ax.transAxes, fontweight="bold", fontsize=9)`。
- 面板对齐优先 `patchwork` 自动对齐；坐标轴标题能合并就合并。

## 8. R 导出最小模板

```r
library(ggplot2); library(ggsci); library(patchwork)

p <- ggplot(dat, aes(x, y, colour = group)) +
  geom_point(size = 1.2) +
  scale_colour_lancet() +
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

- [ ] **已定复杂度层级（§0.1）并按层级检索**：T1 用 `fig_setup.R` 出；T2/T3 已 grep `references/recipes_catalog.md` 命中配方、打开 work.R/预览借鉴（非凭记忆从零写）；图型按 `chart-gallery.md` 选型（不无脑柱/箱，新意服务表达）
- [ ] 宽度按 mm 指定（88 / 120 / 180）
- [ ] 同时输出 PDF + 300 DPI PNG
- [ ] 字体 Arial/Helvetica + 中文统一一种，字号 6–10 pt
- [ ] PDF 用 `cairo_pdf`（R）或 `pdf.fonttype=42`（Python）
- [ ] 含中文图件已 `sysfonts::font_add` + `showtext_auto()` 注册中文字体，并 Read PNG 验证
- [ ] 配色 ggsci 或色盲友好调色板，全论文一致
- [ ] 无 3D / 默认灰底 / 彩虹色 / 单独 JPEG
- [ ] 坐标轴有单位；置信区间/误差条含义在图注写明
- [ ] 图题图注不嵌入图内
- [ ] KM 曲线带 risk table；森林图用 forestploter **或**与全文一致的 ggplot 分面森林（二选一服从全文统一风格）
- [ ] 多面板 patchwork/constrained_layout，标签 bold 小写
- [ ] 若保留标题，已居中加粗
- [ ] 图例默认优先右侧/底部
- [ ] 同层级多组点位/误差线没完全重叠
- [ ] **color/fill 映射无 NA / 未匹配分类**（映射表覆盖全部取值，新类别同步补，映射后断言 `!anyNA`）
- [ ] **多面板共享图例 = 单一 facet 图**（每面板独立排序用 reorder_within），不用 patchwork 各面板分类子集不同 + `guides="collect"`（会出重复图例）
- [ ] **标签为领域可读名**，无内部变量名 / 列前缀 / 单位后缀（`traj_`、`_ms2`、`_bpm`）
- [ ] **同一论文各图风格一致**（theme/配色/分面布局同款）；**多结局分析每张图含全部结局**，不漏

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
- **NEVER** `theme_bw()` 不带 `base_size` 覆盖；默认 11pt 对 88mm 画布过大。
- **NEVER** nomogram / forest / 相关矩阵高度与行数不匹配。
- **NEVER** `ggsave(..., width = 8, height = 6)` 英寸默认值带进最终图；**一律 `units = "mm"`**。
- **NEVER** 含中文图把 `base_family` 留作 `"Arial"` / `"sans"` 不注册中文字体；必须 `sysfonts::font_add` + `showtext::showtext_auto()`。
- **NEVER** 只看 PNG 就宣称 PDF 没问题；PNG 走 `ragg::agg_png`、PDF 走 `cairo_pdf`，两条字体路径独立；中文图必须额外把 PDF 第一页转 PNG 复核。

### 12bis 分类映射 / 多面板 / 标签 / 一致性（4 条铁律，违反即返工）

1. **映射零 NA**：任何 color/fill/group 由查表得到时，表必须覆盖全部取值；新增类别（如新特征族）立即补表；映射后 `stopifnot(!anyNA(x))`。图例出现 "NA"/灰色未命名组 = 漏映射，必修。
2. **共享图例用单 facet 图**：N 个面板共享一个图例时，**优先单个 `facet_wrap`/`facet_grid`**（每面板独立排序用 reorder_within 手法：唯一 y 键 + `scale_y_discrete(labels=)` 还原显示名）。**NEVER** 用 patchwork 拼 N 子图 + `guides="collect"` 当各子图分类子集不同——会出上下重复图例；必须用 patchwork 时显式统一各面板因子 `levels` + `drop=FALSE`。
3. **标签领域化 + 随论文语言**：轴/图例/注释/分面标题/因子水平**只用领域可读名**，**NEVER** 暴露内部变量名、列前缀、单位后缀（`traj_`、`seq_`、`_ms2`、`_bpm`、`subject_id`）；维护"列名→标签"映射并**按语言键存中英对照**（`label_zh` / `label_en`），出图按当前论文语言取标签。**英文稿 NEVER 沿用中文标签的图**——切到英文键重出图；中文稿同理。新变量必补中英两条（呼应 CLAUDE §2 禁暴露内部名）。
4. **全文一致 + 不漏结局**：同一论文所有图共用同一 theme/配色顺位/分面布局（如统一 `theme_bw(8)` + 三结局按 outcome 分面 + lancet `pal3`）；**多结局/多终点分析里每张按结局的图必须含全部结局**，不可只画其中几个；**亚组森林必须按亚组类别分区呈现**（`facet_grid(类别~)` 或分区标题），不可平铺成无结构列表。

### 12ter 每张图出后强制「美观 + 合理性」自检（每生成/重渲一张图都必做，任一不过 = 返工）

**先 Read PNG/PDF 看，再逐条过——不只看好不好看，更看数字对不对：**

1. **数值可溯源、不过时**：图上每个数字都能在数据源（表 / `0_result_summaries.md`）查到且**完全一致**；schematic / 标注里的数字**禁止硬编码**（硬编码必随结果更新而过时——如设计图 AUC 未随主结果重跑而停在旧值）；与全文 headline 不矛盾。
2. **无统计假象 / 不合常理**：警惕「所有格子同值 / 全为同一常数 / 全 ±同一数」——多是计算 bug（典型：对仅 2 组做标准化 `scale()` 恒得 ±0.707，热图全 ±0.7 是假象不是信号）；检查量级、方向、分布、趋势是否符合常识与已知结论（如校准 slope>1 应表现为预测向中部压缩、不该出现矛盾形状）。**发现可疑模式 = 疑点，先判定是画图 / 原数据 / 方法哪一层的问题再出图**。
3. **表达正确**：分类映射无 NA、图例不重复不缺、**图例不压任何数据曲线/点/柱/注释（重叠即返工，改外嵌或挪到空白象限）**、标签无内部变量名、坐标/标签/标题无裁切、图型匹配数据（AUC 用点+CI 而非截断柱）、多结局图含全部结局、与同篇其它图 theme/配色/布局一致。

**未做完这三条自检 = 图未完成**；任一条触发即回到代码层定位根因（画图 bug / 数据陈旧 / 方法错误）后重出，不带病交付。
