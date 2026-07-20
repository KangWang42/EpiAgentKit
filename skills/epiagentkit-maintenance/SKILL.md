---
name: epiagentkit-maintenance
description: 维护和持续优化 EpiAgentKit 仓库的专用 skill，覆盖全局或项目 `CLAUDE.md` / `AGENTS.md`、skills、references、hooks、安装同步脚本、合同测试与 README。触发场景：(1) 用户要求完善、重构或精简 EpiAgentKit 规则；(2) 新建或修改本仓库 skill；(3) 新建、修改或排查 hooks；(4) 调整安装、同步、doctor、路由、跨平台一致性或维护规范；(5) 审查这些组件是否简洁、优雅、结构清楚、约束明确且无行为回退。普通研究项目的数据分析、写作或项目初始化不触发本 skill。修改 skill 时同时使用 `skill-creator`；Git 仅在命令可用且当前目录为仓库时使用，不可用时跳过且不得安装。
---

# EpiAgentKit 维护

把规则、skills、hooks、脚本、测试和文档视为一个行为系统。基于真实缺口持续优化，不做追加式堆砌，不以缩短文件为由丢失已有能力。

## 1. 建立基线

1. 确认目标是 EpiAgentKit 源仓库或用户明确指定的副本；不要把普通研究项目当成本仓库维护。
2. 完整读取根 `CLAUDE.md`、`AGENTS.md`、目标组件及其直接 references、调用者、测试和同步路径。修改 skill 时先加载 `skill-creator`，并检查该 skill 的完整目录。
3. 只读检查运行环境。先判断命令是否存在，再运行验证；缺少 R、Python、Node、Java、LibreOffice、TeX、Git 或依赖时说明影响和用户可执行的准备方式，不创建环境，也不安装、升级或降级任何工具。
4. Git 仅作可选增强：命令可用且当前目录为仓库时读取状态和差异；Git 不可用或目录不是仓库时，改用文件清单、内容检索和直接校验建立基线，不执行 `git init`，不安装 Git，也不把缺少 Git 判为任务失败。
5. 不读取后回显凭证、私密设置或环境变量完整内容；只报告键、类型和设置状态。

## 2. 写变更合同

编辑前明确记录：

- **观察到的缺口**：真实失败、重复、冲突、误触发、漏触发、不可执行规则或过高上下文成本。
- **必须保留的行为**：旧场景、输出、兼容性、安全边界和安装结果。
- **最小变更集**：哪些内容保留、重写、合并、下沉、脚本化、删除或新增，以及理由。
- **代表性验证**：至少一个旧场景和一个新场景；涉及边界时同时包含应触发与不应触发用例。

没有可复现缺口时，不新增规则。两个方案通过相同验证时，选择更短、单源更清楚、维护成本更低的一项。

## 3. 选择唯一归属

| 内容 | 唯一归属 |
| --- | --- |
| 每个会话都必须知道的跨任务硬红线、总路由、单源指针、完成条件 | 根 `CLAUDE.md` |
| 本仓库结构、编码、验证、贡献和维护约定 | 根 `AGENTS.md` |
| 任务触发边界与核心工作流 | 对应 `SKILL.md` |
| 条件细节、长规范、变体和示例 | 对应 `references/` |
| 重复且需要确定性的操作 | 对应 `scripts/` |
| 必须在固定生命周期执行或阻断的检查 | `hooks/` 与客户端配置 |
| 安装、同步、依赖闭包和双端映射 | `scripts/config_core.py`、同步器及合同测试 |
| 面向使用者的能力、安装与安全说明 | `README.md` |

每个概念保持一个单源。更新概念单源时，同步修改所有调用者、模板、测试和文档；删除被替代的旧表述。不要把 skill 的条件参数复制进全局 `CLAUDE.md`，也不要把全局优先级在各 skill 重写一遍。

## 4. 按组件修改

### CLAUDE.md 与 AGENTS.md

- 先核对 Claude Code 官方 [memory](https://code.claude.com/docs/en/memory) 与 [best practices](https://code.claude.com/docs/en/best-practices)；只固化当前任务需要且经核验的机制。
- 根 `CLAUDE.md` 目标不超过 200 行，使用短段落、标题、列表和可验证措辞。只保留广泛适用且删除后会造成错误的规则；领域流程转 skill，目录或语言专属规则转项目或路径级规则。
- `AGENTS.md` 只保留本仓库开发约定，不复制领域规则。Claude Code 与 Codex 需要同一行为时，从仓库单源同步，不手工维护两份不同正文。
- “简洁、优雅、规范”必须落到可检查标准：目的适配、事实准确、层级清楚、结构紧凑、术语一致、版式克制、命令可执行、验收明确。

### Skills 与 references

- description 同时写清能力、具体触发场景、排除边界和上下游依赖；核心步骤用祈使式。
- `SKILL.md` 只放选择与执行主干，条件细节放一层可达的 references。避免深层引用、重复说明、教程式铺陈和无调用者资产。
- 新 skill 必须使用 `skills/skill-creator/scripts/init_skill.py` 初始化；删除全部占位资源，仅保留实际需要的文件。
- 运行 `python skills/skill-creator/scripts/quick_validate.py skills/<skill-name>`，再检查引用存在、触发边界、旧场景与新场景。

### Hooks、脚本与同步器

- 需要确定性阻断时用 hook，不用提示词模拟强制执行；同时控制误报、漏报、重复输出和上下文噪声。
- Python 运行 `python -m py_compile` 并以代表性输入实跑；Shell 运行 `bash -n` 并做安全样例；R 多行代码写入文件后用 `Rscript 文件.R` 实跑。
- Hook 变更同时核对 Claude Code 与 Codex 的事件名、匹配器、启动器、冲突清理和安装清单。Windows 路径与编码必须有代表性验证。
- 安装器、同步器、依赖闭包或工作流合同变更后，运行 `python scripts/audit_workflow_contracts.py`；不得只凭退出码，必须扫描完整输出中的异常词。

## 5. 验证与签发

按变更范围从小到大运行：

1. 目标组件的语法、validator 和代表性实跑。
2. `python -m unittest discover -s scripts/tests -v`。
3. 工作流合同变化时运行 `python scripts/audit_workflow_contracts.py`。
4. 运行 `python scripts/epiagentkit.py sync --target all` 与 `python scripts/epiagentkit.py doctor --target all`，确认 Claude Code 与 Codex 文件一致。
5. 全量扫描验证输出中的 `error|warning|traceback|failed|nan`，逐项归因；不能把预期提示、库噪声或真实失败混为一类。
6. 检查无占位文件、无失效引用、无重复单源、无 emoji、无生成过程痕迹，且未覆盖来源不明的既有改动。

Git 可用且当前目录为仓库时，最后审查完整差异并按全局约定提交；否则报告“Git 已跳过”，不初始化仓库、不安装 Git、不因此阻止签发。Push 仍只在用户当轮明确要求时执行。

## 6. 交付说明

先报告完成结果，再列出：改动的行为、保留的旧行为、验证命令与结果、兼容性或回退影响、Git 已提交或已跳过。不要把探索过程、内部思维或冗长逐文件流水账写进交付。
