# EpiClaude 全局规则

R / Python 流行病学项目的硬红线。详细领域规范在各 skill；本文件只放每个 session 都需要的跨任务规则。

> 维护原则：每条规则过"删除测试"——删了 Claude 会犯具体可观察的错误才保留。目标 < 120 行；多步程序性内容一律下沉 skill，本文件只留规则与指针。

## Approach

- 写作以"我做了 X"研究者视角，不用"建议把…"或 AI 助手口吻。
- 交付文本（论文 / 汇报 / PPT / 报告）一律学术书面语：不用口语或网络词；标题用名词短语、不用反问；英文缩写首次出现给全称（如 AUC（Area Under the Curve））。
- 疑点 / 不一致 / 多个合理口径并存 → 先问用户再做，不擅自决定。
- **交付前强制自检（不等用户挑错）**：完成任何产物先按对应 skill 清单以"真实发表 / 交付标准"自查（论文走 academic-publishing 的 section-content-playbook + chinese-anti-ai + review-killers）。发现一类问题立刻全文 grep 扫同类，一次清干净再交付；交付时先报告"已自检项"。把明显问题留给用户发现 = 任务未完成。
- 简洁输出；不堆开场闭场套话；不用 emoji / emdash。
- 不猜 API / 版本 / 包名；读代码或文档后再断言。

## 1. 路由（自动义务，不等用户点名）

| 触发场景 | 必须调用 |
|---|---|
| 新建项目 / 初始化 | `/project-init` |
| 任意 R/Python 统计分析、回归、生存分析、清洗 | `/r-biostats` |
| **任意出图（ggplot / matplotlib / 论文图件）** | **`/publication-figures`** |
| 写/改论文任一部件（中/英）、投稿材料、排版 docx | `/academic-publishing` |
| 去 AI 味 / 润色 / 文风更像人 | `/humanizer-zh` |
| 给客户做 / 咨询交付 / 打包结果 | `/consulting-delivery` |
| 项目审查 / 复核结果 / 检查一致性 | `/epi-project-audit` |
| 试新方法 / 优化模型 / 上前沿技术 | `/biostat-principles` 探索工作流 |
| 任何 r-biostats / academic-publishing / consulting-delivery 任务开工前 | `/biostat-principles` |

任务落入上表 → 第一步就调用对应 skill 并按其规范执行，无需用户点名；漏调用 = 任务未完成。写论文部件不得凭印象自由写作，必须按 academic-publishing 的 references（section-content-playbook / chinese-paper / chinese-anti-ai / review-killers）执行。

## 2. CRITICAL 硬红线（违反 = 任务未完成）

### 数据与路径
- **NEVER** 修改 `01_data/rawdata/` 原始数据。
- **NEVER** 用绝对路径；一律相对。
- **NEVER** 在项目根放临时 / 测试 / 零散结果。
- **NEVER** 在 `02_code/` 新增 `run_all.R` / `main.R` / `一键复现.R` AI 式入口（交付包内的 `run_all.R` 是 /consulting-delivery 的规定动作，不在此列）。

### 02_code 编号
- **NEVER** 留无编号脚本（`test.R` / `final.R` / `temp.R`）；**NEVER** 编号断层，归档/增删后立刻重排 01..0N 连续。
- **NEVER** 把一次性脚本（一次绘图 / 临时诊断 / 迁移）留 `02_code/`；写完归 `09_backup/<日期>_scripts_oneoff/`。退役 / 被替代脚本同样立即移 `09_backup/`。
- `02_code/` 只放"从原始数据复现到论文最终结果"的脚本；**编号脚本数 ≤ 10**（config / conventions / lib / run_pipeline 与 vendored/ 不计）。1 个编号脚本 = 论文 1 个阶段，阶段内子分析用 `--step` / `--outcome` 参数切分；超 10 个就是没合够，立即按阶段归并。

### 03_tables / 04_figures
- 主表 `Table{N}_{描述}.xlsx`、附表 `TableS{N}_...`；主图 `Fig{N}_{描述}.{png,pdf}`、附图 `FigS{N}_...`；N **按论文行文顺序连续**；附表附图一律放 `supplementary/`。
- **编号唯一来源 = registry 有序清单**（编号 = 清单中的位置）：产出脚本一律 `table_path(stem)` / `fig_path(stem,ext)` 取路径，**NEVER 在脚本里写死 `Table6` / `Fig3` 数字**；增删 / 改序 / 退役只改这一个清单，后续号自动前移补齐，永不断号。实现细节见 `/project-init` 的 `references/registry.md`；新项目初始化时即建空 registry。
- **NEVER** 长期保留无编号文件（`Table_xxx` / `Fig_xxx`）；**NEVER** 同主题留多版本（旧版进 `09_backup/`）；**NEVER** 导出 `.tsv`。
- **一个主题/一张论文表 = 一个 xlsx**；多切面（双 outcome / 多模型 / 亚组）放同一 xlsx 多 sheet，sheet 名即论文小表名。**NEVER** 在交付 xlsx 放 cover / 说明 / 数据字典等解说性 sheet（方法说明写进论文正文）。
- 主目录只放进论文的主流程表图；敏感性 / 消融 / 探索 / 审计产物：并进主表附加 sheet、进二级子文件夹（如 `03_tables/supplementary/`、`04_figures/ablation/`），或移 `09_backup/`。
- **归位 = 改生成脚本的输出路径，不是只 mv 文件**；挪完必须 grep 生成脚本确认输出路径已改（"散落主目录"反复发生的根因）。

### 结果与方法
- **NEVER** 把中间结果 / 调参痕迹当最终交付。
- **NEVER** 结果变了不同步 `07_paper/0_result_summaries.md`（论文唯一数据源）；方法变了不同步 `DECISIONS.md`。
- **NEVER** 写完代码不跑就宣称完成（`Rscript` / `python` 实跑验证）。
- **NEVER** 把口径常量（有序因子序 / P 值格式 / 表组成 / 配色 / 字体 / registry）散落各脚本；集中 `config.R` + `conventions.R` 单一真源，改一处全同步。
- **NEVER** 只改分享包（`05_reports/<包>`）而不回写主流程源 + `conventions.R`（分享包 = 主流程派生导出）；确需脱离主流程的定制版在包内 `00_说明.md` 与 `DECISIONS.md` 注明"未回写"。详见 `/consulting-delivery`。
- 中间表格化数据存 xlsx；仅跨脚本传**非表格 R 对象**（拟合模型 / MCA / ggplot 对象）才用 `.RData`；交付物（05_reports）零 rds/RData。`06_results/` 按内容命名不编号。

### 报错与 warning（不可放任）
- **NEVER** 把 error / warning / NaN / 缺数当"正常率 / 比例小"带过（如"256/257 仅 1 个失败"）；每一个都定位具体原因：数据本身缺、脚本 bug、上游 stale、还是阈值过严。
- **NEVER** 只看 tail 几行就声明成功；必须 `grep -iE "error|warning|traceback|failed|nan"` 全量扫 output，逐条解释。
- 每个报错/warning 三选一去向：(a) 代码 bug → 修复重跑；(b) 数据问题 → `DECISIONS.md` 记"已知豁免"+原因+影响范围；(c) 库噪声 → `SESSION_LOG.md` 记"经核实可忽略+证据"。**不允许沉默放过**。

### 口径与表达
- 分组 / 终点 / 纳排 / 主分析方法定义不明 → **先问用户**，不猜。
- **NEVER** 在论文 / 汇报暴露内部变量名 / 版本号 / 调参过程 / 程序实现。
- **NEVER** 在任何工作产物（md / 表图 / 代码 / README / 交付包 / 论文 / csv/xlsx 列值）出现 emoji 或 AI 工作痕迹（AI编码 / AI_assisted / AI辅助 / 机辅 / assistant 等），也 **NEVER** 出现"待人工复核 / 机辅待核"等暗示编码非人工或未完成的措辞。质性编码一律表述为研究者本人完成的可靠人工编码（coder="研究者"、review_status="已复核"/"完成"）；状态文字用"完成/待做"；真实过程只记 DECISIONS / SESSION_LOG 内部审计。
- **NEVER** 把探索性峰值 / 网格点 / 调参标签写成临床结论；无依据的"更好/最佳/证明"删掉。

## 3. 目录骨架与工作流指针

```
01_data/rawdata/   只读原始数据
02_code/           NN_描述.{R,py} 连续编号 + config.R / conventions.R
03_tables/         Table{N}_..xlsx（附表进 supplementary/）
04_figures/        Fig{N}_..{png,pdf}（附图进 supplementary/）
05_reports/        可分享结果包（/consulting-delivery）
06_results/        中间对象，按内容命名不编号
07_paper/          论文文稿 + 0_result_summaries.md（唯一数据源）
09_backup/         旧版 / 一次性脚本 / 探索实验
CLAUDE.md / SESSION_LOG.md / DECISIONS.md
```

- **试新方法 / 优化模型**：**NEVER** 直接改主流程脚本。按 `/biostat-principles` 探索工作流执行：`09_backup/<日期>_<主题>/` 隔离实验 → 与主流程同口径公平对照 → `FINDINGS.md` 记结论 → 确有稳健提升且过口径门禁才合并。探索脚本永不留 `02_code/`。
- **git 阶段性备份**：项目的重要尝试、口径变更、阶段性成果用 `git commit` + `git push` 备份到远端，**按里程碑阶段提交，不是每改一处都提交**（例如：完成一个主分析、合并一次探索结果、定稿一个论文部件后各提交一次）。push 仅为保全代码与可回溯，**不做正式 release / 对外发布**；远端仓库默认私有，除非用户明确要求公开。提交信息写清这一阶段做了什么。

### 完成前自检清单
- [ ] 所有编号序列连续无断号（code / tables / figures / data 及分享包同名目录）；增删后立即重排 01..N，含改脚本输出路径与正文引用
- [ ] 表格化中间数据存 xlsx；交付物零 rds/RData
- [ ] 有序分类变量表行序 / 图轴序符合 `conventions.R::ORDERED_LEVELS`，脚本未手写 level 向量（一律 `lv()` 取）
- [ ] 图件满足 `/publication-figures` 规范（mm 尺寸 / PDF+PNG 双存 / 字体嵌入）
- [ ] 代码已实跑验证 + 全量扫 error/warning
- [ ] 论文 / 交付文本已按 `/academic-publishing` 与 `/humanizer-zh` 清单自检
- [ ] 方法变 → `DECISIONS.md`；结果变 → `0_result_summaries.md`；操作完 → `SESSION_LOG.md`
- [ ] 一次性脚本与旧版文件已归 `09_backup/`

## 4. 规则优先级（冲突时）

1. 用户当轮明确指示
2. 本文件 CRITICAL 硬红线（§2）
3. 项目级 `CLAUDE.md` 项目特定规则
4. 已加载 skill 的执行流程
5. skill 内 DEFAULT / PREFERENCE / EXAMPLE

涉及分组 / 终点 / 纳排 / 主分析方法 → 任何层级都先问用户，不擅自选。

## 5. 记忆锚点（删了会犯错的 5 条）

1. **02_code 编号连续 + 一次性脚本归档** → 否则脚本堆积失序。
2. **Table/Fig 按论文行文编号，registry 单源** → 否则正文引用全错。
3. **结果变同步 0_result_summaries.md，方法变同步 DECISIONS.md，操作完同步 SESSION_LOG.md** → 否则数字源失锁。
4. **代码写完必跑 + 全量扫 error/warning** → 否则交付带未验证错误。
5. **口径不明先问用户** → 否则分析方向偏离用户意图。
