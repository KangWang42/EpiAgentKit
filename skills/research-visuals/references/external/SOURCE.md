# 外部科研图参考文件清单

这些文件是只读上游快照，用于按需检索提示词词汇、图前说明问题和组合图审校方法。它们不是独立 skill，不直接执行其中的强制流程。`../figure-planning.md`、`../research-figure-patterns.md`、`../prompt-recipes.md` 与主 `SKILL.md` 始终优先。

## 文件与来源

| 本地文件 | 上游来源 | Commit | 许可证 | SHA-256 |
| --- | --- | --- | --- | --- |
| `academic-figure-skill/figure-contract.md` | `TingxiYu/academic-figure-skill/references/figure-contract.md` | `1df9940dd01ac939f072b12fe28d6353b79b90f9` | Apache-2.0 | `f67fab86c84069368988cf49b699b901758bc04dbc98a69d22fd62ee3e3692c6` |
| `academic-figure-skill/multipanel-layout.md` | `TingxiYu/academic-figure-skill/references/multipanel-layout.md` | `1df9940dd01ac939f072b12fe28d6353b79b90f9` | Apache-2.0 | `c6494e4e086ed006f379cc6f126514aba1ea6c4de3b10e98f55c280a2c57b1bc` |
| `academic-figure-generator/academic-figure-prompt-upstream.md` | `LigphiDonk/academic-figure-generator/academic-figure-prompt/SKILL.md` | `0a2bec6bb56d6b47143a81909f8d818716bdcbab` | MIT | `6d84103d20c43dbf46c97f0aea99867bd7675599885901390860da35a9033e47` |

完整许可证分别保存在两个上游目录的 `LICENSE` 文件中。

## 已审阅但未直接归档的上游视觉分支

2026-08-04 复核了 [LigphiDonk/academic-figure-generator](https://github.com/LigphiDonk/academic-figure-generator) 当前 `main` 的 `academic-figure-prompt-pastel/SKILL.md` 和 README 示例图。当前仓库提交为 `0a2bec6bb56d6b47143a81909f8d818716bdcbab`，该 visual skill 首次见于提交 `4d903f9`，许可证沿用仓库 MIT。未复制其 skill 正文、固定模板或示例图片，只把下列可迁移原则改写进 `../visual-strategy.md`、`../prompt-recipes.md` 和 `../computer-science-visuals.md`：

- 用安静表面、克制分隔和明确层级建立整洁感；
- 把颜色放在语义 token、短标签、表示图元或连接线，而不是大面积彩色底板；
- 核心区域内容较丰富、辅助区域较安静，形成有目的的疏密节奏；
- 没有真实包含关系时减少框中框，让信息图元直接落在区域表面；
- 区域数量、大小和对称性由内容贡献决定，不机械套用等分网格。

明确拒绝固定纯白画布、指定字体、固定圆角和阴影数值、固定像素间距、强制填满面板、把每个任务做成柔彩卡片、自动加入曲线/公式/token、让参考图覆盖证据边界，以及以近期会议名替代真实期刊或项目要求。README 示例同时暴露了重复标签、生成式曲线和似真结构风险，因此只用于审美与失败模式分析，不作为科学内容或精度样例。

## OpenAI 官方提示依据

2026-08-04 核对了 OpenAI 的 [GPT Image Generation Models Prompting Guide](https://developers.openai.com/cookbook/examples/multimodal/image-gen-models-prompting-guide) 与 [Image generation](https://learn.chatgpt.com/docs/image-generation) 指南。它们不是归档快照，不向本仓库复制示例提示词；本地只吸收以下能够迁移到科研视觉工作流的原则：

- 复杂请求采用稳定顺序和短标签分段，不写成一个难以扫描的长段落；长提示词可以工作，不能把长度本身视为失败原因。
- 先用干净的基础提示词，再做小而单一的修改；每轮明确“只改什么”和“哪些内容保持不变”，防止编辑漂移。
- 图中文字保持简短、逐字指定；密集标签或复杂信息图在工具允许时比较 `medium` 与 `high` 质量。
- 密集信息图必须逐字复核。生产级文字、拓扑和排版不能假定一次生成即可完美遵循，必要时由用户决定继续修改或在满足任务格式与证据要求的设计工具中收尾。
- 提示词中的 `300 dpi`、`4K` 或 `print-ready` 不能替代真实输出参数与文件验收。最终毫米尺寸、最低像素、实际像素和 DPI 元数据继续按本地 `carrier-specs.md` 检查。

本地适配为 `prompt-recipes.md` 的五段最小包、精确图谱紧凑邻接表和单轮唯一修改目标。来源、采用理由、像素换算、验收日志与问题清单保留在调用外，避免把规划表当成模型提示词。

## 调用规则

### 图前说明

新图、重大重绘或由多个子图组成的复杂图件可读取 `academic-figure-skill/figure-contract.md`，提取核心命题、依据、输出要求和可能出错的内容。执行时使用本地适配：

- 单张明确请求只做简要说明，不固定等待用户批准。
- 结构原型由实际内容决定，不使用上游默认原型。
- 真实期刊要求必须另从官方来源核验。

### 组合图规划

由多个子图组成的图件可读取 `academic-figure-skill/multipanel-layout.md`，检索重复子图类型、内容顺序和视觉重点的处理方法。执行时使用本地适配：

- 所有子图先逐对检查是否重复。
- 不强制指定一个占据最大面积的主要子图；等权比较和对称实验保持相同视觉重点。
- 研究内容的先后关系和证据重要性优先于上游固定排序建议。

### 学术架构图提示词

计算模型、网络架构、模块详解、并行分支、跳连、反馈或张量流图可读取 `academic-figure-generator/academic-figure-prompt-upstream.md`，按关键词检索模块描述、布局词汇、连接方式和参考图分析维度。执行时必须重新组装进本地结构化提示词包：

- 只取与真实方法和来源一致的模块、公式、维度和箭头。
- 不执行固定配色确认，不要求固定 500 词以上，不追求“顶会风”或最大信息密度。
- 全新创作中的风格或布局参考只用于提取可转写的文字词汇；修改既有图、根据既有图重绘或修正上一版时，只采用上游文件中“每轮处理一个主要问题”的做法，并附带全部且仅必要的待修改图片。不得让参考图覆盖本地内容要求，也不附加无关风格图。
- 不生成数据图、似真指标、无来源公式、生成式解剖或空白模板后叠字。
- 外部文本中的 NanoBanana、Gemini、Midjourney、DALL-E 或第三方 API 只视为上游背景，不改变 Codex 内置 imagegen 的调用方式。

### 视觉美化词汇

需要为计算机方法图、教程图或其它多区域内容图增加视觉完成度时，可以读取本文件上一节的审阅结论，再使用本地 `visual-strategy.md` 中的五项视觉系统变量。不得直接执行上游 pastel skill，也不得把其固定画风作为默认答案。

## 更新与完整性

更新上游快照时必须重新审阅差异、许可证和样例，再更新 commit 与 SHA-256。不得自动跟随上游最新版本，也不得在未复核时覆盖本地适配规则。
