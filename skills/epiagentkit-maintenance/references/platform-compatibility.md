# Claude Code、Codex 与 Agent Skills 兼容性

核验日期：2026-09-30。用于修改 skill 元数据、跨客户端工具调用、规则加载、hooks 和同步器；实施时还需核对实际客户端版本与会话工具。官方能力说明不能证明当前账号、会话或安装已经具备该能力。

## 共用内容与客户端差异

| 项目 | 已核验要求 | 本仓库处理 |
| --- | --- | --- |
| Skill 包 | `SKILL.md` 与 scripts、references、assets 可组成开放标准技能包 | 两端同步同一正文与资源；依赖闭包只负责安装，不强制同时调用 |
| 元数据 | 标准要求 name、description；description 最多 1024 字符，compatibility 最多 500 字符 | validator 接受标准字段和上限；描述仍只写能力、真实触发及关键排除 |
| 自动调用 | Claude Code 使用 `disable-model-invocation`；Codex 使用 `agents/openai.yaml` 的 `policy.allow_implicit_invocation` | 不把两个字段视为同一个设置；不因敏感动作而默认隐藏整个技能 |
| 全局规则 | Codex 读取 `~/.codex/AGENTS.md`；Claude Code 支持 `CLAUDE.md`，当前版本还可按 Project instructions 设置读取 `AGENTS.md` | 继续从根 `CLAUDE.md` 同步；不因新版本支持而强制迁移旧安装 |
| 规则容量 | Claude 建议短且有针对性的规则；Codex 默认项目文档合计上限为 32 KiB | 关注实际加载字节，不以增加上限替代清理重复规则 |
| 工具与浏览器 | 技能标准不提供工具、登录会话、模型或执行环境 | 按当前工具文档选择适配路径；缺失时报告具体功能，推进不依赖它的已授权工作 |
| Hooks | 两端命令 hooks 可共享部分事件与 JSON 结构，但支持范围与激活条件不同 | 检查事件、匹配器、输入、输出与启动器；doctor 的文件一致不等于实际会话已经运行 |

来源：[Agent Skills 规范](https://agentskills.io/specification)、[Codex skills](https://learn.chatgpt.com/docs/build-skills)、[Codex AGENTS.md](https://learn.chatgpt.com/docs/agent-configuration/agents-md)、[Claude Code skills](https://code.claude.com/docs/en/skills)、[Claude Code memory](https://code.claude.com/docs/en/memory)。

Claude Code 从 v2.1.277 起支持直接读取 `AGENTS.md`。默认在工作目录及其上级没有 `CLAUDE.md` 或 `CLAUDE.local.md` 时读取它；存在这些文件时，若需要同时读取两者，应核对 Project instructions 设置或使用正式的 `@AGENTS.md` 导入。本仓库继续要求维护任务读取根规则与仓库开发约定，不依赖模型自行猜测另一份文件。

## Hooks 的实际边界

Claude Code 在 Windows 上默认用 Git Bash 执行 hook 命令（未安装 Git Bash 时才用 PowerShell），hook 可用 `shell` 字段指定。Git Bash 会把以 `/` 开头的参数当作路径转换，`cmd.exe /d /s /c call ...` 因此失效并报“`run_hook.cmd` 不是内部或外部命令”。同步器为 Claude 生成 `"shell": "bash"` 和直接调用脚本的命令，Codex 保留 `run_hook.cmd` 启动器；hook 脚本传给 Windows Python 的路径用 `pwd -W` 取得。修改启动方式后，必须按客户端的实际 shell 执行生成的命令字符串验证，不能只用 Python 直接启动 cmd。来源：[Claude Code Hooks](https://code.claude.com/docs/en/hooks)（`shell` 字段说明，2026-10-01 核对）。

Codex 非受管 hooks 需要在 `/hooks` 中审阅并信任当前定义；新增或变更会要求重新审阅。不能写入虚构信任状态，也不把安装成功称为安全检查已经激活。Shell 与 unified exec 按 `Bash` 匹配，`apply_patch` 可按 `apply_patch`、`Edit` 或 `Write` 匹配；MCP 工具以实际工具名匹配。必须继续用本地代表性输入验证脚本解析，不能仅凭事件同名认定兼容。

本地命令 hooks 适用于受支持的本地编排和执行环境；云端编排即使连接本地计算机，也不能据此认定会运行这些 hooks。原始数据保护仍须落实到实际文件操作和分析入口，不能只依赖未确认激活的 hook。

来源：[Codex Hooks](https://learn.chatgpt.com/docs/hooks)、[Claude Code Hooks](https://code.claude.com/docs/en/hooks)。

## 优化的证据

OpenAI 2026-09-11 的技能与提示词更新建议缩短描述、按条件读取资源、删除不必要的固定步骤，并明确授权范围与完成条件。Claude Code 同样建议保持可验证任务、控制上下文并复用既有项目要求。对本仓库的应用是减少重复加载和没有实质分歧的确认，同时保留研究定义、科学证据、原始数据和成品验收责任。

比较旧版与新版时使用同一任务和原始输入，分别检查任务选择、额外工作、暂停次数、完整产物和验证结果。字符量只证明描述加载量变化；静态分流样例和安装测试不能证明模型速度、准确率或自动调用稳定性。未运行真实双模型任务时明确写出该限制，不发布性能百分比。

来源：[OpenAI 技能与提示词更新](https://developers.openai.com/blog/rethinking-skills-and-prompts-for-gpt-6-astra)、[Claude Code best practices](https://code.claude.com/docs/en/best-practices)、[Agent Skills 评测](https://agentskills.io/skill-creation/evaluating-skills)。
