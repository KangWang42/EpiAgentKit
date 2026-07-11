---
name: epi-project-audit
description: |
  全局流行病学与生物统计项目审查 skill。把项目审查变成带门禁的 TODO 状态机：六层审查逐项过检 → 失败自动给修复建议 → 全过才能签发。
  触发场景：用户说"检查项目"、"质控"、"复核结果"、"审稿前自查"、"统一框架"、"检查命名/代码/结果/论文一致性"、"全面查一下"。
  上游依赖：biostat-principles（审查尺度）+ consulting-delivery（如果项目含咨询交付包）。
---

# Epi Project Audit（带门禁的 6 层审查）

> **审查本质**：证据链核对。不只看代码、不只看结果；看的是"数据 → 代码 → 结果 → 表图 → 正文"这条链是否首尾一致。
> **工作模式**：六层逐项过 TODO → 每层有硬门禁 → 不通过不进入下一层 → 全过才发 **pass**。

---

## 一、开工前准备

### 1.1 读项目规则（顺序优先）

按以下顺序读取，先服从项目级规则，再执行本 skill：

1. 项目内 `CLAUDE.md` / `AGENTS.md`
2. `README.md`（项目说明）
3. `PROTOCOL.md` / `SAP.md`（预设研究问题、分析与偏离边界）
4. `DECISIONS.md`（方法决策与方案偏离历史）
5. `SESSION_LOG.md`（操作日志）
6. `07_paper/results.yaml`（结果机器单源）+ 派生 `0_result_summaries.md`

**缺失关键文件就已经是扣分项**，要写入"Problems found"。

### 1.2 问用户（强制）

如果用户只说"检查一下"没指定范围，**必须先问**：

```
【澄清】本次审查的范围：
  [A] 全量审查（推荐，涵盖 6 层）
  [B] 只审代码可运行性
  [C] 只审结果一致性
  [D] 只审论文 / 交付物
  [E] 只审某个具体目录或文件
  
默认 A。请确认或指定。
```

用户模糊回答 → 默认 [A]。

---

## 二、6 层审查状态机（每层带门禁）

```
[START]
  ↓
[Layer 1: 项目骨架]      ——门禁：目录结构、命名、日志完整
  ↓ 不过 → 记录问题 + 给修复建议 + 继续（不中断）
[Layer 2: 数据链]         ——门禁：原始只读、派生可追溯、缺失有交代
  ↓
[Layer 3: 代码质量]       ——门禁：可运行、无 error、脚本编号
  ↓
[Layer 4: 结果一致性]    ——门禁：表图/摘要/正文数字完全一致
  ↓
[Layer 5: 科学合理性]    ——门禁：方法适配、结论不超证据
  ↓
[Layer 6: 交付一致性]    ——门禁：README/日志/决策/分享包同步
  ↓
[VERDICT]  pass / pass with concerns / fail
```

**每层的判定**：

- **绿（pass）**：全部 TODO 通过
- **黄（concerns）**：有非阻塞问题，已写入报告
- **红（fail）**：有证据链断裂、数字不一致、结论无支撑 → **必须修复后重审**，不可签发

---

## 三、Layer 1 · 项目骨架审查

### TODO 清单

- [ ] 目录结构符合七层规范（01_data / 02_code / 03_tables / 04_figures / 05_reports / 06_results / 07_paper / 09_backup）
- [ ] `01_data/rawdata/` 存在且最近无修改时间变动
- [ ] `02_code/` 内脚本**全部**按 `NN_描述.R` 编号且连续无断号；无 `test.R`、`final.R`、`temp.R`
- [ ] `02_code/` 编号脚本数 ≤ 10（config / conventions / lib / run_pipeline 与 vendored/ 不计）；探索 / 一次性脚本不在 `02_code/`（应在 `09_backup/`）
- [ ] `03_tables/` / `04_figures/` 编号按论文行文顺序连续无断号；`TableS{N}` / `FigS{N}` 在 `supplementary/`；无 `Table_xxx` / `Fig_xxx` 无编号残留；交付 xlsx 内无 cover / 说明类解说性 sheet
- [ ] 根目录无散落临时文件（`.csv`、`.xlsx`、`.png` 不在根）
- [ ] `CLAUDE.md` / `PROTOCOL.md` / `SAP.md` / `SESSION_LOG.md` / `DECISIONS.md` 存在；入口规则文件不超过 200 行
- [ ] `09_backup/EXPERIMENTS.md` 登记全部探索尝试；每个已运行实验有 `PLAN.md` 与 `FINDINGS.md`
- [ ] `09_backup/` 存在；旧版文件已归档，不在活跃目录
- [ ] 没有多个互相冲突的"最终版"（比如 `final/` + `最终版/` + `提交版/`）

### 红线（任一触发 → Layer 1 判 fail）

- 根目录存在 > 3 个散落非规范文件
- `02_code/` 存在无编号脚本
- 原始数据被修改（文件 mtime 晚于项目开始日期）
- `09_backup/` 和活跃目录共存同名文件但内容不同

### 自动修复动作

能客观修复的直接修（并记录）：
- 把 `test.R`、`temp.R` 移入 `09_backup/` + 改名 `NN_backup_原名.R`
- 把散落的 `.csv` / `.png` 移入对应目录
- 补建缺失的 `SESSION_LOG.md`（用模板）

不自己动手的（要写入"Problems found"）：
- 覆盖冲突的多版本（让用户决定保留哪版）
- 删除"看似无用"的文件（除非用户明示）

---

## 四、Layer 2 · 数据链审查

### TODO 清单

- [ ] `01_data/rawdata/` 下每个文件都有对应的数据字典（README 或单独 md）
- [ ] 原始数据只读（检查是否有脚本 `write` 回 `01_data/rawdata/` → 违规）
- [ ] 派生数据全部在 `06_results/` 或结果包 `data/`
- [ ] 每个派生数据能追溯到生成脚本（用 git grep / 搜索引用）
- [ ] 关键变量在字典里有定义、单位、来源说明
- [ ] 缺失数据有处理记录（删？插补？在哪个脚本？哪个决策）
- [ ] 样本量从原始 → 清洗 → 分析，每一步的损失数量可追溯（CONSORT / STROBE 流程）

### 红线

- 发现脚本修改了 `01_data/rawdata/` 的文件
- 存在无法追溯来源的派生数据
- 样本量链断裂（原始 1000 → 分析 500，但中间去了谁没说）

---

## 五、Layer 3 · 代码质量审查

### TODO 清单

- [ ] **真实跑一遍**：`Rscript 02_code/NN_xxx.R` 逐个执行（或至少主分析）
- [ ] 无 error，warning 已理解且合理
- [ ] 脚本顶部有 `library()` 完整清单 + `set.seed()`
- [ ] 用相对路径（grep `setwd`、grep `"C:/"`、grep `/Users/`）
- [ ] 无 `for` 循环的数据处理（有也能说明必要性）
- [ ] 无 `print()` / `cat()` 作为调试残留
- [ ] 无 TSV 输出（grep `write\.tsv`、`write_tsv`）
- [ ] 脚本之间靠 `06_results/` 落盘传值，不靠环境变量；表格化中间数据是 xlsx（rds 仅限模型等非表格对象）
- [ ] 无写死的 `Table\d` / `Fig\d` 输出路径（grep `Table[0-9]|Fig[0-9]`；产出路径应经 `config.R` 的 `table_path()` / `fig_path()` 取，registry 见 project-init）
- [ ] 结果包（`05_reports/*/`）内脚本不回读项目根（grep `\.\./`）

### 红线

- 任何 R 脚本报 error
- `01_data/rawdata/` 被脚本写入
- 绝对路径出现（移植性破坏）
- 结果包内脚本依赖包外文件

### 自动修复动作

- `print()` 残留 → 删除
- `setwd()` 绝对路径 → 改 `here::i_am()` 或 `Rproj` 提示
- 散落 TSV → 转 CSV 或合入 XLSX

---

## 六、Layer 4 · 结果一致性审查（最关键）

**这是一切审查的核心：数字必须从"数据源 → 脚本产物 → 表 → 图 → 摘要 → 正文"一致到底。**

### 先跑自动审计（结果单一真源项目）

若项目已用结果单一真源（`07_paper/results.yaml`，见 r-biostats `result-summary-schema.md`），**先跑**：

```bash
python <此skill>/scripts/check_consistency.py <项目根>
```

它双向比对交付文档（论文/报告/PPT）里的 CI、P 与 results.yaml：方向A 报"文中统计量在源中无匹配"（疑似手敲/陈旧/未回写），方向B 报"源有文档未用"，并列出 `interp_review` 的"解读待复核"键。退出码非 0 = Layer 4 未过门禁。脚本是初筛，下方人工矩阵仍需补图内/精度等它覆盖不到的项。

### TODO 清单

- [ ] 从 `0_result_summaries.md` 取出**每一个关键数字**（样本量、主效应、P 值、95%CI、事件数）
- [ ] 每个数字能在 `03_tables/` 的某张表里找到（完全相等）
- [ ] 每个数字能在 `04_figures/` 对应图的风险表/脚注/图例里找到
- [ ] 每个数字能在 `07_paper/` 的正文 / 摘要 / 讨论结论里找到
- [ ] 数字精度全文统一（不能一处 0.45，一处 0.4453）
- [ ] 亚组分析和主分析的样本量能对得上
- [ ] 敏感性分析方向与主分析一致（如果不一致要有讨论）

### 红线

- 正文某个数字在 `0_result_summaries.md` 找不到 → **fail**
- 摘要的 HR 与结果表的 HR 不一致 → **fail**
- 图上的 N 和基线表的 N 不一致 → **fail**
- 讨论结论引用的数字在表里不存在 → **fail**

### 强制输出

Layer 4 审查必须输出一张**数字一致性矩阵**：

| 关键数字 | 0_result_summaries.md | 03_tables/ | 04_figures/ | 07_paper/ | 一致？ |
|---------|---------------------|-----------|-----------|-----------|--------|
| 样本量 N | 1234 | Table1: 1234 | Fig1 risk table: 1234 | 摘要: 1234 | 一致 |
| 主 HR | 1.45 | Table3: 1.45 | Fig2 forest: 1.45 | 摘要/讨论: 1.45 | 一致 |
| P 值 | 0.004 | Table3: 0.004 | — | 摘要: 0.004 | 一致 |

任何一行不一致 → Layer 4 fail。

---

## 七、Layer 5 · 科学合理性审查

### TODO 清单

- [ ] 研究设计（队列/病例对照/横断面/RCT/Meta）明确
- [ ] 主终点、分析人群和主要模型与冻结的 PROTOCOL/SAP 一致；偏离均在 `DECISIONS.md` 有时间、原因和确认记录
- [ ] 主分析方法匹配研究设计（比如队列用 Cox 或 Poisson，不要用逻辑回归无视时间）
- [ ] 纳排标准前后一致（方法节说的排除标准，和 CONSORT 流程图一致）
- [ ] 样本量足够支撑分析（事件数 ≥ 10×协变量数 for Cox）
- [ ] 模型诊断做了（PH 假设、线性假设、多重共线、异常值）
- [ ] 敏感性分析覆盖了主要的口径假设
- [ ] 探索实验完整登记而非只保留“最佳”结果；主线采用项达到预设晋级标准，未采用项未混入主 `results.yaml`
- [ ] 有 STROBE / CONSORT / PRISMA / AMSTAR 等对应报告规范遵循

### 红线

- 方法学严重错配（比如 RCT 分析忽略了随机分层）
- 主要分析在看过结果后变更，却未记录为 SAP 偏离或探索性分析
- 只报告成功尝试、无法还原全部方法搜索过程，或未过门禁的探索结果被写成主要结论
- 事件数 < 10×协变量，过拟合风险高但未披露
- 缺关键假设检验却未说明

### 结论强度标定（核心）

扫描讨论和摘要，检查以下"过强措辞"：

| 原文 | 问题 | 改为 |
|------|------|------|
| "证实" / "证明" | 观察性研究无法"证实" | "支持" / "提示" |
| "明确说明" | 过强 | "方向一致" |
| "稳固的保护作用" | 过强 + 情感词 | "保护方向" |
| "可以得出结论" | 过强 | "结果提示" |
| "显著降低风险" | 混淆统计显著和临床意义 | "与较低风险相关" |
| "具有因果意义" | 观察性证据不支持 | "存在关联" |

全文逐条列出超纲措辞的位置 + 建议替换。

---

## 八、Layer 6 · 交付一致性审查

### TODO 清单

- [ ] `README.md` 与实际目录一致
- [ ] `SESSION_LOG.md` 的最后一条时间 ≥ 最近一次代码修改时间
- [ ] `DECISIONS.md` 覆盖所有方法选择（grep 方法名 vs `DECISIONS.md`）
- [ ] `05_reports/` 的分享包能独立运行（可随机抽一个实测）
- [ ] 分享包的 `00_写作说明.md` / `01_方法与结果.docx` 与包内代码和表一致
- [ ] 分享包如果面向客户 → 过 `consulting-delivery` 的 FINAL 终检清单（§八）
- [ ] 旧版、废弃版本全部在 `09_backup/`

### 红线

- 分享包无法独立运行（依赖外部文件）
- docx 结论与包内 tables 数字不一致
- 未披露的敏感性分析或亚组分析在正文提及

---

## 九、如何使用 references/

- 完整逐项审查表 → [references/audit-checklist.md](references/audit-checklist.md)
- 结论措辞标定表 → [references/claim-calibration.md](references/claim-calibration.md)

两份文件是本 skill 的展开，逐项对照使用。

---

## 十、输出合约（OUTPUT CONTRACT）

审查结束后**必须**用以下结构输出：

```markdown
## Audit verdict

- Status: pass / pass with concerns / fail
- Scope: [审查范围，哪些层]
- Date: YYYY-MM-DD
- Reviewer: Agent (`epi-project-audit` skill)

## Layer-by-layer results

| Layer | 内容 | 结果 | 主要问题 |
|-------|------|------|---------|
| 1. 项目骨架 | 目录/命名/日志 | pass / concern / fail | ... |
| 2. 数据链 | 原始只读/派生可追溯 | pass / concern / fail | ... |
| 3. 代码质量 | 可运行/规范/路径 | pass / concern / fail | ... |
| 4. 结果一致性 | 数字全链一致 | pass / concern / fail | ... |
| 5. 科学合理性 | 方法/结论标定 | pass / concern / fail | ... |
| 6. 交付一致性 | 日志/决策/分享包 | pass / concern / fail | ... |

## Numbers consistency matrix

[Layer 4 产出的表格完整粘贴]

## What is correct

- [已验证正确的点，说服力最强的结论]

## Problems found（按严重度排序）

### Critical（必须修复）
- [证据链断裂、数字不一致等 fail 级问题]

### Warning（建议修复）
- [命名不规范、注释不足等 concerns]

### Fixed in this audit
- [本次审查直接客观修复的小问题]

> 审查中发现"非阻塞但该补"的项（缺某项数据、某分析能强化但没做、某文献待补、下一步建议），除写进本报告外，**同时追加到项目根 `BACKLOG.md` 主表**（待完善内容+完善方式 AI/人工+重要性 必补/建议/可选+状态，见全局 CLAUDE.md §2），避免报告读完就忘；红色 Critical 不进 BACKLOG，必须修复后重审。

## Scientific judgment

[结论是否与证据强度匹配？哪些措辞超纲？]

## Sign-off

- [ ] 本项目/结果 **可以/不可以** 直接用于投稿/汇报/交付
- [ ] 修复以下 N 处 Critical 问题后重审
- [ ] 附带说明：[关键注意事项]
```

---

## 十一、修复权限边界

### 可以自己直接修（修了就写在 Fixed 里）

- 文件命名不规范（重命名）
- 散落临时文件（移入对应目录）
- 打印调试残留（删除）
- 相对路径问题（改相对）
- `SESSION_LOG.md` 缺失本次操作（补写）
- 结果包内对项目根的回读（改为自包含）

### 必须问用户再改

- 涉及方法选择（改模型）
- 删除看似废弃的结果（可能是用户保留的）
- 合并多版本（保留哪版不确定）
- 结论措辞（用户才是作者）
- 数据脱敏（哪些字段敏感不确定）

**不属于这两类的 → 写入 Problems found 让用户决定**。

---

## 十二、审查频率建议

| 时机 | 建议审查范围 |
|------|------------|
| 每次完成一个主分析 | Layer 3 + Layer 4 |
| 提交给导师 / 合作方 | 全量 6 层 |
| 投稿前 | 全量 + 特别关注 Layer 5（结论标定） |
| 咨询交付前 | 全量 + 过 `consulting-delivery` 终检 |
| 项目归档前 | Layer 1（清理）+ Layer 6（一致性） |
