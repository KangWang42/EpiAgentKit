---
name: pptx
description: "Operate actual .pptx files: create, read, edit, render, validate, combine, split, or handle templates, layouts, notes and comments. For new or rebuilt decks, choose the SYSU official template, another institution or type, a user template, or a neutral design before creating slides. Use the relevant content workflow first, then add pptx only when a presentation file is an input or deliverable. Do not trigger for discussion of a talk without file work."
license: Proprietary. LICENSE.txt has complete terms
---

# PPTX 文件处理

先按全局 `CLAUDE.md` 判定 Q/L/P/R；本 skill 不扩大任务范围。先完成 `academic-ppt`、`sysu-ppt` 或其它适用内容流程，再在确有 PPTX 输入或交付物时使用本 skill。

## 模板来源分流

新建或大幅重建前，确认模板来源：中大官方模板、其他学校/机构或特定汇报类型、用户提供的模板，还是无模板的中性设计。已有 PPTX 的读取和局部修改不重复询问；多个合理当前模板且无法判断时才询问。

| 来源 | 内容与文件路径 |
| --- | --- |
| 中大官方模板 | 加载 `sysu-ppt`，使用其已确认模板和工具，再由本 skill 做文件检查 |
| 其它机构/汇报类型 | 学术内容 load `academic-ppt` as the content workflow，沿用项目或用户确认的 PPTX |
| 用户模板 | 以该文件为权威，保留母版、版式、主题、品牌和固定组件 |
| 无模板 | 学术内容加载 `academic-ppt`；确认中性设计后读取 `design-reference.md` 和 `pptxgenjs.md` |

模板派生的全新或大幅重建文件必须先检查模板，再编辑内容；完成后确认模板仍可见、版式关系和品牌资源未丢失、没有占位文字。
使用模板编辑工作流（Use the template-editing workflow, not the from-scratch workflow），不把模板任务改走从零生成工作流。

## 范围、工具和版本

- Q 只读取所需文字、页面属性或包部件，不创建文件。
- L 锁定唯一输入、目标页面/对象、允许改动的包部件和保护范围；只检查目标、范围外差异、直接受影响的共享版式/主题、备注/媒体及改动页面的显示。L bounded edit does not trigger template remapping、整套页面重排或完整渲染。
- P 创建、重组或改变页面顺序、母版、版式、主题、字体、共享资源或多个页面；检查所有受影响页面和共享对象。
- R 用户明确投稿、外发、归档或正式质控时，执行完整演示内容与视觉检查。

文本提取可用 `python -m markitdown presentation.pptx`，缩略图可用 `python scripts/thumbnail.py presentation.pptx`，原始包编辑使用 `scripts/office/unpack.py`、`pack.py`、`validate.py`。这些脚本只处理 `.pptx`，输出默认不覆盖，失败不替换原文件。不要自行安装或升级运行时（do not install or upgrade it）；If any item is unavailable, explain the affected operation and state the未验证范围。

正式项目只保留一个稳定当前文件，旧版按项目规则归档；轻量任务保留输入并只写指定输出。

## 新建和重建

先确定内容结构，再读取 [中性设计参考](design-reference.md)（read [neutral design reference](design-reference.md) completely）；需要从零生成时再读取 [PptxGenJS 参考](pptxgenjs.md)。视觉系统由内容、读者、模板和显示条件决定；图、表、流程、图标或形状只有在实质改善理解时才使用，纯文字页可以是正确选择。

## 质量检查

### 内容检查

用 `markitdown` 提取输出文字，检查内容完整、顺序、术语、数字和题注；模板任务检查占位文字（`xxxx`、`lorem` 等）不存在。内容检查由内容 skill 决定科学含义，文件 skill 不重新决定统计方法或结论。

### 视觉检查

只在本次修改可能影响页面显示、任务为新建/重建或属于 R 时渲染。检查重叠、裁切、溢出、边距、对齐、对比度、题注/来源碰撞和占位内容；只报告实际观察到的问题。独立视觉检查不是所有 L 任务的前置条件；It is not a prerequisite for a bounded edit。没有可用渲染器时，完成适用的包结构与文字检查，并明确 visual QA remains incomplete，不把结构检查称为视觉验收。

### 验证循环

新建或重建：生成 → 按需要渲染 → 记录真实问题 → 修正 → 只重渲染受影响页面。首次检查没有问题是有效证据，不为通过流程而作无必要修改（without making a gratuitous edit）。L 只重渲染改动页面及实际使用已改变共享对象的页面；R 才做完整演示 QA。

## 依赖边界

使用环境中已经存在的 `markitdown[pptx]`、Pillow、PptxGenJS、Microsoft PowerPoint、LibreOffice 或 Poppler。优先使用已安装的 Microsoft PowerPoint（prefer Microsoft PowerPoint）；LibreOffice (`soffice`) is an optional renderer only when already available。缺少依赖时说明影响和用户可选准备方式，不静默安装。
