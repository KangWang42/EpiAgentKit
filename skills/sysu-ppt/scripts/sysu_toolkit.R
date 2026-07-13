# ============================================================================
# SYSU Public Health PPT Toolkit  v2
# 中山大学公共卫生学院组会汇报 PPT 生成工具箱
# ----------------------------------------------------------------------------
# 设计目标：
#   1. 字体：中文 宋体 / 英文 Times New Roman（同一段落自动分流）
#   2. 版式多样：纯文字 / 双栏文字 / 左右图文 / 上下图文 / 整图 / 表格 / 文表 / 代码示例 / 章节页
#   3. 充实排版：正文区占满约 80% 版面，标题带主色下划线规则
#   4. 强调：重点内容加粗 + 主色
# ============================================================================

library(officer)
library(magrittr)
library(flextable)

# 在 source() 执行时立即锁定 skill 根目录；不要等到函数调用后再读 sys.frame()。
.SYSU_TOOLKIT_FILE <- tryCatch(
  normalizePath(sys.frame(1)$ofile, winslash = "/", mustWork = TRUE),
  error = function(e) NA_character_
)
.SYSU_SKILL_DIR <- if (!is.na(.SYSU_TOOLKIT_FILE)) dirname(dirname(.SYSU_TOOLKIT_FILE)) else NA_character_

# 结果单一真源取数（C1：下游取数禁手敲）。数字只在 results.yaml 改，PPT 一律 val() 取。
# 用法：tx(paste0("S2 vs S1 差异 ", val("07_paper/results.yaml", "S2_vs_S1_diff")))
val <- function(path, key, which = "full") {
  doc <- yaml::read_yaml(path)
  v <- doc$results[[key]]$rendered[[which]]
  if (is.null(v)) stop(sprintf("results.yaml 取数失败：%s / %s", key, which))
  v
}

# ============================================================================
# 1. 全局样式
# ============================================================================
SYSU <- list(
  col = list(title = "#006D5B", accent = "#005825", text = "#1A1A1A",
             gray = "#666666", band = "#006D5B", box = "#F2F6F4"),
  en  = "Times New Roman",   # 英文 / 拉丁字符
  cn  = "宋体",              # 中文（东亚字符）
  mono = "Consolas",
  sz  = list(cover_title = 38, cover_sub = 24, title = 24, h2 = 18,
             body = 16, small = 13, code = 14, page = 12)
)

# 几何布局（英寸，幻灯片 13.333 x 7.5）
G <- list(
  # 与模板 "Title and Content" 的绿色竖条(矩形 8, x=0.667,y=0.50,h=0.575)对齐：
  # 标题文字框左缘紧贴竖条右侧、垂直居中于竖条，底部横线与竖条底缘齐平。
  title    = ph_location(left = 0.92, top = 0.50, width = 11.5, height = 0.575),
  body     = ph_location(left = 0.85, top = 1.58, width = 11.60, height = 5.45),
  col_l    = ph_location(left = 0.85, top = 1.58, width = 5.55,  height = 5.45),
  col_r    = ph_location(left = 7.00, top = 1.58, width = 5.45,  height = 5.45),
  txt_l    = ph_location(left = 0.85, top = 1.62, width = 5.55,  height = 5.40),
  top_box  = ph_location(left = 0.85, top = 1.55, width = 11.60, height = 1.30),
  bot_box  = ph_location(left = 0.85, top = 5.10, width = 11.60, height = 1.90),
  page     = ph_location(left = 12.35, top = 7.05, width = 0.80, height = 0.35)
)

# ============================================================================
# 1b. 模板注册表（default = 原模板2中大医学；public_health = 原模板1公卫学院）
# ----------------------------------------------------------------------------
# 不同模板的版式命名不同：default 用中文布局名，public_health 用英文布局名。
# master 名在 sysu_init 时从文件读取，避免抄错隐藏字符。
# ============================================================================
.TPL_REG <- list(
  default = list(file = "template.pptx",
                 cover = "1_空白", content = "3_空白", blank = "空白",
                 cover_style = "native"),  # 棕榈封面/绿框+校徽+水印
  public_health = list(file = "template-公卫学院.pptx",
                       cover = "标题幻灯片", content = "Title and Content", blank = "Blank",
                       cover_style = "green")
)
.ACT <- new.env(parent = emptyenv())   # 活动模板：master/cover/content/blank/cover_style

.assets_dir <- function() {
  skill_roots <- path.expand(c(
    Sys.getenv("EPICLAUDE_SKILLS"),
    "~/.claude/skills", "~/.agents/skills", "~/.codex/skills"
  ))
  cand <- c(if (!is.na(.SYSU_SKILL_DIR)) file.path(.SYSU_SKILL_DIR, "assets") else NA_character_,
            "assets", "../assets",
            file.path(skill_roots[nzchar(skill_roots)], "sysu-ppt", "assets"))
  cand <- cand[!is.na(cand)]
  hit <- cand[dir.exists(cand)]
  if (length(hit)) hit[1] else NA_character_
}

# ============================================================================
# 2. 文本属性工厂（中英自动分流）
# ============================================================================
#' 生成 run 文本属性
.fp <- function(size = SYSU$sz$body, bold = FALSE, color = SYSU$col$text,
                italic = FALSE, mono = FALSE) {
  lat <- if (mono) SYSU$mono else SYSU$en
  ea  <- if (mono) SYSU$mono else SYSU$cn
  fp_text(font.size = size, bold = bold, italic = italic, color = color,
          font.family = lat, hansi.family = ea, eastasia.family = ea, cs.family = lat)
}

# 行内文本助手
tx  <- function(text, size = SYSU$sz$body, color = SYSU$col$text) ftext(text, .fp(size, FALSE, color))
bd  <- function(text, size = SYSU$sz$body, color = SYSU$col$accent) ftext(text, .fp(size, TRUE, color))
cd  <- function(text, size = SYSU$sz$code, color = SYSU$col$text) ftext(text, .fp(size, FALSE, color, mono = TRUE))
sp  <- function(h = 8) fpar(ftext("", .fp(h)))   # 垂直间距
para <- function(...) fpar(...)

# 项目符号段（主色圆点 + 自动行距与段后间距，撑满版面）
bullet <- function(head, body = "", size = SYSU$sz$body) {
  runs <- if (nzchar(body)) list(bd(paste0("● ", head), size), tx(body, size))
          else list(bd(paste0("● ", head), size))
  do.call(fpar, c(runs, list(fp_p = fp_par(line_spacing = 1.45, padding.bottom = 9, padding.top = 2))))
}
# 次级项目符号（缩进、空心点）
sub_bullet <- function(text, size = SYSU$sz$body - 1) {
  fpar(tx(paste0("○ ", text), size),
       fp_p = fp_par(line_spacing = 1.35, padding.left = 30, padding.bottom = 5))
}

# 成段正文（两端对齐 + 较大行距），用于减少"满屏列表"、增加文字感。
# 接受若干 ftext run，例如 prose(bd("背景："), tx("一段较长的说明文字……"))
prose <- function(..., align = "left") {
  fpar(..., fp_p = fp_par(line_spacing = 1.5, padding.bottom = 11, padding.top = 2, text.align = align))
}

# 层级小标题（框架感：1.1 / 1.1.1 / ① 等），主色加粗，自动留白。
heading <- function(text, size = SYSU$sz$h2) {
  fpar(ftext(text, .fp(size, TRUE, SYSU$col$title)),
       fp_p = fp_par(line_spacing = 1.2, padding.top = 7, padding.bottom = 4))
}

# 带编号条目（编号自带语义，不再加圆点）。num 例："①" / "1." / "(1)"
#   - 有 body：编号+小标题加粗主色，后接正文  →  "① 信息损失：正文……"
#   - 仅 head：编号加粗，句子正常字重           →  "1 一句结论……"
num_item <- function(num, head, body = "", size = SYSU$sz$body) {
  runs <- if (nzchar(body)) list(bd(paste0(num, " ", head, "："), size), tx(body, size))
          else if (nzchar(head)) list(bd(paste0(num, " "), size), tx(head, size))
          else list(bd(num, size))
  do.call(fpar, c(runs, list(fp_p = fp_par(line_spacing = 1.45, padding.bottom = 9, padding.top = 2, padding.left = 4))))
}

# ============================================================================
# 3. 内部基础函数
# ============================================================================
.title_fp  <- function() .fp(SYSU$sz$title, TRUE, SYSU$col$title)
# 竖条由模板 "矩形 8" 提供；此处仅加底部主色横线，与竖条底缘齐平，二者构成对齐的 L 形。
.title_par <- function() fp_par(border.bottom = fp_border(color = SYSU$col$accent, width = 1.2),
                                padding.left = 6, padding.bottom = 6, padding.top = 0)

# 细横线（flextable 实现，跨模板可靠渲染；border 在部分版式里不渲染时用它）
.rule_ft <- function(w, color = SYSU$col$accent, lw = 1.4) {
  ft <- flextable(data.frame(x = ""))
  ft <- delete_part(ft, "header")
  ft <- border_remove(ft)
  ft <- hline_bottom(ft, border = fp_border(color = color, width = lw), part = "body")
  ft <- width(ft, j = 1, width = w)
  ft <- height(ft, i = 1, height = 0.04, part = "body")
  ft <- padding(ft, padding = 0, part = "body")
  ft <- fontsize(ft, size = 1, part = "body")
  ft <- color(ft, color = "white", part = "body")
  ft
}

.add_title <- function(ppt, title) {
  ppt <- ph_with(ppt, value = fpar(ftext(title, .title_fp()), fp_p = .title_par()),
                 location = G$title)
  # 当前默认中大医学模板无绿色竖条、段落边框不渲染：补一条可靠的 flextable 横线
  if (exists("cover_style", envir = .ACT) && identical(.L("cover_style"), "native")) {
    ppt <- ph_with(ppt, .rule_ft(11.5),
                   location = ph_location(left = 0.92, top = 1.04, width = 11.5, height = 0.06))
  }
  ppt
}

.add_pagenum <- function(ppt) {
  idx <- length(ppt) - 1L                 # 封面不计页码
  if (idx < 1L) return(ppt)
  fpp <- .fp(SYSU$sz$page, FALSE, SYSU$col$gray)
  ph_with(ppt, value = fpar(ftext(as.character(idx), fpp), fp_p = fp_par(text.align = "right")),
          location = G$page)
}

.new <- function(ppt, title) {
  ppt <- add_slide(ppt, layout = .L("content"), master = .L("master"))
  ppt <- .add_title(ppt, title)
  ppt
}

# 读取 SVG viewBox 宽高比（w/h），不依赖渲染器。
.svg_aspect <- function(path) {
  x <- paste(readLines(path, warn = FALSE, encoding = "UTF-8"), collapse = " ")
  m <- regexec("viewBox\\s*=\\s*['\"]\\s*[-+0-9.eE]+[ ,]+[-+0-9.eE]+[ ,]+([-+0-9.eE]+)[ ,]+([-+0-9.eE]+)\\s*['\"]",
               x, perl = TRUE)
  hit <- regmatches(x, m)[[1]]
  if (length(hit) == 3) {
    wh <- suppressWarnings(as.numeric(hit[2:3]))
    if (all(is.finite(wh)) && all(wh > 0)) return(wh[1] / wh[2])
  }
  NA_real_
}

# 读取 PNG 或 SVG 的真实宽高比（w/h）
.img_aspect <- function(path) {
  if (requireNamespace("png", quietly = TRUE) && grepl("\\.png$", path, ignore.case = TRUE)) {
    d <- dim(png::readPNG(path)); return(d[2] / d[1])
  }
  if (grepl("\\.svg$", path, ignore.case = TRUE)) return(.svg_aspect(path))
  NA_real_
}
# 等比缩放：在 (max_w × max_h) 盒子内按图片真实比例取最大尺寸，保证视觉不变形
.fit <- function(path, max_w, max_h) {
  a <- .img_aspect(path)
  if (is.na(a)) return(c(w = max_w, h = max_h))   # 非 PNG 时退回给定尺寸
  w <- max_w; h <- w / a
  if (h > max_h) { h <- max_h; w <- h * a }
  c(w = w, h = h)
}

# 图片智能居中（保持给定尺寸，水平居中，垂直在正文区居中）
.center_img <- function(img, w, h, top = NULL) {
  left <- (13.333 - w) / 2
  if (is.null(top)) top <- 1.58 + (5.45 - h) / 2
  ph_location(left = left, top = top, width = w, height = h)
}

# officer 0.7.x 支持 SVG，但写入 PPTX 时需要 rsvg；提前给出明确错误。
.external_media <- function(path, width, height) {
  if (grepl("\\.svg$", path, ignore.case = TRUE) &&
      !requireNamespace("rsvg", quietly = TRUE)) {
    stop("嵌入 SVG 需要 R 包 rsvg；请安装后重试，或使用同名 PNG 回退。")
  }
  external_img(path, width = width, height = height)
}

# ============================================================================
# 4. 公开 API
# ============================================================================

#' 初始化（读取模板并清空所有演示页，仅保留母版布局）
#' @param template 模板："default"/"模板1"/"medical" 为默认中大医学模板；
#'   "模板2"/"公卫" 为原公卫学院模板；也可传 .pptx 完整路径。
sysu_init <- function(template = "default") {
  key <- switch(template,
                "default" = "default", "模板1" = "default", "模板一" = "default",
                "medical" = "default", "医学" = "default",
                "public-health" = "public_health", "public_health" = "public_health",
                "模板2" = "public_health", "模板二" = "public_health", "公卫" = "public_health",
                NA_character_)
  if (!is.na(key)) {
    reg  <- .TPL_REG[[key]]
    ad   <- .assets_dir()
    path <- if (!is.na(ad)) file.path(ad, reg$file) else reg$file
  } else {
    path <- template                                  # 当作完整路径
    reg  <- if (grepl("公卫|public", path, ignore.case = TRUE)) .TPL_REG$public_health else .TPL_REG$default
  }
  if (is.na(path) || !file.exists(path)) stop("找不到模板文件: ", path)
  ppt <- read_pptx(path)
  assign("master",      layout_summary(ppt)$master[1], .ACT)   # 直接读，避免隐藏字符
  assign("cover",       reg$cover,       .ACT)
  assign("content",     reg$content,     .ACT)
  assign("blank",       reg$blank,       .ACT)
  assign("cover_style", reg$cover_style, .ACT)
  while (length(ppt) > 0) ppt <- remove_slide(ppt, 1)          # 清空自带演示页
  ppt
}
.L <- function(k) get(k, envir = .ACT)                          # 取活动模板配置

#' 封面页
sysu_add_cover <- function(ppt, title, subtitle = "", author = "", date = "") {
  ppt <- add_slide(ppt, layout = .L("cover"), master = .L("master"))
  if (identical(.L("cover_style"), "native")) {
    # 默认中大医学模板：棕榈实景照片 + 绿色色带已由版式提供；在绿带上叠白色标题文字。
    ppt <- ph_with(ppt, fpar(ftext(title, .fp(46, TRUE, "white")), fp_p = fp_par(text.align = "center")),
                   location = ph_location(left = 0.6, top = 2.42, width = 12.1, height = 1.1))
    info <- block_list(
      fpar(ftext(subtitle, .fp(23, FALSE, "white")), fp_p = fp_par(text.align = "center")),
      sp(12),
      fpar(ftext(paste0(author, "      ", date), .fp(18, FALSE, "white")), fp_p = fp_par(text.align = "center")))
    ppt <- ph_with(ppt, info, location = ph_location(left = 0.6, top = 3.78, width = 12.1, height = 1.5))
    return(ppt)
  }
  # 默认模板：绿底封面，白色大标题
  ttl <- .fp(SYSU$sz$cover_title, TRUE, "white")
  ppt <- ph_with(ppt, fpar(ftext(title, ttl), fp_p = fp_par(text.align = "center")),
                 location = ph_location(left = 0.4, top = 1.70, width = 12.5, height = 1.4))
  info <- block_list(
    fpar(ftext(subtitle, .fp(SYSU$sz$cover_sub, TRUE, SYSU$col$text)), fp_p = fp_par(text.align = "center")),
    sp(14),
    fpar(ftext("中山大学公共卫生学院", .fp(24, TRUE, SYSU$col$text)), fp_p = fp_par(text.align = "center")),
    sp(10),
    fpar(ftext(author, .fp(22, TRUE, SYSU$col$accent)), fp_p = fp_par(text.align = "center")),
    sp(8),
    fpar(ftext(date, .fp(18, FALSE, SYSU$col$gray)), fp_p = fp_par(text.align = "center"))
  )
  ppt <- ph_with(ppt, info, location = ph_location(left = 0.4, top = 4.0, width = 12.5, height = 3.2))
  ppt
}

#' 正式汇报章节分隔页（上下主色规则线 + 大号居中标题）；组会禁止调用。
sysu_add_section <- function(ppt, title, subtitle = "") {
  ppt <- add_slide(ppt, layout = .L("blank"), master = .L("master"))
  line <- strrep("─", 26)             # 实线（box-drawing）
  rule <- function() fpar(ftext(line, .fp(16, FALSE, SYSU$col$accent)), fp_p = fp_par(text.align = "center"))
  ppt <- ph_with(ppt, rule(), location = ph_location(left = 1.6, top = 2.95, width = 10.1, height = 0.4))
  ttl <- block_list(
    fpar(ftext(title, .fp(34, TRUE, SYSU$col$title)), fp_p = fp_par(text.align = "center")),
    if (nzchar(subtitle)) fpar(ftext(subtitle, .fp(18, FALSE, SYSU$col$gray)), fp_p = fp_par(text.align = "center")) else sp(2)
  )
  ppt <- ph_with(ppt, ttl, location = ph_location(left = 1.6, top = 3.4, width = 10.1, height = 1.3))
  ppt <- ph_with(ppt, rule(), location = ph_location(left = 1.6, top = 4.6, width = 10.1, height = 0.4))
  ppt <- .add_pagenum(ppt)
  ppt
}

#' 纯文字页（全宽）
sysu_add_text <- function(ppt, title, content) {
  ppt <- .new(ppt, title)
  ppt <- ph_with(ppt, content, location = G$body)
  .add_pagenum(ppt)
}

#' 双栏文字页
sysu_add_two_text <- function(ppt, title, left, right) {
  ppt <- .new(ppt, title)
  ppt <- ph_with(ppt, left,  location = G$col_l)
  ppt <- ph_with(ppt, right, location = G$col_r)
  .add_pagenum(ppt)
}

#' 左右图文页（side = "right" 图在右 / "left" 图在左）
sysu_add_text_image <- function(ppt, title, content, img, img_w, img_h,
                                side = "right", caption = NULL) {
  ppt <- .new(ppt, title)
  wh <- .fit(img, img_w, img_h); img_w <- wh[["w"]]; img_h <- wh[["h"]]  # 等比缩放
  # 把"图+题注"作为一个整体在内容区垂直居中（区间略上提，避免整体偏靠下）
  cap_extra <- if (is.null(caption)) 0 else 0.34
  img_top <- max(1.55 + (5.25 - (img_h + cap_extra)) / 2, 1.55)
  if (side == "right") {
    ppt <- ph_with(ppt, content, location = G$txt_l)
    ix <- 7.0 + (5.85 - img_w) / 2
  } else {
    ppt <- ph_with(ppt, content, location = ph_location(left = 7.0, top = 1.62, width = 5.55, height = 5.40))
    ix <- 0.85 + (5.55 - img_w) / 2
  }
  ppt <- ph_with(ppt, .external_media(img, width = img_w, height = img_h),
                 location = ph_location(left = max(ix, 0.6), top = img_top, width = img_w, height = img_h))
  if (!is.null(caption)) {
    cy <- img_top + img_h + 0.05
    ppt <- ph_with(ppt, fpar(ftext(caption, .fp(SYSU$sz$small, FALSE, SYSU$col$text)), fp_p = fp_par(text.align = "center")),
                   location = ph_location(left = max(ix, 0.6) - 0.3, top = cy, width = img_w + 0.6, height = 0.4))
  }
  .add_pagenum(ppt)
}

#' 上下图文页：上图下文 (img_pos="top") 或 上文下图 ("bottom")
#' caption：图下方"图N ……"题注（黑色小字、居中）
sysu_add_image_caption <- function(ppt, title, img, img_w, img_h, content, img_pos = "top", caption = NULL) {
  ppt <- .new(ppt, title)
  wh <- .fit(img, img_w, img_h); img_w <- wh[["w"]]; img_h <- wh[["h"]]  # 等比缩放
  if (img_pos == "top") {
    ppt <- ph_with(ppt, .external_media(img, width = img_w, height = img_h),
                   location = .center_img(img, img_w, img_h, top = 1.55))
    cap_h <- 0
    if (!is.null(caption)) {
      cap_h <- 0.34
      cleft <- (13.333 - img_w) / 2
      ppt <- ph_with(ppt, fpar(ftext(caption, .fp(SYSU$sz$small, FALSE, SYSU$col$text)), fp_p = fp_par(text.align = "center")),
                     location = ph_location(left = cleft - 0.5, top = 1.55 + img_h + 0.04, width = img_w + 1, height = 0.3))
    }
    ppt <- ph_with(ppt, content,
                   location = ph_location(left = 0.85, top = 1.55 + img_h + 0.15 + cap_h, width = 11.60,
                                          height = 7.0 - (1.55 + img_h + 0.15 + cap_h)))
  } else {
    ppt <- ph_with(ppt, content, location = G$top_box)
    ppt <- ph_with(ppt, .external_media(img, width = img_w, height = img_h),
                   location = .center_img(img, img_w, img_h, top = 2.95))
  }
  .add_pagenum(ppt)
}

#' 整图页（标题 + 居中大图 + 可选图注）
sysu_add_image <- function(ppt, title, img, img_w, img_h, caption = NULL) {
  ppt <- .new(ppt, title)
  wh <- .fit(img, img_w, img_h); img_w <- wh[["w"]]; img_h <- wh[["h"]]  # 等比缩放
  top <- if (is.null(caption)) NULL else 1.62
  ppt <- ph_with(ppt, .external_media(img, width = img_w, height = img_h),
                 location = .center_img(img, img_w, img_h, top = top))
  if (!is.null(caption)) {
    left <- (13.333 - img_w) / 2
    ppt <- ph_with(ppt, fpar(ftext(caption, .fp(SYSU$sz$small, FALSE, SYSU$col$text)), fp_p = fp_par(text.align = "center")),
                   location = ph_location(left = left - 0.5, top = 1.62 + img_h + 0.1, width = img_w + 1, height = 0.4))
  }
  .add_pagenum(ppt)
}

# 表格(含其下方 note)在内容区垂直居中起始 top；区间(1.5~6.7)略上提，避免整体偏靠下。
# extra = note 等表下附加元素的预留高度（一并纳入居中），无则 0。
.tbl_center_top <- function(ft, extra = 0, fallback = 1.85) {
  th <- tryCatch(flextable::flextable_dim(ft)$heights, error = function(e) NA_real_)
  if (is.na(th)) return(fallback)
  max((1.5 + 6.7 - (th + extra)) / 2, 1.6)
}

#' 表格页（flextable 水平居中 + 垂直居中）
#' top 默认 NULL = 按表高自动垂直居中；传数值则固定。
sysu_add_table <- function(ppt, title, ft, left = NULL, top = NULL, note = NULL) {
  ppt <- .new(ppt, title)
  fw <- sum(ft$body$colwidths)
  if (is.null(left)) left <- max((13.333 - fw) / 2, 0.5)
  if (is.null(top)) top <- .tbl_center_top(ft, extra = if (is.null(note)) 0 else 0.55)
  ppt <- ph_with(ppt, ft, location = ph_location(left = left, top = top))
  if (!is.null(note)) {
    th <- tryCatch(flextable::flextable_dim(ft)$heights, error = function(e) 2)
    note_top <- min(6.85, top + th + 0.15)
    ppt <- ph_with(ppt, fpar(ftext(note, .fp(SYSU$sz$small, FALSE, SYSU$col$gray))),
                   location = ph_location(left = left, top = note_top, width = fw, height = 0.4))
  }
  .add_pagenum(ppt)
}

#' 左文右表页（表格在右栏垂直居中）
#' top 默认 NULL = 按表高自动垂直居中；传数值则固定。
sysu_add_text_table <- function(ppt, title, content, ft, top = NULL) {
  ppt <- .new(ppt, title)
  ppt <- ph_with(ppt, content, location = G$txt_l)
  if (is.null(top)) top <- .tbl_center_top(ft)
  ppt <- ph_with(ppt, ft, location = ph_location(left = 6.95, top = top))
  .add_pagenum(ppt)
}

# ---- 卡片网格（统一淡灰底 + 主色细左条，内容垂直居中协调）----
.CARD_BG   <- "#F4F5F7"   # 统一淡灰背景（避免彩色方块）
.CARD_BD   <- "#DCDFE4"   # 细边框（浅灰）
.CARD_BAR  <- "#006D5B"   # 左侧细色条（品牌绿，唯一点缀色）
# 卡片内文本属性（中英分流，沿用宋体/Times）
.cfp <- function(size, bold, color) fp_text(font.size = size, bold = bold, color = color,
  font.family = SYSU$en, hansi.family = SYSU$cn, eastasia.family = SYSU$cn, cs.family = SYSU$en)

#' 卡片网格页。cards = list(list(tag, head, body), ...)（统一淡灰风格，color 参数已忽略）
#' @param cols 每行卡片数（默认：<=3 一行；4 用 2x2；6 用 2x3）
#' @param intro 顶部可选说明（block_list）
#' @param card_h 单卡高度（英寸）；默认按内容自适应并垂直居中。给定则固定。
sysu_add_cards <- function(ppt, title, cards, cols = NULL, intro = NULL, card_h = NULL) {
  ppt <- .new(ppt, title)
  n <- length(cards)
  if (is.null(cols)) cols <- if (n <= 3) n else if (n == 4) 2 else 3
  rows <- ceiling(n / cols)

  top0 <- 1.62
  if (!is.null(intro)) {
    ppt <- ph_with(ppt, intro, location = ph_location(left = 0.85, top = top0, width = 11.6, height = 0.95))
    top0 <- 2.70
  }
  L <- 0.85; R <- 12.48; gap <- 0.30
  cw <- (R - L - gap * (cols - 1)) / cols
  bottom <- 6.95; avail <- bottom - top0
  # 卡片取“贴合内容”的高度并紧跟 intro 顶端对齐——不强行拉满，底部留白即可。
  if (is.null(card_h)) {
    fill <- (avail - gap * (rows - 1)) / rows
    cap  <- if (rows == 1) 2.55 else 2.05      # 内容尺寸上限，避免高卡内部大片空白
    card_h <- min(fill, cap)
  }
  ytop <- top0

  for (i in seq_len(n)) {
    cd <- cards[[i]]
    r <- (i - 1) %/% cols; c <- (i - 1) %% cols
    x <- L + c * (cw + gap); y <- ytop + r * (card_h + gap)
    ft <- flextable(data.frame(x = " "))
    ft <- delete_part(ft, "header"); ft <- border_remove(ft)
    ft <- bg(ft, bg = .CARD_BG, part = "body")
    ft <- border(ft, border.top = fp_border(color = .CARD_BD, width = 0.75),
                 border.bottom = fp_border(color = .CARD_BD, width = 0.75),
                 border.right = fp_border(color = .CARD_BD, width = 0.75),
                 border.left = fp_border(color = .CARD_BAR, width = 3), part = "body")
    hd <- if (!is.null(cd$tag) && nzchar(cd$tag)) paste0(cd$tag, "  ", cd$head) else cd$head
    ft <- mk_par(ft, i = 1, j = 1, value = as_paragraph(
      as_chunk(hd, props = .cfp(SYSU$sz$h2, TRUE, SYSU$col$title)),
      as_chunk("\n", props = .cfp(7, FALSE, SYSU$col$title)),
      as_chunk(cd$body, props = .cfp(SYSU$sz$body - 1, FALSE, SYSU$col$text))))
    ft <- valign(ft, valign = "center", part = "body")     # 内容垂直居中
    ft <- line_spacing(ft, space = 1.35, part = "body")
    ft <- padding(ft, padding.top = 8, padding.bottom = 8, padding.left = 14, padding.right = 12, part = "body")
    ft <- width(ft, j = 1, width = cw); ft <- height(ft, i = 1, height = card_h, part = "body")
    ft <- hrule(ft, rule = "exact", part = "body")
    ppt <- ph_with(ppt, ft, location = ph_location(left = x, top = y, width = cw, height = card_h))
  }
  .add_pagenum(ppt)
}

#' 代码 / 示例页（等宽字体 + 浅底色框，可选上方说明文字）
sysu_add_code <- function(ppt, title, code_lines, intro = NULL) {
  ppt <- .new(ppt, title)
  top <- 1.58
  if (!is.null(intro)) {
    ppt <- ph_with(ppt, intro, location = ph_location(left = 0.85, top = top, width = 11.60, height = 1.4))
    top <- 3.0
  }
  body <- do.call(block_list, lapply(code_lines, function(l)
    fpar(cd(l), fp_p = fp_par(shading.color = SYSU$col$box, padding = 2, line_spacing = 1.1))))
  ppt <- ph_with(ppt, body, location = ph_location(left = 0.85, top = top, width = 11.60, height = 7.0 - top))
  .add_pagenum(ppt)
}

# ============================================================================
# 5. 三线表样式助手
# ============================================================================
#' 构建 SYSU 风格三线表
#' @param df data.frame
#' @param widths 各列宽度（英寸）
#' @param fsize 字号
sysu_flextable <- function(df, widths = NULL, fsize = 14, align = "left") {
  ft <- flextable(df)
  ft <- theme_booktabs(ft)
  ft <- bg(ft, part = "header", bg = SYSU$col$title)
  ft <- color(ft, part = "header", color = "white")
  ft <- bold(ft, part = "header")
  ft <- font(ft, part = "all", fontname = SYSU$cn)
  ft <- fontsize(ft, part = "all", size = fsize)
  ft <- align(ft, part = "all", align = align)
  ft <- valign(ft, part = "all", valign = "center")
  ft <- padding(ft, padding = 5, part = "all")
  ft <- bg(ft, part = "body", i = seq(2, nrow(df), by = 2), bg = "#EEF4F1")
  if (!is.null(widths)) ft <- width(ft, width = widths)
  ft <- height_all(ft, height = 0.5)
  ft
}

# ============================================================================
# 6. 保存（体裁门禁 + 强制文本框顶端对齐）
# ============================================================================
#' 组会体裁检查：禁止目录页与 sysu_add_section() 生成的章节分隔页。
.validate_meeting_deck <- function(ppt) {
  sm <- officer::pptx_summary(ppt)
  if (!nrow(sm)) return(invisible(ppt))
  sm$text <- trimws(as.character(sm$text))
  directory_titles <- c("目录", "汇报提纲", "内容提要", "agenda", "contents")
  directory_rows <- nzchar(sm$text) & tolower(sm$text) %in% directory_titles
  if (any(directory_rows)) {
    slides <- paste(sort(unique(sm$slide_id[directory_rows])), collapse = ", ")
    stop("组会 PPT 禁止目录页；检测到目录类标题，幻灯片：", slides, call. = FALSE)
  }

  section_rows <- grepl("─{4,}", sm$text)
  if (any(section_rows)) {
    slides <- paste(sort(unique(sm$slide_id[section_rows])), collapse = ", ")
    stop("组会 PPT 禁止章节分隔/过渡页；检测到 sysu_add_section() 页面，幻灯片：",
         slides, call. = FALSE)
  }
  invisible(ppt)
}

#' 保存 PPT。genre 默认 meeting；正式开题/答辩须显式传 formal。
#' 等价于 print(ppt, path)，但保存前执行体裁门禁，并把所有"空 bodyPr"文本框设为顶端对齐。
#' 仅按字节替换 ASCII 串 <a:bodyPr/>，不触碰中文(UTF-8)与已显式设置对齐的表格单元。
sysu_save <- function(ppt, path, genre = c("meeting", "formal")) {
  genre <- match.arg(genre)
  if (identical(genre, "meeting")) .validate_meeting_deck(ppt)
  path <- normalizePath(path, winslash = "/", mustWork = FALSE)
  print(ppt, path)
  td <- tempfile(); dir.create(td)
  utils::unzip(path, exdir = td)
  sld <- list.files(file.path(td, "ppt", "slides"), pattern = "slide[0-9]+\\.xml$", full.names = TRUE)
  for (fp in sld) {
    n <- file.info(fp)$size
    x <- readChar(fp, n, useBytes = TRUE)                       # 按字节读，不重编码
    x <- gsub("<a:bodyPr/>", "<a:bodyPr anchor=\"t\"/>", x, fixed = TRUE, useBytes = TRUE)
    writeChar(x, fp, eos = NULL, useBytes = TRUE)               # 按字节写回
  }
  fl <- list.files(td, recursive = TRUE, all.files = TRUE, no.. = TRUE)
  if (file.exists(path)) unlink(path)
  zip::zip(zipfile = path, files = fl, root = td)               # 重新打包为 pptx
  invisible(path)
}

# cat("SYSU Toolkit v2 loaded.\n")
