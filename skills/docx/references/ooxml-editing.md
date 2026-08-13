# OOXML 高级编辑参考

只有确定性局部修订脚本正确拒绝当前操作，且任务确实需要直接修改字段、书签、批注、既有修订、绘图或复杂混合格式时使用本参考。普通文字、图片或格式修改不加载本文件。

## 1. 结构要求

- `<w:pPr>` 中常用元素顺序为 `<w:pStyle>`、`<w:numPr>`、`<w:spacing>`、`<w:ind>`、`<w:jc>`，`<w:rPr>` 最后。
- 首尾含空格的 `<w:t>` 加 `xml:space="preserve"`。
- RSID 使用 8 位十六进制值，例如 `00AB1234`。
- 新增引号或撇号时使用智能引号字符或相应 XML 实体；不得让转义过程改变可见正文。

## 2. 修订标记

插入和删除是段落中的独立元素：

```xml
<w:ins w:id="1" w:author="Reviewer" w:date="2025-01-01T00:00:00Z">
  <w:r><w:t>inserted text</w:t></w:r>
</w:ins>
<w:del w:id="2" w:author="Reviewer" w:date="2025-01-01T00:00:00Z">
  <w:r><w:delText>deleted text</w:delText></w:r>
</w:del>
```

`<w:del>` 中使用 `<w:delText>`，删除字段指令时使用 `<w:delInstrText>`。只标记实际变化部分，并把原 `<w:rPr>` 复制到相应新 run：

```xml
<w:r><w:t>The term is </w:t></w:r>
<w:del w:id="1" w:author="Reviewer" w:date="...">
  <w:r><w:delText>30</w:delText></w:r>
</w:del>
<w:ins w:id="2" w:author="Reviewer" w:date="...">
  <w:r><w:t>60</w:t></w:r>
</w:ins>
<w:r><w:t> days.</w:t></w:r>
```

删除整段或整个列表项时，同时在段落标记的 `<w:pPr><w:rPr>` 中加入 `<w:del/>`，否则接受修订后会残留空段落：

```xml
<w:p>
  <w:pPr>
    <w:numPr>...</w:numPr>
    <w:rPr><w:del w:id="1" w:author="Reviewer" w:date="..."/></w:rPr>
  </w:pPr>
  <w:del w:id="2" w:author="Reviewer" w:date="...">
    <w:r><w:delText>Entire paragraph content</w:delText></w:r>
  </w:del>
</w:p>
```

拒绝另一作者的插入时，在其 `<w:ins>` 内加入当前作者的 `<w:del>`；恢复另一作者删除的文字时，保留原 `<w:del>`，在其后增加当前作者的 `<w:ins>`，不得改写原作者修订记录。

## 3. 批注

运行 `scripts/comment.py` 建立批注部件后，在 `document.xml` 加定位标记。`<w:commentRangeStart>` 与 `<w:commentRangeEnd>` 是 `<w:r>` 的同级元素，不能放在 run 内：

```xml
<w:commentRangeStart w:id="0"/>
<w:r><w:t>commented text</w:t></w:r>
<w:commentRangeEnd w:id="0"/>
<w:r>
  <w:rPr><w:rStyle w:val="CommentReference"/></w:rPr>
  <w:commentReference w:id="0"/>
</w:r>
```

回复批注使用 `comment.py --parent` 创建，并把回复范围嵌在父批注范围内。每个批注引用 ID 必须与批注部件一致。

## 4. 图片关系

直接添加图片时必须同时完成四项：

1. 图片文件写入 `word/media/`。
2. 在 `word/_rels/document.xml.rels` 建立唯一关系，例如 `<Relationship Id="rId5" Type=".../image" Target="media/image1.png"/>`。
3. 在 `[Content_Types].xml` 声明图片扩展名。
4. 在 `document.xml` 以该关系 ID 引用，并设置显示尺寸；914400 EMU 等于 1 英寸。

```xml
<w:drawing>
  <wp:inline>
    <wp:extent cx="914400" cy="914400"/>
    <a:graphic>
      <a:graphicData uri=".../picture">
        <pic:pic><pic:blipFill><a:blip r:embed="rId5"/></pic:blipFill></pic:pic>
      </a:graphicData>
    </a:graphic>
  </wp:inline>
</w:drawing>
```

完成后运行包验证，并核对关系、内容类型、图片字节、替代文字、显示尺寸和受影响页面。不得用重新打包成功替代这些检查。
