# ============================================================
# 组会汇报 / 文献分享 PPT 骨架模板（13-15 页）。
# CRITICAL：禁止目录页；禁止任何章节分隔/过渡页；封面后直接进入实质内容。
# 生成脚本不得调用 sysu_add_section()，主题切换只用内容页标题编号表达。
# 按主题填内容即可。体现推荐结构与版式搭配。
# 用法：复制到目标文件夹，改主题/内容/模板，Rscript 运行。
# 原则：精确表达，不堆字；结构/机制优先画图。
# 开题/答辩/正式研究汇报请改用 defense_blueprint.R（更长、含章节页与目录）。
#
# 取自答辩 deck 的可复用做法（组会也适用）：
#   - 方法对比用四列三线表「方法名称 | 核心思想 | 主要优势 | 主要局限」，比泛泛的"维度×甲乙"更有信息量（见下方对比页）。
#   - 段落标签用规范名词（研究意义/核心思想/评价指标/局限性…），措辞库见 defense_blueprint.R 顶部注释。
#   - 主色中大深绿 #014924；强调用克制的红 #C00000（全篇 1-2 处关键结论）；每页优先用图。
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

TPL <- "default"        # 默认中大医学；用户要原公卫模板时改 "模板2"
FIG <- "figures"        # 非统计图解按 image-diagrams 优先生成 PNG；统计图走 publication-figures
f <- function(x) file.path(FIG, x)

ppt <- sysu_init(TPL)

# 封面：标题 + 一行英文副标题 + 作者/日期（勿堆多行小字）
ppt <- sysu_add_cover(ppt, "汇报主题", "English Subtitle", "汇报人：（姓名）", "2026 组会学习分享")

# 1 背景：左文右示意图（文字 3-4 段，精炼；右图讲清概念）
ppt <- sysu_add_text_image(ppt, "1 背景：为什么关注它",
  block_list(
    prose(bd("现状　"), tx("点明领域现状或核心痛点。")),
    prose(bd("问题　"), tx("点出核心问题，避免铺陈。")),
    prose(bd("思路　"), tx("本主题给出的解决思路。"))),
  f("concept.png"), img_w = 5.5, img_h = 4.0, side = "right",
  caption = "图1　核心概念示意")

# 1.1 关键定义：纯文字（成段 + 少量编号，写清即可）
ppt <- sysu_add_text(ppt, "1.1 核心概念", block_list(
  prose(bd("定义　"), tx("精确定义，一两句。")),
  num_item("①", "要素一", "简短说明。"),
  num_item("②", "要素二", "简短说明。"),
  prose(bd("说明　"), tx("给出对该概念的直觉性说明。"))))

# 2 方法/分类：整图或上下图文（谱系/流程一图胜千言）
ppt <- sysu_add_image_caption(ppt, "2 方法谱系",
  f("taxonomy.png"), img_w = 9.8, img_h = 4.4,
  block_list(prose(bd("要点　"), tx("概述下列各类方法的共同脉络与划分依据。"))), img_pos = "top",
  caption = "图2　方法谱系总览")

# 2.1 并列要点：卡片（真正并列的 3-4 项，全篇≤2-3 页卡片）
ppt <- sysu_add_cards(ppt, "2.1 三种主流方法",
  list(
    list(tag = "①", head = "方法 A", body = "简述核心机制与代表性工作。"),
    list(tag = "②", head = "方法 B", body = "简述核心机制与代表性工作。"),
    list(tag = "③", head = "方法 C", body = "简述核心机制与代表性工作。")),
  intro = block_list(prose(bd("关键　"), tx("引出三者的共同点或区别。"))))

# 2.2 机制细节：左文右图（流程图讲清步骤）
ppt <- sysu_add_text_image(ppt, "2.2 机制细节",
  block_list(prose(bd("关键　"), tx("配合右图的两三句要点。"))),
  f("mechanism.png"), img_w = 5.4, img_h = 4.2, side = "right",
  caption = "图3　机制流程")

# 3 对比/评估：四列三线表（答辩 deck 的高信息量对比范式，组会讲方法同样适用）
cmp <- data.frame(
  方法名称 = c("方法 A", "方法 B"),
  核心思想 = c("简述核心机制。", "简述核心机制。"),
  主要优势 = c("适用场景/长处。", "适用场景/长处。"),
  主要局限 = c("失效条件/代价。", "失效条件/代价。"), check.names = FALSE)
ppt <- sysu_add_table(ppt, "3 方法对比",
  sysu_flextable(cmp, widths = c(2.0, 3.2, 2.8, 2.8), fsize = 14),
  note = "注：按核心思想、适用条件与局限三维比较。")

# 3.1 实操：代码/示例页
ppt <- sysu_add_code(ppt, "3.1 实操示例",
  c("library(pkg)", "fit <- model(y ~ x, data = d)", "summary(fit)"),
  intro = block_list(prose(bd("步骤　"), tx("概述该示例的操作流程。"))))

# 4 决策/建议：左文右流程图
ppt <- sysu_add_text_image(ppt, "4 决策建议",
  block_list(
    prose(bd("默认　"), tx("默认怎么做。")),
    prose(bd("例外　"), tx("什么情况下换做法。"))),
  f("decision.png"), img_w = 5.2, img_h = 4.4, side = "right",
  caption = "图4　决策流程")

# 4.1 总结：纯文字（编号收束 take-home）
ppt <- sysu_add_text(ppt, "4.1 Take-home", block_list(
  num_item("1", "结论一句。"),
  num_item("2", "结论一句。"),
  num_item("3", "结论一句。"),
  prose(bd("核心结论　"), tx("最精炼的收尾。"))))

# 参考文献
ppt <- sysu_add_text(ppt, "主要参考文献", block_list(
  prose(tx("1. 作者. 标题. 期刊. 年.")),
  prose(tx("2. 作者. 标题. 期刊. 年."))))

sysu_save(ppt, "输出_主题.pptx", genre = "meeting")
cat("done. slides =", length(ppt), "\n")
