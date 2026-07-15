# ============================================================
# 开题 / 答辩 / 正式研究汇报 PPT 骨架（区别于组会分享 deck_skeleton.R）
# 蓝本来自 5 份真实开题答辩 PPT 的共性结构、用词与版式。按主题填内容即可。
# 体裁特征（与组会 deck 的关键差异）：
#   1. 篇幅长：20-40 页（组会才 13-15）；研究方法是主体，可占全篇 1/3~1/2。
#   2. 用章节分隔页（每个一级章节前插一张只有章节名的过渡页）——这是答辩体裁的规范，
#      与组会 deck"不加过渡页"相反。用 sysu_add_section()。
#   3. 固定骨架顺序（见下）；封面含汇报人/指导老师/时间；结尾"请各位老师批评指正！"。
#   4. 技术路线图必备（一张总流程图统领研究内容）。
# ============================================================
#
# ---------- 规范结构（开题/答辩通用，按需增删页，不改顺序） ----------
#   00 封面          标题（研究全称，名词短语）/ 汇报人：X / 指导老师：X / 时间
#   00 目录          列一级章节名（立题依据 / 研究目的与内容 / 研究方法 / 创新点与可行性 / 进度安排）
#   一 立题依据(研究背景)   3-6 页：① 研究意义 → ② 国内外研究现状 → ③ 现存不足与科学问题
#   二 研究目的与内容       2-4 页：① 研究目的（总目标）→ ② 研究内容（按子课题分点，与方法对应）
#   三 研究方法            主体，6-20 页：每个研究内容展开——总流程图 → 分步骤（数据/模型/模拟/评价指标）
#   四 技术路线图          1 页：一张总技术路线流程图（数据→处理→建模→验证→应用）
#   五 创新点与可行性分析   2-4 页：① 创新点（3 点内）② 可行性（数据/方法/平台/前期基础/团队）
#   六 进度安排            1-2 页：甘特式进度表（阶段 × 时间）
#   (七 参考文献)          可选 1-2 页：主要文献编号列出
#   尾 致谢页              "请各位老师批评指正！"
#
# ---------- 规范用词库（直接取用，勿口语化） ----------
#   章节名：立题依据 / 研究背景 / 研究现状与不足 / 研究目的与内容 / 研究方法 /
#           技术路线 / 创新点 / 可行性分析 / 进度安排 / 研究计划 / 参考文献
#   段落标签：研究意义 / 国内外研究现状 / 科学问题 / 研究目的 / 研究内容 / 方法流程 /
#           数据来源 / 评价指标 / 创新点 / 可行性 / 预期成果
#   方法对比表表头：方法名称 | 核心思想 | 主要优势 | 主要局限
#   评价指标常用：偏倚（Bias）/ 均方根误差（RMSE）/ 95%CI 覆盖率 / AUC / 灵敏度 / 特异度
#   封面署名：汇报人：X　　指导老师：X 副教授　　时间：2025.12
#   结尾：请各位老师批评指正！ / 恳请老师们批评指正！
#   英文缩写首次出现给全称：PS（Propensity Score，倾向性评分）等。
#
# ---------- 设计基调（来自真实 deck） ----------
#   主色：中大深绿 #014924（章节号/标题竖条/表头），强调用克制的红 #C00000（仅关键结论 1-2 处）。
#   字体：中文微软雅黑/宋体、英文 Times New Roman（toolkit .fp() 已自动分流）。
#   不追求每页配图。背景证据、机制、随访/处理流程和技术路线需要图；
#   目的、定义、公式、创新、可行性和计划页优先用文字、表格、公式或时间轴。
#   科研图解先读 research-visuals/references/research-figure-patterns.md，逐页判定主要表达方式。
# ============================================================

Sys.setlocale("LC_ALL", "Chinese (Simplified)_China.utf8")
skill_roots <- path.expand(c(
  Sys.getenv("EPIAGENTKIT_SKILLS"), Sys.getenv("EPICLAUDE_SKILLS"),
  "~/.claude/skills", "~/.agents/skills", "~/.codex/skills"
))
skill_dirs <- file.path(skill_roots[nzchar(skill_roots)], "sysu-ppt")
SKILL <- skill_dirs[dir.exists(skill_dirs)][1]
if (!length(SKILL) || is.na(SKILL)) stop("找不到 sysu-ppt；请设置 EPIAGENTKIT_SKILLS")
source(file.path(SKILL, "scripts", "sysu_toolkit.R"))

TPL <- "default"
FIG <- "figures"        # 流程/结构/路线及场景配图按 research-visuals 优先生成 PNG
f <- function(x) file.path(FIG, x)

ppt <- sysu_init(TPL)

# ---- 封面 ----
ppt <- sysu_add_cover(ppt, "（研究题目全称，名词短语）", "English Title (optional)",
                      "汇报人：（姓名）　　指导老师：（姓名）副教授", "2025.12")

# ---- 目录（列一级章节）----
ppt <- sysu_add_text(ppt, "目录", block_list(
  num_item("一", "立题依据", ""),
  num_item("二", "研究目的与内容", ""),
  num_item("三", "研究方法", ""),
  num_item("四", "创新点与可行性分析", ""),
  num_item("五", "进度安排", "")))

# ============ 一、立题依据 ============
ppt <- sysu_add_section(ppt, "一、立题依据")     # 章节分隔页（答辩体裁要用）

# 1.1 研究意义：左文右示意图
ppt <- sysu_add_text_image(ppt, "1.1 研究意义",
  block_list(
    prose(bd("研究意义　"), tx("点明该问题对学科/公共卫生/临床决策的重要性，一两句。")),
    prose(bd("现实需求　"), tx("当前实践中的痛点或政策需求。"))),
  f("background.png"), img_w = 5.2, img_h = 4.0, side = "right", caption = "图1　研究背景示意")

# 1.2 国内外研究现状：方法对比三线表
cmp <- data.frame(
  方法名称 = c("方法 A", "方法 B"),
  核心思想 = c("……", "……"),
  主要优势 = c("……", "……"),
  主要局限 = c("……", "……"), check.names = FALSE)
ppt <- sysu_add_table(ppt, "1.2 国内外研究现状",
  sysu_flextable(cmp, widths = c(2.2, 3.6, 2.6, 2.6), fsize = 14),
  note = "注：按是否支持连续处理变量、能否捕捉非线性等维度比较。")

# 1.3 现存不足与科学问题：纯文字，落到本研究要解决的科学问题
ppt <- sysu_add_text(ppt, "1.3 现存不足与科学问题", block_list(
  prose(bd("变量选择　"), tx("现有方法在 …… 上的局限。")),
  prose(bd("效应估计　"), tx("现有方法在 …… 上的局限。")),
  prose(bd("科学问题　"), tx("由此提出本研究拟回答的核心科学问题。"))))

# ============ 二、研究目的与内容 ============
ppt <- sysu_add_section(ppt, "二、研究目的与内容")

ppt <- sysu_add_text(ppt, "2.1 研究目的", block_list(
  prose(bd("总目标　"), tx("陈述研究总目标：构建 X 方法，并应用于 Y 数据以回答某一科学问题。"))))

ppt <- sysu_add_text(ppt, "2.2 研究内容", block_list(
  num_item("内容一", "方法构建", "拟解决的方法学问题与技术路径。"),
  num_item("内容二", "模拟评价", "模拟场景设计 + 与基准方法的对照指标。"),
  num_item("内容三", "实证应用", "真实队列数据上的适用性检验与效应量化。")))

# ============ 三、研究方法（主体）============
ppt <- sysu_add_section(ppt, "三、研究方法")

# 3.x 每个研究内容：先总流程图，再分步细化
ppt <- sysu_add_image_caption(ppt, "3.1 方法总流程",
  f("method_flow.png"), img_w = 9.8, img_h = 4.4,
  block_list(prose(bd("方法流程　"), tx("概述方法整体流程，串联下列各步骤。"))), img_pos = "top",
  caption = "图2　方法总流程")

ppt <- sysu_add_text_image(ppt, "3.2 第一步：变量筛选",
  block_list(prose(bd("目标函数　"), tx("配合右图的两三句关键设定。"))),
  f("step1.png"), img_w = 5.4, img_h = 4.2, side = "right", caption = "图3　第一步示意")

ppt <- sysu_add_text_image(ppt, "3.3 第二步：效应估计",
  block_list(prose(bd("平衡权重　"), tx("两三句说明估计量构造。"))),
  f("step2.png"), img_w = 5.4, img_h = 4.2, side = "right", caption = "图4　第二步示意")

ppt <- sysu_add_text(ppt, "3.4 模拟研究与评价", block_list(
  prose(bd("模拟场景　"), tx("线性 / 非线性无交互 / 非线性有交互三种场景。")),
  prose(bd("评价指标　"), tx("偏倚（Bias）、均方根误差（RMSE）、95%CI 覆盖率。"))))

# ============ 四、技术路线图 ============
ppt <- sysu_add_image(ppt, "四、技术路线图",
  f("roadmap.png"), img_w = 11.0, img_h = 5.4, caption = "图5　技术路线")

# ============ 五、创新点与可行性分析 ============
ppt <- sysu_add_section(ppt, "五、创新点与可行性分析")

ppt <- sysu_add_text(ppt, "5.1 创新点", block_list(
  num_item("1", "方法创新", "陈述方法学层面的创新点及其相对现有方法的改进。"),
  num_item("2", "应用创新", "陈述在数据或应用场景层面的创新点。")))

ppt <- sysu_add_text(ppt, "5.2 可行性分析", block_list(
  prose(bd("数据可行　"), tx("数据来源与样本量。")),
  prose(bd("方法可行　"), tx("方法成熟度与前期基础。")),
  prose(bd("平台可行　"), tx("计算平台与团队支撑。"))))

# ============ 六、进度安排 ============
plan <- data.frame(
  阶段 = c("第一阶段", "第二阶段", "第三阶段"),
  时间 = c("2025.12–2026.06", "2026.07–2026.12", "2027.01–2027.06"),
  任务 = c("方法构建与模拟", "实证数据分析", "论文撰写与答辩"), check.names = FALSE)
ppt <- sysu_add_table(ppt, "六、进度安排",
  sysu_flextable(plan, widths = c(2.2, 3.8, 4.4), fsize = 16))

# ---- 致谢页 ----
ppt <- sysu_add_section(ppt, "请各位老师批评指正！")

sysu_save(ppt, "输出_开题报告.pptx", genre = "formal")
cat("done. slides =", length(ppt), "\n")
