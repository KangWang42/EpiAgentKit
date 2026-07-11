---
name: consulting-delivery
description: |
  统计咨询交付包标准技能。把 R 分析结果打包成客户可独立复现、可直接阅读、无模板化写作痕迹的专业交付物。
  触发场景：(1) 用户说"给客户做""咨询任务""交付给 XX""打包结果"；(2) 在 05_reports/ 下新建结果-M-D-主题 文件夹；(3) r-biostats 任务完成后需要外发；(4) 用户请人做的分析要发回对方。
  上游依赖：biostat-principles（尤其原则 6 可复现）+ r-biostats 已完成分析 + academic-humanizer 学术审校。
---

# 咨询交付包标准 skill

> **目标**：客户拿到一个 zip → 不问任何问题 → 运行 `run_all.R` → 重现全部结果 → 打开 `01_方法与结果.docx` 直接阅读 → 看不出是 AI 写的。

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

- **口径常量集中一处**：有序因子顺序、P 值格式、表组成、配色、字体、表图 registry 等放进被主流程与导出脚本共同 `source()` 的 `02_code/conventions.R` + `config.R`。改口径只改这一个文件，主流程与分享包各跑一次即同步。
- **分享包由导出脚本生成**：写 `02_code/NN_export_<topic>.R` 或 `09_backup` 一次性脚本，自动建目录→按分享编号复制数据/表/图→扫生成过程痕迹→出 docx，可随时重跑。要改分享内容 = 改主流程源 + 重跑导出，不进包手改。
- **冻结部分例外**：已发表/冻结的产物不套用新口径，在 DECISIONS 记为豁免。
- **防漂移两条硬规则**：① 分享包 `00_说明.md` 记一行"由 `<脚本>` 于 `<日期>` 从主流程导出"；② 用户在分享包里提的修改意见**必须回写主流程源 + conventions.R**，不能只改分享包。
- **若确实只想改分享、不动主流程**：在该包 `00_说明.md` 注明"脱离主流程的定制版，未回写"，并记 DECISIONS.md。

---

## 二、交付包状态机

```
[r-biostats 分析已完成]
    ↓
[SCAFFOLD]  建交付包骨架（scripts/consulting_scaffold.R）
    ↓
[MIGRATE]   迁移数据/脚本/表/图进包
    ↓
[ISOLATE]   改路径，让包自包含、不依赖项目根
    ↓
[RUN_ALL]   写 run_all.R 一键复现（模板见 references/templates.md §1）
    ↓
[REPRODUCE] 空 R session 实测跑通
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
| 包内脚本 | `NN_描述.R` 从 01 起 | `01_data_prep.R` |
| 包内表 | `TableN_描述.xlsx`（或 `TN_`/`TSN_`） | `Table1_baseline.xlsx` |
| 包内图 | `FigN_描述.pdf/.png`（或 `FN_`/`FSN_`） | `Fig2_forest.pdf` |

**禁止命名**：`最终版`、`最新`、`final2`、`new`、`修订`、`v2`、`修改后`。每个新版本用新日期建新包，不原地覆盖。

**包内编号连续性（CRITICAL，与项目主文件夹同一标准）**：
- `data/`（含子目录）、`tables/`、`figures/` 内所有文件及 `code/` 的分析脚本一律带编号前缀且从 01（或 T1/F1）起连续，包括复制进来的原始数据与质性材料；`code/config.R`、`code/conventions.R` 作为单源 helper 不编号。
- 任何合并 / 增删 / 改名后立即重排补号，不许断号或跳号残留；脚本输出路径与脚本头注释同步改。
- 同主题多张表合并为单 xlsx 多 sheet，合并后下游编号顺延重排。
- docx 正文"表 N / 图 N"引用与包内文件编号保持一致，重排后同步改正文。

---

## 四、标准目录结构（CRITICAL）

```
05_reports/结果-4-20-训练测试集/
├── 00_客户说明.md              ← 逐文件清单（模板 §3）
├── 01_方法与结果.docx          ← 可直接阅读的方法+结果（要求 §4）
├── run_all.R                   ← 一键复现脚本（模板 §1）
├── README.md                   ← 文件清单（可选）
├── data/                       ← 本包需要的数据（编号从 01 起）
├── code/                       ← config.R / conventions.R + 包内分析脚本，从 01 起（头部模板 §2）
├── results/                    ← 中间数据（xlsx，按内容命名不编号；禁 rds/RData）
├── tables/                     ← TableN_*.xlsx
└── figures/                    ← FigN_*.pdf + .png
```

**根目录只允许上面这些内容**。散落 `.csv`、截图、缓存、临时稿 → 全部清出或移入子目录。

骨架用 `scripts/consulting_scaffold.R` 的 `create_delivery_pack("结果-4-20-主题")` 一键创建。

---

## 五、run_all.R 与包内脚本核心要求

完整模板见 `references/templates.md` §1-2；不可妥协的要求：

- 在一台**空 R session + 空环境**里 `source("run_all.R")` 能跑通；脚本顶部检查工作目录与依赖包并自动安装。
- 脚本之间只靠 `results/*.xlsx` 传表格化数据，不靠环境变量；**禁 rds/RData**；模型对象不跨脚本传（留在产出它的脚本内、只导出结果表）。
- 每个 `code/NN_xxx.R` 开头有完整 `library()`；全部相对路径；不读包外文件、不 `setwd()` 绝对路径。
- 模板与输出内禁 emoji，状态用文字。

---

## 六、REPRODUCE 阶段（强制）

```bash
# 1. 新开一个临时目录，复制交付包进去
cp -r "05_reports/结果-4-20-训练测试集" /tmp/test_pack
# 2. 启动新 R session（不继承当前环境）
Rscript --vanilla -e "setwd('/tmp/test_pack'); source('run_all.R')"
```

**通过标准**：`run_all.R` 无 error；所有预期 table / figure 都生成；数字与原 `03_tables/` 完全一致。
不通过 → 多是路径硬编码、依赖未声明、脚本顺序隐式依赖；回 ISOLATE 修。

---

## 七、ACADEMIC_EDIT 阶段（CRITICAL）

docx 写完后必须过 `academic-humanizer`（事实锁 → 模式审计 → 最小改写 → 证据与语体复核）。本阶段交付包特有的补充：

- **数据文件同样要扫（不只 docx）**：包内所有 csv / xlsx 的列名与单元格值全量 grep
  `AI|assistant|assisted|机辅`，命中一律以研究者视角改写（如 coder 列 `AI_assisted` → `研究者`）。
  只改交付包副本，项目内部主档与 DECISIONS.md 保留真实审计记录。
  注意 `Colaizzi` 等词含 "ai" 子串，命中后人工确认再改。
- 全包（md / docx / 表 / 代码注释）禁 emoji；扫描用 perl Unicode 区间
  `[\x{1F300}-\x{1FAFF}\x{2600}-\x{27BF}]`（sed 对多字节 emoji 不可靠）。
- docx 禁出现的内容（版本号 / 内部变量名 / 调试痕迹等）见 `references/templates.md` §4。

**交付目标**：收件人看到的是委托人本人完成的分析与写作。后续修改意见一律新建新文件夹交付（§九），不在旧包上改。

---

## 八、FINAL 阶段 · 终检清单

发出去之前逐项对照：

### 可复现
- [ ] `run_all.R` 在空 session 实测跑通（§六流程）
- [ ] 所有路径相对；依赖包列表完整，新电脑能自动装

### 可读
- [ ] `00_客户说明.md` = 逐文件清单，每个文件一行用途（含 data 子目录每个文件）
- [ ] `01_方法与结果.docx` ≥ 3000 字，图表真实嵌入，数字与 tables/ 一致
- [ ] 若交付论文初稿：按 `academic-publishing` 规范生成（见 templates.md §4 末尾）
- [ ] Word 字体、字号、行距符合学术标准

### 不露生成过程痕迹
- [ ] docx 过了 academic-humanizer；包内全部 csv / xlsx 列值已扫生成过程与助手口吻相关标记并清零
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

客户反馈后要改结果 → **新建新日期的包**，旧包移 `09_backup/` 或保留原位。

```
05_reports/
├── 结果-4-20-训练测试集/           ← v1，已交付
├── 结果-4-25-训练测试集-亚组补充/  ← v2
└── 结果-5-02-训练测试集-终稿/      ← v3
```

**禁止**：在 v1 原地修改、用 `final_v2` 命名、在同一个文件夹里堆多次迭代。

---

## 十、与其他 skill 的协作 + 常见翻车

| 上游 | 本 skill 做什么 | 下游 |
|------|---------------|------|
| `biostat-principles` 原则 6（可复现） | 落实为 run_all.R + 实测 | — |
| `r-biostats` 完成分析 | 打包、改路径、写客户文档 | `academic-humanizer` 做事实锁、证据强度与学术语体审校 |
| `project-init --consulting` | 骨架已建 | 本 skill 做后续填充 |

| 翻车场景 | 原因 | 预防 |
|------|------|------|
| 客户打开报错 | 路径硬编码 / 没装依赖包 | REPRODUCE 必做 + run_all.R 自动装包 |
| docx 数字和 xlsx 对不上 | 结果改了 docx 没更新 | 每次改分析重跑 docx 生成脚本 |
| 中文 PDF 乱码 | 用了默认 pdf() | 统一 `cairo_pdf` |
| 字体在客户电脑变形 | 本地特殊字体 | Times New Roman + 宋体 |
| 客户说"看不懂" | docx 太技术 | 00_客户说明.md 写明看哪里 |
| 文风模板化、缺少研究者声纹 | 套话太多 | ACADEMIC_EDIT 阶段不跳过 |
| 返工多次 | 开工没对齐口径 | `biostat-principles` 原则 1 严格执行 |

## reference 导航

| 文件 | 何时读 | 内容 |
|------|--------|------|
| `references/templates.md` | RUN_ALL / WRITE 阶段 | run_all.R 模板、包内脚本头部模板、00_客户说明.md 模板、01_方法与结果.docx 结构与禁词表 |
| `scripts/consulting_scaffold.R` | SCAFFOLD 阶段 | `create_delivery_pack()` 一键建骨架 |
