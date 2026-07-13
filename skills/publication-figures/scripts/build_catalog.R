# ============================================================
# 配方库检索目录生成器（publication-figures）
# 作用：①把本地全库的教程(.md)+预览(png/jpg/pdf)同步进 skill 各配方文件夹
#       （work.R 已在；跳过 260MB 体量的原始数据）；②扫全部配方自动生成
#       references/recipes_catalog.md —— 一次 grep 即按意图定位配方的单一路由面。
# 用法：Rscript build_catalog.R   （库更新后重跑即可重生成）
# 自由度：低（确定性脚本）。
# ============================================================
`%||%` <- function(a, b) if (is.null(a) || length(a) == 0) b else a

# skill 根：优先命令行 --skill= / EPIAGENTKIT_SKILLS，再检测 Claude/Codex 用户目录
.args <- commandArgs(trailingOnly = TRUE)
.sk <- sub("^--skill=", "", .args[grepl("^--skill=", .args)])
.skill_roots <- path.expand(c(
  Sys.getenv("EPIAGENTKIT_SKILLS"),
  Sys.getenv("EPICLAUDE_SKILLS"),
  "~/.claude/skills",
  "~/.agents/skills",
  "~/.codex/skills"
))
.skill_candidates <- file.path(.skill_roots[nzchar(.skill_roots)], "publication-figures")
.default_skill <- .skill_candidates[dir.exists(.skill_candidates)][1]
if (!length(.sk) && (length(.default_skill) == 0 || is.na(.default_skill))) {
  stop("找不到 publication-figures；请传 --skill=... 或设置 EPIAGENTKIT_SKILLS")
}
SKILL <- if (length(.sk)) .sk else .default_skill
ADV  <- file.path(SKILL, "references", "recipes_advanced")
COMMON <- file.path(SKILL, "references", "recipes_common_50")
# 本地全库（含教程/预览/数据）——只读来源
SRC_ADV <- Sys.getenv("PUBLICATION_FIGURES_SOURCE", unset = "")

# ---- 同步教程+预览进 skill（跳过 data；让 skill 自包含）----
sync_rich <- function() {
  if (!dir.exists(SRC_ADV)) { message("本地源不存在，跳过同步：", SRC_ADV); return(invisible()) }
  n <- 0
  for (d in list.dirs(SRC_ADV, recursive = FALSE)) {
    nm <- basename(d)
    dest <- file.path(ADV, nm)
    if (!dir.exists(dest)) dir.create(dest, recursive = TRUE)   # 新增缺失文件夹
    files <- list.files(d, full.names = TRUE, recursive = TRUE,  # 含嵌套子文件夹
                        pattern = "\\.(md|png|jpg|jpeg|pdf|R)$", ignore.case = TRUE)
    for (f in files) {
      tgt <- file.path(dest, basename(f))
      if (!file.exists(tgt) || file.info(f)$mtime > file.info(tgt)$mtime) {
        file.copy(f, tgt, overwrite = TRUE); n <- n + 1
      }
    }
  }
  message("同步教程/预览/脚本：", n, " 个文件")
}

# ---- 抽取一个配方文件夹的元数据 ----
clean_name <- function(nm) {
  nm <- gsub("\\[会员专享\\]\\s*", "", nm)
  nm <- gsub("[（(]?20\\d{6}[）)]?", "", nm)          # 去日期
  nm <- gsub("-0?\\d{6,8}$", "", nm)
  trimws(nm)
}
pkgs_of <- function(folder) {
  rs <- list.files(folder, pattern = "\\.R$", full.names = TRUE, ignore.case = TRUE)
  if (length(rs) == 0) return("")
  txt <- unlist(lapply(rs, function(f) tryCatch(readLines(f, warn = FALSE, encoding = "UTF-8"),
                                                error = function(e) character(0))))
  m <- regmatches(txt, gregexpr("(?:library|require)\\(([A-Za-z0-9._]+)\\)", txt, perl = TRUE))
  m <- unlist(m)
  pk <- gsub(".*\\(([A-Za-z0-9._]+)\\).*", "\\1", m)
  # pacman::p_load(a,b,c)
  pl <- regmatches(txt, regexpr("p_load\\(([^)]*)\\)", txt))
  if (length(pl)) pk <- c(pk, trimws(unlist(strsplit(gsub(".*p_load\\(|\\).*", "", pl), ","))))
  pk <- unique(pk[nzchar(pk) & pk != "tidyverse"])
  paste(head(pk, 6), collapse = ", ")
}
tech_of <- function(folder) {
  mds <- list.files(folder, pattern = "\\.md$", full.names = TRUE, ignore.case = TRUE)
  if (length(mds) == 0) return("")
  txt <- tryCatch(readLines(mds[[1]], warn = FALSE, encoding = "UTF-8"), error = function(e) character(0))
  # 找首条含"本节/介绍/绘制"的行，去 markdown 与促销
  cand <- txt[grepl("本节|介绍|如何", txt)]
  line <- (cand %||% txt[nzchar(trimws(txt))])[1]
  if (is.na(line)) return("")
  line <- gsub("^[>#*\\s]+|[*`]", "", line)
  line <- gsub("欢迎关注.*|公众号.*|淘宝.*|微信.*|VIP.*", "", line)
  line <- trimws(line)
  if (nchar(line) > 70) line <- paste0(substr(line, 1, 70), "…")
  line
}
flags_of <- function(folder) {
  has_md <- length(list.files(folder, pattern = "\\.md$", ignore.case = TRUE)) > 0
  has_pv <- length(list.files(folder, pattern = "\\.(png|jpg|jpeg|pdf)$", ignore.case = TRUE)) > 0
  paste0(if (has_md) "教程" else "", if (has_md && has_pv) "+" else "", if (has_pv) "预览" else "")
}

build_catalog <- function() {
  rows <- list()
  # 进阶库
  for (d in list.dirs(ADV, recursive = FALSE)) {
    nm <- basename(d)
    rows[[length(rows) + 1]] <- data.frame(
      区 = "进阶", 图型 = clean_name(nm), 关键包 = pkgs_of(d), 技法 = tech_of(d),
      资料 = flags_of(d), 路径 = file.path("recipes_advanced", nm),
      stringsAsFactors = FALSE)
  }
  # 常用 50（单 .R 文件）
  for (f in list.files(COMMON, pattern = "\\.R$", full.names = TRUE)) {
    nm <- sub("\\.R$", "", basename(f))
    txt <- tryCatch(readLines(f, warn = FALSE, encoding = "UTF-8"), error = function(e) character(0))
    m <- unlist(regmatches(txt, gregexpr("(?:library|require)\\(([A-Za-z0-9._]+)\\)", txt, perl = TRUE)))
    pk <- unique(gsub(".*\\(([A-Za-z0-9._]+)\\).*", "\\1", m))
    pk <- paste(head(pk[nzchar(pk) & pk != "tidyverse"], 6), collapse = ", ")
    rows[[length(rows) + 1]] <- data.frame(
      区 = "常用", 图型 = gsub("^[0-9]+", "", nm), 关键包 = pk, 技法 = "",
      资料 = "代码", 路径 = file.path("recipes_common_50", basename(f)),
      stringsAsFactors = FALSE)
  }
  df <- do.call(rbind, rows)
  df <- df[order(df$区, df$图型), ]
  out <- file.path(SKILL, "references", "recipes_catalog.md")
  con <- file(out, open = "w", encoding = "UTF-8")
  writeLines(c(
    "# 配方检索目录（recipes_catalog）—— 出图前 grep 这里按意图定位",
    "",
    paste0("> 自动生成（scripts/build_catalog.R），共 ", nrow(df), " 条。库更新后重跑重生成。"),
    "> 用法：按意图关键词（热图/森林/云雨/桑基/网络/生存/ROC/火山…）grep 本表 → 命中行的「路径」开 work.R（进阶配方同目录常有 .md 教程 + 渲染预览，先 Read 预览看效果再借鉴）。",
    "> 落地仍按 SKILL.md §1–§12 重写为发表级（原脚本多为教程风，不达发表级）。",
    "",
    "| 区 | 图型 | 关键包 | 技法 | 资料 | 路径 |",
    "|---|---|---|---|---|---|"
  ), con)
  for (i in seq_len(nrow(df))) {
    writeLines(sprintf("| %s | %s | %s | %s | %s | `%s` |",
      df$区[i], df$图型[i], df$关键包[i], df$技法[i], df$资料[i], df$路径[i]), con)
  }
  close(con)
  message("生成目录：", out, "（", nrow(df), " 条）")
}

sync_rich()
build_catalog()
