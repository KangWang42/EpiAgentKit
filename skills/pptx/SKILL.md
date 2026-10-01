---
name: pptx
description: "Read, create, edit, render or validate .pptx files, including templates, layouts, notes and comments. Use for actual presentation files, not talk planning alone."
license: Proprietary. LICENSE.txt has complete terms
---

# PPTX 文件处理

本 skill 负责 `.pptx` 文件的读取、生成、修改、渲染和包结构检查。汇报内容先由 `academic-ppt`、`sysu-ppt` 或其它适用内容流程确定；本 skill 不重新决定科学内容。

## 1. 判定范围

- **Q 读取**：只提取所需文字、页面属性或包部件，不创建文件。
- **L 局部修改**：已有文件中指定页面、对象、文字、备注或媒体的修改。完整读取 [局部修改与模板编辑](editing.md) 第 1 节，按其步骤只改授权部件。局部修改不触发模板重新匹配、整套页面重排或完整渲染，也不重复询问模板来源。
- **P 新建或重建**：新建文件，或改变页面顺序、母版、版式、主题、字体、共享资源或多个页面。检查所有受影响页面和共享对象。
- **R 正式交付**：用户明确投稿、外发、归档或正式质控时，执行完整的内容与视觉检查。

## 2. 新建或重建前确定模板来源

从材料确定来源；未指定机构或模板且材料充分时直接采用中性设计并说明选择。只有明确要求机构模板但缺少文件，或存在多个合理的当前模板时才询问。

| 来源 | 做法 |
| --- | --- |
| 中大官方模板 | 加载 `sysu-ppt`，使用其模板和工具，再由本 skill 做文件检查 |
| 其它学校、机构或特定汇报类型 | 学术内容加载 `academic-ppt` 作为内容流程，沿用用户或项目确认的 PPTX |
| 用户提供的模板 | 以该文件为准，保留母版、版式、主题、品牌和固定组件；按 [editing.md](editing.md) 第 2 节的模板编辑流程进行，不改走从零生成流程 |
| 无模板 | 学术内容加载 `academic-ppt`；完整读取 [中性设计参考](design-reference.md)，从零生成时再读取 [PptxGenJS 参考](pptxgenjs.md) |

模板派生的文件完成后确认：模板仍可见，版式关系和品牌资源没有丢失，没有残留占位文字。

## 3. 工具

所有脚本只处理 `.pptx`，输出默认不覆盖已有文件，失败时不替换原文件。

| 操作 | 命令 |
| --- | --- |
| 提取文字 | `python -m markitdown presentation.pptx` |
| 模板缩略图（选版式用） | `python scripts/thumbnail.py presentation.pptx [前缀] [--cols N]` |
| 解包 / 打包 / 校验 | `python scripts/office/unpack.py in.pptx unpacked/`；`python scripts/office/pack.py unpacked/ out.pptx --original in.pptx`；`python scripts/office/validate.py out.pptx` |
| 复制页面或从版式新建页面 | `python scripts/add_slide.py unpacked/ slide2.xml` 或 `slideLayout2.xml` |
| 删除页面后清理孤立部件 | `python scripts/clean.py unpacked/` |
| 逐页渲染 PNG（Windows，已安装 PowerPoint） | `powershell -NoProfile -File scripts/render_slides.ps1 -InputPath out.pptx -OutputDir 空目录` |

渲染优先使用已安装的 Microsoft PowerPoint；`render_slides.ps1` 要求 PowerPoint 当前未运行，避免影响用户已打开的文件。没有 PowerPoint 时，只有在 LibreOffice（`soffice`）已经安装的情况下才用它转 PDF 再转图片。

使用环境中已有的 `markitdown[pptx]`、Pillow、defusedxml、PptxGenJS、PowerPoint、LibreOffice 或 Poppler。缺少某项时，说明受影响的操作、用户可选准备方式和未能验证的范围，不自行安装或升级运行时。

## 4. 检查

**内容**：用 `markitdown` 提取输出文字，核对完整性、顺序、术语、数字和题注；模板任务确认 `xxxx`、`lorem` 等占位文字不存在。

**视觉**：只在本次修改可能影响页面显示、任务为新建或重建、或属于 R 时渲染。检查重叠、裁切、溢出、边距、对齐、对比度、题注与来源碰撞以及占位内容，只报告实际看到的问题。局部修改只渲染改动页面，以及实际使用了已改变共享对象的页面；视觉检查不是所有局部修改的前置条件。没有可用渲染器时完成包结构和文字检查，并说明视觉检查未完成，不把结构检查称为视觉验收。

**修正循环**：生成，按需渲染，记录真实问题，修正，只重渲染受影响页面。首次检查没有问题是有效证据，不为显示检查过程而做无必要的修改。

正式项目只保留一个稳定的当前文件，旧版按项目规则归档；轻量任务保留输入文件，只写指定输出。
