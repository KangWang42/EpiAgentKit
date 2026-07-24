---
name: consulting-delivery
description: |
  把已完成并验证的 R 或 Python 分析打包为客户可独立复现、可直接阅读且保留真实溯源的咨询交付物。用于“给客户交付”“打包结果”或在 05_reports/ 建正式结果包；不用于未完成分析或内部探索。上游为 biostat-principles，文本终审配合 academic-humanizer，签发配合 epi-project-audit。
---

# 咨询交付包标准 skill

> **目标**：客户拿到一个 zip → 不问任何问题 → 运行 `run_all.R` 或 `run_all.py` → 重现全部结果 → 打开 `01_方法与结果.docx` 直接阅读。

**不触发的情况**：自己研究用的中间产物、实验性脚本、不打算外发的结果。

---

## 一、分享包与主流程的关系（防漂移，CRITICAL）

分享包按来源分三类，处理方式不同：

| 类型 | 含义 | 真源在哪 | 做法 |
|---|---|---|---|
| (a) 主流程搬运 | 把主流程已有结果/论文打包外发 | **主流程** | 分享包是主流程的**导出快照**，零手改；要改内容先改主流程再重导出 |
| (b) 补充结果 | 主流程没有、为这次分享新做的分析 | 分享包或主流程 | 若进论文/长期用 → 写成主流程编号脚本；纯一次性 → `09_backup/` |
| (c) 尝试/探索 | 试新方法 | `09_backup/<日期>_*/` | 验证有效才合并进主流程（biostat-principles §7）；从不直接进分享 |

**核心原则：单一真源，分享包是派生物不是手改终点。**

- **口径常量集中一处**：有序水平、P 值格式、表组成、配色、字体和 registry 放入所选语言的 `02_code/conventions.*` 与 `config.*`。主流程与导出脚本共用该单源。
- **分享包由导出脚本生成**：写与主流程同语言的 `02_code/NN_export_<topic>.*` 或正式项目归档区的一次性脚本，自动建目录、复制数据/表/图、清理意外调试痕迹并生成文档。要改内容先改主流程源再重导出。
- **冻结部分例外**：已发表/冻结的产物不套用新口径，在 DECISIONS 记为豁免。
- **防漂移两条硬规则**：① 分享包 `00_说明.md` 记一行"由 `<脚本>` 于 `<日期>` 从主流程导出"；② 用户在分享包里提的修改意见**必须回写主流程源 + 所选语言的 conventions 文件**，不能只改分享包。
- **若确实只想改分享、不动主流程**：在该包 `00_说明.md` 注明"脱离主流程的定制版，未回写"，并记 DECISIONS.md。

---

## 二、交付包状态机

```
[R 或 Python 分析已完成并验证]
    ↓
[SCAFFOLD]  建交付包骨架（scripts/consulting_scaffold.R）
    ↓
[MIGRATE]   迁移数据/脚本/表/图进包
    ↓
[ISOLATE]   改路径，让包自包含、不依赖项目根
    ↓
[RUN_ALL]   按主流程语言写 run_all.R 或 run_all.py
    ↓
[REPRODUCE] 空 R session 或干净 Python 环境实测跑通
    ↓       ↓ 不通过回到 ISOLATE
[WRITE]     写 00_客户说明.md + 01_方法与结果.docx（模板见 references/templates.md §3-4）
    ↓
[ACADEMIC_EDIT] academic-humanizer 扫全包
    ↓
[FINAL]     终检 + 压缩 + 交付
```

**每阶不通过不许进入下一阶。REPRODUCE 失败必须回退修路径，不能靠在自己电脑上跑通蒙混。**

---

## 三、命名与编号

| 对象 | 格式 | 示例 |
|------|------|------|
| 文件夹 | `结果-M-D[-主题]`（用户指定名优先） | `结果-4-20-训练测试集` |
| 压缩包 | 同文件夹名 `.zip` | `结果-4-20-训练测试集.zip` |
| 包内脚本 | `NN_描述.R` 或 `NN_描述.py` 从 01 起 | `01_data_prep.R` |
| 包内表 | `TableN_描述.xlsx`（或 `TN_`/`TSN_`） | `Table1_baseline.xlsx` |
| 包内图 | `FigN_描述.pdf/.png`（或 `FN_`/`FSN_`） | `Fig2_forest.pdf` |

**禁止命名**：`最终版`、`最新`、`final2`、`new`、`修订`、`v2`、`修改后`。`05_reports/` 同一主题只保留一个当前包；反馈迭代前先把上一交付批次整包归档，再在当前包路径重建。用户明确要求日期入名时可更新当前包日期，但旧日期包不得继续留在 `05_reports/`。

**包内编号连续性（CRITICAL，与项目主文件夹同一标准）**：
- `data/`（含子目录）、`tables/`、`figures/` 内所有文件及 `code/` 的分析脚本一律带编号前缀且从 01（或 T1/F1）起连续，包括复制进来的原始数据与质性材料；`code/config.*`、`code/conventions.*` 作为单源 helper 不编号。
- 任何合并 / 增删 / 改名后立即重排补号，不许断号或跳号残留；脚本输出路径与脚本头注释同步改。
- 同主题多张表合并为单 xlsx 多 sheet，合并后下游编号顺延重排。
- docx 正文"表 N / 图 N"引用与包内文件编号保持一致，重排后同步改正文。

---

## 四、标准目录结构（CRITICAL）

```
05_reports/结果-4-20-训练测试集/
├── 00_客户说明.md              ← 逐文件清单（模板 §3）
├── 01_方法与结果.docx          ← 可直接阅读的方法+结果（要求 §4）
├── run_all.R / run_all.py      ← 与主流程语言一致的一键复现入口
├── README.md                   ← 文件清单（可选）
├── data/                       ← 本包需要的数据（编号从 01 起）
├── code/                       ← config.* / conventions.* + 包内分析脚本，从 01 起
├── results/                    ← 中间数据（xlsx，按内容命名不编号；禁 rds/RData）
├── tables/                     ← TableN_*.xlsx
└── figures/                    ← FigN_*.pdf + .png
```

**根目录只允许上面这些内容**。散落 `.csv`、截图、缓存、临时稿 → 全部清出或移入子目录。

骨架用 `scripts/consulting_scaffold.R` 的 `create_delivery_pack("结果-4-20-主题", language = "R")` 或 `language = "python"` 创建。

---

## 五、复现入口与包内脚本核心要求

完整模板见 `references/templates.md` §1-2；不可妥协的要求：

- R 包在空 R session 中运行 `run_all.R`；Python 包在用户选定的隔离环境中按锁定依赖运行 `run_all.py`。入口必须检查工作目录并按编号执行脚本。
- 脚本之间只靠 `results/*.xlsx` 传表格化数据，不靠环境变量；**禁 rds/RData**；模型对象不跨脚本传（留在产出它的脚本内、只导出结果表）。
- R 脚本声明完整 `library()`；Python 包提供 `requirements.txt` 或项目锁文件。全部路径相对，不读包外文件，不写死 `setwd()` 或绝对路径。
- 模板与输出内禁 emoji，状态用文字。
- 复现检查只使用本机已有的兼容 R/Python 环境。若环境或依赖缺失，停止检查并说明缺什么、影响什么以及用户可如何准备；不得创建虚拟环境或执行安装、升级命令。

---

## 六、REPRODUCE 阶段（强制）

```bash
# 1. 新开一个临时目录，复制交付包进去
cp -r "05_reports/结果-4-20-训练测试集" /tmp/test_pack
# 2A. R 包：启动新 R session（不继承当前环境）
Rscript --vanilla -e "setwd('/tmp/test_pack'); source('run_all.R')"
# 2B. Python 包：使用用户已准备好的隔离环境
/path/to/existing/environment/python /tmp/test_pack/run_all.py
```

Windows 使用用户已准备好的隔离环境中的 `python.exe` 执行同一流程。**通过标准**：复现入口无 error；所有预期 table / figure 都生成；数字与原 `03_tables/` 完全一致。
不通过 → 多是路径硬编码、依赖未声明、脚本顺序隐式依赖；回 ISOLATE 修。

---

## 七、ACADEMIC_EDIT 阶段（CRITICAL）

docx 写完后必须过 `academic-humanizer`（不可变事实清单 → 模式审计 → 最小改写 → 证据与语体复核）。本阶段交付包特有的补充：

- **不篡改真实溯源**：不得修改分析数据、审计字段、作者身份、工具使用或法规、期刊、合同要求披露的事实。扫描 csv/xlsx 仅用于发现意外调试文本、临时内部标签和不应外发的非分析字段；命中后先判定字段语义。
- 非分析审计字段只有在不影响结果、合同允许且导出 manifest 记录字段名与排除理由时，才可从外发副本排除；主流程源保持不变。无法判断是否应披露时保留并向用户报告。
- 全包（md / docx / 表 / 代码注释）禁 emoji；扫描用 perl Unicode 区间
  `[\x{1F300}-\x{1FAFF}\x{2600}-\x{27BF}]`（sed 对多字节 emoji 不可靠）。
- docx 禁出现的内容（版本号 / 内部变量名 / 调试痕迹等）见 `references/templates.md` §4。

**交付目标**：研究者视角、方法与结果准确、责任和工具披露真实、复现路径完整。后续修改按 §九 从主流程重生当前包。

---

## 八、FINAL 阶段 · 终检清单

发出去之前逐项对照：

### 可复现
- [ ] `run_all.R` 或 `run_all.py` 在隔离环境实测跑通（§六流程）
- [ ] 运行 `python <epi-project-audit技能目录>/scripts/run_check_project.py <项目根> --json`；入口已从安装清单解析中央 EpiAgentKit 源，无 ERROR 才能签发，WARN 已逐项解释
- [ ] 所有路径相对；依赖清单完整，新环境可按清单安装且缺包时明确停止

### 可读
- [ ] `00_客户说明.md` = 逐文件清单，每个文件一行用途（含 data 子目录每个文件）
- [ ] `01_方法与结果.docx` 篇幅与任务复杂度和客户需求匹配，图表真实嵌入，数字与 tables/ 一致
- [ ] 若交付论文初稿：按 `academic-publishing` 规范生成（见 templates.md §4 末尾）
- [ ] Word 字体、字号、行距符合学术标准

### 不露生成过程痕迹
- [ ] docx 过了 academic-humanizer；csv/xlsx 已扫描意外调试痕迹，真实分析、审计和披露字段未被篡改
- [ ] 全包无 emoji（含 md / 代码注释 / 表格单元格）
- [ ] 无内部版本号、调试痕迹、内部变量名；写作视角是"我做了 XX"
- [ ] 关键结论用科学克制语气（"提示"/"支持方向"），非"证实"/"明确"

### 编号
- [ ] data（含子目录）/ code / tables / figures 全部编号且从 01（T1/F1）连续无断号
- [ ] docx 正文"表 N / 图 N"与包内文件编号一致

### 目录干净
- [ ] 根目录只有 §四 规定内容；无 `.DS_Store` / `Thumbs.db` / `~$xxx.docx`
- [ ] 无 `旧版`/`备份`/`测试` 文件；压缩包名与文件夹名一致

### 安全
- [ ] 患者隐私已脱敏（ID 匿名化、出生日期 → 年龄）
- [ ] 无数据库密码、API key、内部路径；机构名按约定匿名

---

## 九、版本迭代规则

客户反馈后要改结果 → 先把上一版文件夹、同名 zip、对应主流程旧代码与核验记录整组移入 `09_backup/YYYY-MM-DD_HHMM_<主题>_<反馈阶段>/`，保留原相对目录并写 `MANIFEST.md`；随后在 `05_reports/` 重建唯一当前包，并在 `09_backup/INDEX.md` 顶部登记归档时间、目录、当前包路径和原因。

```
05_reports/
└── 结果-5-02-训练测试集/           ← 唯一当前交付包

09_backup/2026-05-02_1430_训练测试集_客户反馈/
├── MANIFEST.md
└── 05_reports/
    ├── 结果-4-25-训练测试集/
    └── 结果-4-25-训练测试集.zip
```

**禁止**：未留快照就覆盖上一版、用 `final_v2` 命名、让多个日期包并列留在 `05_reports/`、只归档成品却遗漏与该版绑定的代码或核验记录。

---

## 十、与其他 skill 的协作 + 常见问题

| 上游 | 本 skill 做什么 | 下游 |
|------|---------------|------|
| `biostat-principles` 原则 6（可复现） | 落实为语言匹配的复现入口 + 实测 | — |
| `r-biostats` 或 `python-biostats` 完成分析 | 打包、改路径、写客户文档 | `academic-humanizer` 做不可变事实清单、证据强度与学术语体审校 |
| `project-init --consulting` | 骨架已建 | 本 skill 做后续填充 |

| 常见问题 | 原因 | 预防 |
|------|------|------|
| 客户打开报错 | 路径硬编码 / 没锁定依赖 | REPRODUCE 必做 + 语言对应的依赖清单 |
| docx 数字和 xlsx 对不上 | 结果改了 docx 没更新 | 每次改分析重跑 docx 生成脚本 |
| 中文 PDF 乱码 | 用了默认 pdf() | 统一 `cairo_pdf` |
| 字体在客户电脑变形 | 本地特殊字体 | Times New Roman + 宋体 |
| 客户说"看不懂" | docx 太技术 | 00_客户说明.md 写明看哪里 |
| 文风模板化、缺少研究者声纹 | 套话太多 | ACADEMIC_EDIT 阶段不跳过 |
| 返工多次 | 开工没对齐口径 | `biostat-principles` 原则 1 严格执行 |

## reference 导航

| 文件 | 何时读 | 内容 |
|------|--------|------|
| `references/templates.md` | R 包 RUN_ALL / WRITE 阶段 | run_all.R 模板、包内脚本头部模板、00_客户说明.md 模板、01_方法与结果.docx 结构与禁词表 |
| `scripts/consulting_scaffold.R` | SCAFFOLD 阶段 | `create_delivery_pack()` 一键建骨架 |
