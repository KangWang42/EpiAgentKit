# docx-js 生成参考

仅在已经选择 JavaScript `docx` 生成新文件或大幅重建 Word 时使用。先读取 `delivery-requirements.md`；已有文件的局部修改不加载本参考。

## 基本建立与验证

```javascript
const { Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell, ImageRun,
        Header, Footer, AlignmentType, PageOrientation, LevelFormat,
        TableOfContents, HeadingLevel, BorderStyle, WidthType, ShadingType,
        PageNumber, PageBreak } = require('docx');

const doc = new Document({ sections: [{ children: [/* content */] }] });
Packer.toBuffer(doc).then(buffer => fs.writeFileSync("doc.docx", buffer));
```

生成后运行 `python scripts/office/validate.py doc.docx`。结构失败时修正生成器或包内容，不把验证器改为可选。

## 页面和样式

- 显式采用用户、模板或交付标准要求的页面大小和页边距。DXA 每英寸为 1440；US Letter 为 12240 × 15840，A4 为 11906 × 16838。
- 横向页面给 `docx-js` 传入纵向长短边并设置 `PageOrientation.LANDSCAPE`，由库交换方向。
- 覆盖内置标题时使用准确 ID（`Heading1`、`Heading2` 等）并设置 `outlineLevel`，否则目录层级不可靠。
- 没有模板或字体要求时沿用普通默认字体，标题保持黑色。

## 列表、表格、图片与分页

- 不使用 Unicode 圆点或换行符模拟列表；用 `LevelFormat.BULLET`、numbering reference 和独立 `Paragraph`。独立列表块使用不同 reference 重新开始编号。
- 表格总宽度等于 `columnWidths` 之和，同时给各单元格设置相符 DXA 宽度和必要内边距；不使用 `WidthType.PERCENTAGE`。三线表保持白底，只设置顶线、表头下横线和底线；机构表单服从模板边框。
- 分层统计表从内容 skill 确认的最终显示矩阵逐行生成；分组/父级行、子级缩进和连续行空白标签均保留对应稳定行键，数值对账继续使用来源行键与字段 ID。
- `ImageRun` 必须声明图像类型、尺寸和替代文字。图件对应正文位置和题注，核对媒体关系、显示尺寸及最终尺寸可读性。
- 分页使用含 `PageBreak` 的 `Paragraph` 或 `pageBreakBefore`，不能把 `PageBreak` 单独放入 children。
- 目录段落使用 `HeadingLevel`，避免以自定义样式代替真正标题层级。

## 完成前核对

- 页面尺寸、方向、页边距、页眉页脚和分页符合当前任务要求；
- 标题层级和目录字段正确；
- 列表编号、表格宽度、边框和跨页行为正确；
- 图件关系、替代文字、显示尺寸和题注对应；
- 正式页面显示通过当前任务要求的渲染检查。
