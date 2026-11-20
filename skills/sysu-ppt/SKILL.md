---
name: sysu-ppt
description: "使用中山大学官方模板制作组会、开题、中期和答辩 PPT。仅在用户明确中山大学场景或选定中大模板时使用；不用于未说明学校的通用汇报。"
---

# SYSU PPT Skill

用 R `officer` + 官方模板，代码化生成**内容清楚、版式克制、可直接上台**的学术汇报 PPT。内容深度、首张实质页思路、标题凝练、正文重点与表格选择统一遵循 [通用学术汇报流程](../academic-ppt/SKILL.md) 第 2–4 节及第 6 节；本文件负责中大模板前置条件、体裁隔离、R 骨架与硬性规范。

## 模板选择前置条件（CRITICAL）

- 只在用户已经明确中山大学场景，或经 `pptx` 确定模板来源并选择中大官方模板后执行本流程。不得把未说明学校的通用 PPT 自动套成中大模板；按 `academic-ppt` 与 `pptx` 从现有材料确定模板，未指定机构或模板时采用中性设计。
- 每个新建的中大汇报必须读取 `assets/template.pptx` 或用户明确选择的 `assets/template-公卫学院.pptx`，并通过 `source(.../sysu_toolkit.R)`、`sysu_init(...)` 和 `sysu_save(...)` 生成。绕过 `sysu_init()` 从空白画布仿制配色、校徽或水印，视为未使用模板、任务未完成。
- 用户提供其他学校、机构、会议或自定义模板时转 `pptx` 的模板编辑流程，不得改套中大模板，也不得伪造对方官方品牌。
- 写逐页故事板前记录已选模板及依据；交付前从生成脚本和渲染页同时核验模板来源。模板资产缺失或无法读取时停止生成并报告具体路径，不静默改成无模板设计。

## 体裁与结构蓝图（先认体裁再开写）

区分结果进展组会、研究拓展讨论与正式汇报，再从对应蓝本选取适用模块（蓝本是参考，不是逐页清单）：

| 体裁 | 内容参考 | 章节分隔页 | R 蓝本 |
|---|---|---|---|
| 结果进展组会 | `../academic-ppt/references/meeting-and-journal-club.md` 的结果进展分支 | **不用** | `references/deck_skeleton.R`，选用结果图表模块 |
| 研究拓展讨论 / 文献分享 / 方法讲解 | 同一参考中的对应分支 | **不用** | `references/deck_skeleton.R`，按目的选用背景、方法、比较和讨论模块 |
| 开题 / 中期 / 答辩 / 正式研究汇报 | `../academic-ppt/references/proposal-and-defense.md` 的对应分支 | 按需要使用 | `references/defense_blueprint.R` |

### 组会体裁要求（CRITICAL，违反 = 未完成）

- **组会 PPT 禁止目录页与任何章节分隔/过渡页**：不得出现“目录 / 汇报提纲 / Agenda / Contents”或只有章节名、序号的空转页；封面后直接进入第一张实质内容页，主题切换用内容页标题编号表达。首张包含具体研究问题、汇报思路与讨论目标的实质页允许生成，不能误判为目录；研究拓展仍属于组会。
- **组会生成脚本禁止调用 `sysu_add_section()`**（仅限开题、答辩、中期和正式研究汇报），且必须用 `sysu_save(ppt, path, genre = "meeting")`（默认 `meeting`，命中目录或过渡页即停止写出）。正式体裁必须显式使用 `genre = "formal"`。

## 逐页设计与模板适配

写内容前先读 [逐页设计实践](references/slide-design-practice.md)；开题/答辩同时读 `references/defense_blueprint.R` 顶部规范用词库与模块说明。

- **一页一条主信息、页数服从内容**：页数、章节与构图由用户要求、时长、内容关系和证据量决定，不得为了靠近参考规模补页，也不编造数字、图或文献。材料充分时必须写清对象、依据、做法、条件、影响或限制，不能只写标签配单行概述；材料不足以独立成页时与相邻页合并。
- **版式服从内容而非配额**：普通科研内容页默认“明确标题 + 1–3 个自然段或简单表格”，同一论证允许连续使用相同自然段版式，不要求在固定页数内更换构图，连续自然段页不因版式相同而判为问题。确有图、表、公式或代码时只保留一个视觉焦点；不做展报式左栏、眉题、徽章、KPI 面板、孤立大号数字、四宫格、渐变、厚重阴影或无语义图标。
- **设计基调与模板适配（两类通用）**：主色中大深绿 `#014924`；强调红 `#C00000` 全篇仅用于 1–2 处关键结论。官方模板只规定画布、母版、校徽或水印、字体、主色、标题与页码；模板导致文字过小、关系隐藏、比较失衡或重复卡片时必须重排或拆页，不得为套用模板牺牲科学表达与可读性。

## 工作流与模板选择

```r
Sys.setlocale("LC_ALL", "Chinese (Simplified)_China.utf8")
skill_roots <- path.expand(c(
  Sys.getenv("EPIAGENTKIT_SKILLS"), Sys.getenv("EPICLAUDE_SKILLS"),
  "~/.claude/skills", "~/.agents/skills", "~/.codex/skills",
  "~/.gemini/config/skills"
))
skill_dirs <- file.path(skill_roots[nzchar(skill_roots)], "sysu-ppt")
SKILL <- skill_dirs[dir.exists(skill_dirs)][1]
if (!length(SKILL) || is.na(SKILL)) stop("找不到 sysu-ppt；请设置 EPIAGENTKIT_SKILLS")
source(file.path(SKILL, "scripts", "sysu_toolkit.R"))

ppt <- sysu_init("default")          # 默认=中大医学版；公卫模板可用 sysu_init("模板2") 或 .pptx 路径
ppt <- sysu_add_cover(ppt, "主标题", "English Subtitle", "汇报人：姓名", "2026 组会")
ppt <- sysu_add_text(ppt, "研究问题与汇报思路", block_list(
  prose(tx("围绕已确认的研究问题，"), bd("提炼本次汇报目标"), tx("，并写明分析范围。")),
  prose(tx("说明已有证据、结果或候选方案的展开顺序，以及"), bd("需要讨论或确认的具体事项"), tx("。"))))
# ……更多内容页（函数速查见 references/toolkit-and-verification.md）……
sysu_save(ppt, "输出.pptx", genre = "meeting")  # 组会强制禁目录/过渡页；正式汇报传 genre = "formal"
```

- **未指明 / 模板1 / medical** → `sysu_init("default")` = `assets/template.pptx`（中大医学棕榈实景封面 + 校徽 + 城市水印）。
- **用户说“模板2/模板二/公卫”** → `sysu_init("模板2")` = `assets/template-公卫学院.pptx`（公卫学院绿色封面 + 标题绿竖条）。两套模板内容页 API 完全一致。

## 硬性规范（每次必须满足）

1. **字体与字号**：中文宋体、英文 Times New Roman，同段自动分流（`.fp()` 内置，无需手动切；slide XML 层已校验 `<a:ea>=宋体`、`<a:latin>=Times New Roman`）。标题默认 24pt；正文 16pt 只作为信息密集页的下限，常规使用 18–20pt，最终以 1280×720 导出图验收。
2. **内容驱动与防溢出**：也不把“每页有图”当目标。同一解释可按语义延续到下一页，不强拆卡片或箭头链。officer 文本框不自动缩字：左右图文/左文右表左栏最多 5 块、约 12 行/230 中文字，纯文字全宽页最多 7 块/340 字（防溢出上限，非填充目标）；超出时删次要句或拆页，绝不缩字号，并逐页检查不压页眉、页脚或页码。
3. **编号与章节隔离**：最多两级且编号只在内容页标题；同主题确有多页时才用 `1.1 / 1.2`，正文不写 `1.1.1`。章节分隔页严格按体裁隔离（组会禁用 `sysu_add_section()`）。
4. **强调、取数与符号**：故事板选定的正文重点用 `prose(tx(...), bd(...), tx(...))` 强调，表格重点用 `flextable::bold()` 定向加粗关键行或单元格。有 `results/results.yaml` 时一律按固定名称取数（旧项目可读旧版结果文件），禁止手填关键数字。编号（`num_item`）与圆点（`bullet`）二选一，不叠加。
5. **学术书面、不口语（每页都查）**：段落小标签用规范词（解决问题 / 指标计算 / 检验 / 局限性 / 定义 / 说明 / 注意事项 / 方法 / 重要性），禁用“一句话 / 坑 / 怎么读 / 怎么办 / 通俗讲 / 回答”；删空话敷衍句；不写逐页免责句和解释性脚注（页脚只放来源，比较组平行命名）；网络口语（净赚、一验就掉、学过头、乱筛、虚高等）改为规范书面语。
6. **当前版单一、旧版整组归档**：当前目录仅保留稳定命名的 `.pptx`、当前脚本与必要素材，不留“完善版 / 最终版 / v2 / final”。重生成前把旧版整组移入 `09_backup/archive/YYYY-MM-DD_HHMM_<汇报主题>_<阶段>/`，写 `MANIFEST.md` 并登记 `09_backup/INDEX.md`。

## 工具接口、配图与视觉验收（按需必读）

编写脚本、设计卡片/配图及交付前验收必须读取 [工具接口、配图与视觉验收](references/toolkit-and-verification.md)：

- **API 与卡片边界**：按其中的 API 速查与文本/表格助手调用 `sysu_toolkit.R`；卡片默认不用，仅限 2–4 个真正并列的短对象。
- **配图规则**：确需非统计流程、框架、机制或技术路线时先读 `../research-visuals/references/research-figure-patterns.md` 并走 `research-visuals` → `imagegen`（仅在工具不可用或强制矢量时转 `svg-diagrams`），统计图走 `publication-figures`。图内不写标题与解释句、字号够大、无多余留白、题注置于图下；imagegen 最多定向修改两轮，不用 PPT 文本框或 SVG 覆盖补字。
- **生成后必跑自检**：用 PowerPoint COM 导出 1280×720 逐页 PNG（只关闭本次自动化创建的实例，不用 `Stop-Process`），逐项核对 `references/toolkit-and-verification.md` 中的 ⓪–⑯ 与归档检查；模板页眉几何对齐与常见布局问题见同文件末节。

## 参考文件

- `references/toolkit-and-verification.md` — API 速查、卡片约束、配图规范、16 项逐页自检与模板几何问题。
- `references/slide-design-practice.md` — 逐页设计说明、版式映射、视觉节奏、文字密度与配图准确性规范。
- `references/deck_skeleton.R` — 组会可选页面与版式示例（无章节页）。
- `references/defense_blueprint.R` — 开题/答辩/正式研究汇报的参考模块、规范用词库与设计基调。
- `references/figure_snippets.R` — 统计图配图示例。
- `../research-visuals/references/research-figure-patterns.md` — 通用科研流程图、框架图、机制图与技术路线规范。
- `scripts/sysu_toolkit.R` / `scripts/example_ppt.R` — 核心工具库与 API 渲染测试脚本。
- `assets/template.pptx`（默认中大医学）、`assets/template-公卫学院.pptx`（模板2）— 两套官方模板。
