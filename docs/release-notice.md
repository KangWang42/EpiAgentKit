# 许可与外部依赖说明

## 一、发布范围

release 1.1 只包含 `SKILLS_INCLUDED.txt` 列出的 17 个 skills、`CLAUDE.md`、使用说明和本说明。压缩包不包含用户配置、凭据、会话记录、缓存、研究数据、系统运行时或源仓库维护目录。

仓库当前没有覆盖全部自有内容的统一根许可证，因此本包按本地 release 制作，不构成公开再分发授权。公开上传、转发或再分发前，须由相应权利人确认其自有内容、引用材料和外部依赖的许可范围；不能从“文件可读取”推定已取得再分发授权。

包内某个 skill 或参考资料若自带许可证、来源说明或固定版本信息，这些文件均随原目录保留并分别适用。不得删除其中的版权、许可证或来源标识。

## 二、明确排除的内容

- `docx`、`pdf`、`pptx`、`xlsx`：这些文件处理 skills 的许可证不允许随本 release 再分发。
- `sysu-ppt`：包含中山大学模板资产，本 release 不提供机构模板。
- `python-ecg-analysis`、`build-web-ui`：属于本机开发或本地排除内容。
- `epiagentkit-maintenance`：依赖完整源仓库的规则、hooks、scripts、测试与同步器，不适合只含 skills 的轻量包。
- `publication-figures/references/recipes_common_50/`、`recipes_advanced/`、旧目录索引和目录生成资料：来源、许可、依赖和统计方法尚未完成核查。包内仅保留 `recipe-quarantine.md` 说明其隔离原因。

## 三、外部能力与运行时

`research-visuals` 使用平台提供的 imagegen 能力；imagegen 服务、模型和系统 skill 不属于本包。Word、PDF、PowerPoint 与 Excel 的实际读写依赖平台或本机已有且使用者有权使用的文件处理能力。本包也不提供 R、Python、Node、Java、LibreOffice、TeX、Git、系统库或统计分析包。

使用者应根据项目锁文件、兼容版本和数据授权准备运行环境。缺少系统运行时或受限制依赖时，不应由 Agent 静默安装、升级或改用非等价方案。

## 四、研究使用边界

本包提供研究工作流规则和 skills，不提供研究结论、临床建议或合规认证。使用者仍需对研究设计、数据授权、伦理、统计口径、结果解释、投稿要求和最终交付承担确认责任。示例中的模拟数据和模拟结果不能作为真实医学证据。
