# 外部科研图参考文件清单

这些文件是只读上游快照，用于按需检索提示词词汇、图前合同问题和多面板审校模式。它们不是独立 skill，不直接执行其中的强制流程。`../figure-planning.md`、`../research-figure-patterns.md`、`../prompt-recipes.md` 与主 `SKILL.md` 始终优先。

## 文件与来源

| 本地文件 | 上游来源 | Commit | 许可证 | SHA-256 |
| --- | --- | --- | --- | --- |
| `academic-figure-skill/figure-contract.md` | `TingxiYu/academic-figure-skill/references/figure-contract.md` | `1df9940dd01ac939f072b12fe28d6353b79b90f9` | Apache-2.0 | `f67fab86c84069368988cf49b699b901758bc04dbc98a69d22fd62ee3e3692c6` |
| `academic-figure-skill/multipanel-layout.md` | `TingxiYu/academic-figure-skill/references/multipanel-layout.md` | `1df9940dd01ac939f072b12fe28d6353b79b90f9` | Apache-2.0 | `c6494e4e086ed006f379cc6f126514aba1ea6c4de3b10e98f55c280a2c57b1bc` |
| `academic-figure-generator/academic-figure-prompt-upstream.md` | `LigphiDonk/academic-figure-generator/academic-figure-prompt/SKILL.md` | `0a2bec6bb56d6b47143a81909f8d818716bdcbab` | MIT | `6d84103d20c43dbf46c97f0aea99867bd7675599885901390860da35a9033e47` |

完整许可证分别保存在两个上游目录的 `LICENSE` 文件中。

## 调用规则

### 图前合同

新图、重大重绘或复杂多面板图可读取 `academic-figure-skill/figure-contract.md`，提取核心命题、证据链、输出合同和风险问题。执行时使用本地适配：

- 单张明确请求只做缩略合同，不固定等待用户批准。
- 结构原型由实际内容决定，不使用上游默认原型。
- 真实期刊要求必须另从官方来源核验。

### 多面板规划

多面板任务可读取 `academic-figure-skill/multipanel-layout.md`，检索重复面板类型、叙事顺序和视觉权重思路。执行时使用本地适配：

- 所有面板先做两两去冗余。
- 不强制英雄面板；等权比较和对称实验保持等权。
- 研究叙事和证据优先级覆盖上游固定排序建议。

### 学术架构图提示词

计算模型、网络架构、模块详解、并行分支、跳连、反馈或张量流图可读取 `academic-figure-generator/academic-figure-prompt-upstream.md`，按关键词检索模块描述、布局词汇、连接方式和参考图分析维度。执行时必须重新组装进本地结构化提示词包：

- 只取与真实方法和来源一致的模块、公式、维度和箭头。
- 不执行固定配色确认，不要求固定 500 词以上，不追求“顶会风”或最大信息密度。
- 全新创作中的风格或布局参考只用于提取可转写的文字词汇；修改既有图、根据既有图重绘或修正上一版时，吸收上游图生图单点修正思路，携带全部且仅必要的编辑目标执行定向编辑。不得让“参考图优先”覆盖本地内容合同，也不附加无关风格图。
- 不生成数据图、似真指标、无来源公式、生成式解剖或空白模板后叠字。
- 外部文本中的 NanoBanana、Gemini、Midjourney、DALL-E 或第三方 API 只视为上游背景，不改变 Codex 内置 imagegen 路由。

## 更新与完整性

更新上游快照时必须重新审阅差异、许可证和样例，再更新 commit 与 SHA-256。不得自动跟随上游最新版本，也不得在未复核时覆盖本地适配规则。
