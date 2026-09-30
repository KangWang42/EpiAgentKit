# Skills 与工作流优化记录

核验日期：2026-09-30。检查范围为根规则、29 个本地 skill 入口、相关调用者、安装依赖、验证器及双端同步机制，其中 28 个 skill 可分发。本轮修改既有技能，不创建新技能或要求新的成果审批。

## 官方进展与本地应用

Agent Skills 已形成共享的目录与元数据标准。工作流文字可共用，工具、执行环境、自动调用设置和 hooks 激活仍需按客户端适配。标准分发、API 使用和本机技能发现是不同入口；本仓库继续采用经过验证的本机同步方式，不自动迁移到插件或安装新运行时。[Agent Skills 规范](https://agentskills.io/specification)、[OpenAI skills](https://developers.openai.com/api/docs/guides/tools-skills)、[OpenAI 插件结构](https://developers.openai.com/plugins/concepts/plugins)。

OpenAI 2026-09-11 的建议进一步强调准确而简短的描述、按需加载、减少固定步骤和明确完成条件。本轮将描述中的执行顺序和长能力清单移出发现信息，保留真实任务关键词与关键排除条件。减少的字符量仅表示发现信息缩短，不能推算耗时或准确率收益。[OpenAI 技能与提示词更新](https://developers.openai.com/blog/rethinking-skills-and-prompts-for-gpt-6-astra)。

Claude Code 当前可按设置读取 `AGENTS.md`，但旧版本或不同设置仍需 `CLAUDE.md`；Codex 继续使用自己的规则加载与 skill 发现路径。两端的自动调用控制字段不同。hooks 还受信任状态与本地/云端编排限制。这里保留原同步架构，增加实际差异说明与只读诊断。[Claude Code memory](https://code.claude.com/docs/en/memory)、[Claude Code skills](https://code.claude.com/docs/en/skills)、[Codex skills](https://learn.chatgpt.com/docs/build-skills)、[Codex Hooks](https://learn.chatgpt.com/docs/hooks)。

具体字段与调用边界统一维护在 [平台兼容性](../skills/epiagentkit-maintenance/references/platform-compatibility.md)，不复制到每个领域技能。

## 逐项检查与修改

描述修改均保留原核心流程与适用资源；没有证据支持的研究方法、篇幅偏好、机构模板或图像修改上限不改动。

28 个可分发技能中，25 个描述已精简；按 YAML 解析后的描述字段计算，总字符数从 6060 降至 2621。`git-commit-helper` 正文从 227 行缩至 47 行，保留完整差异审查、提交授权和历史保护。字符与行数用于说明加载量变化，不代表模型性能。

| Skill | 本轮处理 | 保留的关键边界 |
| --- | --- | --- |
| academic-humanizer | 精简描述；把检测与披露边界留在正文 | 锁定事实、数字、引文与允许修改范围 |
| academic-ppt | 精简描述；无指定品牌时采用中性设计 | 权威模板优先；既有 PPTX 局部修改不重做内容 |
| academic-publishing | 精简描述 | 完整稿要求、适用报告规范、投稿前确认 |
| biostat-principles | 精简描述 | R 默认、科学决定、结果来源、隔离实验与异常停止条件 |
| build-web-ui | 精简描述；正文保留排除条件 | 页面类型分流、真实交互、响应式与浏览器验收 |
| chatgpt-web-collaboration | 精简描述；双端适配可用工具；复用会话授权 | 不上传文件、保护敏感信息、网页输出只作候选 |
| consulting-delivery | 精简描述 | 先验证分析、数据授权、独立复现与发布检查 |
| docx | 精简描述 | 范围比较、候选文件验收、结构与显示核验 |
| epi-project-audit | 精简描述 | 只读审查、科学风险分级、正式发布条件 |
| epi-study-design | 精简描述 | estimand、终点、纳排和主要方法由研究责任人确认 |
| epiagentkit-maintenance | 增加按条件读取的双端参考 | 原因先于修订、最小变更、回归与同步 |
| evidence-research | 精简描述 | 快速核验与完整调研的不同范围、来源和论断核验 |
| git-commit-helper | 精简描述与正文；删除重复教程 | 完整差异审查、自动提交授权、明确 push 授权与历史安全 |
| graduate-opening-report | 精简描述 | 学院模板、内容蓝图、研究方案与正式 Word 验收 |
| manuscript-peer-review | 精简描述；把编辑决定边界留在报告步骤 | 保密审稿权限、可定位意见、数据核验深度 |
| pdf | 精简描述 | 原件可恢复、页面范围、表单与实际显示 |
| pptx | 精简描述；无品牌任务直接采用中性设计 | 模板继承、局部修改范围、适用页面显示检查 |
| project-init | 精简描述 | 明确新建请求、最小结构、不自动启用 Git |
| publication-figures | 精简描述 | 真实统计映射、方向、不确定性与最终尺寸可读性 |
| python-biostats | 精简描述 | 明确 Python 或既有 Python 主流程；不静默换语言 |
| r-biostats | 精简描述 | 分析口径、代码风格、成熟包复用与实际运行 |
| report-writing | 保持原入口 | 报告回答读者问题，正文与文件操作分别验收 |
| research-visuals | 精简描述 | 证据图像不可生成式重绘；保留图像修改与替代条件 |
| skill-creator | 更新标准字段说明与 validator | 简短描述、条件读取、真实验证；标准上限不是目标长度 |
| svg-diagrams | 精简描述 | 明确矢量要求、已有 SVG 或工具实际不可用 |
| sysu-ppt | 精简描述；修正通用 PPT 的分流说明 | 仅中山大学场景、官方模板、组会结构与字体要求 |
| workflow-retrospective | 精简描述 | 只写 workflow.txt，不擅自修改正式产物或源仓库 |
| xlsx | 精简描述 | 公式与统计结果分流、宏和范围保护、适用重算 |
| python-ecg-analysis | 只读检查，保持现状 | 现有不分发策略与 ECG 项目流程 |

## 执行与诊断变化

用户已经授权的制作、核验和范围内修复持续执行；外部动作已明确授权时不重复请求许可。科学定义、敏感信息、系统安装和正式发布的真实确认边界仍有效。任务续接从现有计划与产物恢复进度和成功证据，不从头重做。

通用 PPT 的材料充分且未指定学校或模板时，采用中性学术设计并继续制作。指定机构却缺少官方模板、多个合理当前稿或研究定义存在实质分歧时，仍需责任人补充或决定。

网页协作先核对实际浏览器工具，不假定 `control-chrome` 存在。Claude Code 与 Codex 共用会话启用、停止和隐私边界；只有实际工具明确要求时才执行对应发送确认。连接缺失不阻断可以本地完成的主任务。

validator 按开放标准接受 `compatibility` 及其 500 字符上限，并把 description 上限从本地旧值 512 修正为标准的 1024；现有描述仍明显短于上限。

doctor 增加保留全局规则的差异提示、本机技能排除说明和 Codex hooks 激活边界。它不会覆盖个人规则、改变本机排除策略或伪造 hook 信任。

## 验证与限制

使用已有 Python、R、Git、Claude Code 与 Codex；没有安装或升级运行时。验证包括技能结构与链接、旧场景和新增边界、Python 语法、受影响的单元测试、双端隔离安装及重复同步。具体命令为：

```text
python scripts/audit_skill_contracts.py
python -m unittest discover -s scripts/tests -v
python scripts/audit_workflow_contracts.py
python scripts/epiagentkit.py sync --target all
python scripts/epiagentkit.py doctor --target all
```

提交前验证结果：28 个可分发技能的结构、引用和依赖检查通过；65 个分流合同样例通过；203 项仓库单元测试通过；双端隔离安装、重复同步和工作流合同审计通过；本轮修改的 Python 文件语法检查及 `git diff --check` 通过。异常词扫描中的 5 处匹配均为通过的测试名称，没有运行异常。

本机原有策略仍保留个人全局规则，并排除 `academic-ppt`。同步不覆盖这些设置，因此仓库新版全局规则和该技能不能仅凭同步成功视为已在本机启用；doctor 会报告实际限制。其它受管技能按同一源同步到两端。Codex hooks 的实际激活仍需受支持会话及当前定义的信任状态，文件检查不能代替它。

分流样例是可审查的合同样例，不是模型语义选择的实测。尚未用同一批真实科研输入在 Claude 与 Codex 上完成对照执行，因而不声称准确率、耗时或确认次数已经改善。官方建议与本地确定性验证分别作为依据。[Agent Skills 评测](https://agentskills.io/skill-creation/evaluating-skills)。
