#!/usr/bin/env python3

import csv
from pathlib import Path

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.shared import Mm, Pt


DEMO_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = DEMO_DIR / "output"
RESULTS_PATH = OUTPUT_DIR / "survival-demo-results.csv"
FIGURE_PATH = OUTPUT_DIR / "adjusted-survival-paper.png"
DOCX_PATH = OUTPUT_DIR / "manuscript-preview.docx"


def style_run(run, size=10.5, bold=False, east_asia="宋体"):
    run.bold = bold
    run.font.name = "Times New Roman"
    run.font.size = Pt(size)
    run._element.get_or_add_rPr().rFonts.set(qn("w:eastAsia"), east_asia)
    return run


def add_run(paragraph, text, **formatting):
    return style_run(paragraph.add_run(text), **formatting)


def format_body(paragraph, after=2, first_line=False):
    paragraph.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    paragraph.paragraph_format.line_spacing = 1.2
    paragraph.paragraph_format.space_after = Pt(after)
    if first_line:
        paragraph.paragraph_format.first_line_indent = Pt(21)
    return paragraph


def add_heading(document, text):
    paragraph = document.add_paragraph()
    paragraph.paragraph_format.space_before = Pt(4)
    paragraph.paragraph_format.space_after = Pt(2)
    paragraph.paragraph_format.keep_with_next = True
    add_run(paragraph, text, size=12, bold=True, east_asia="黑体")
    return paragraph


with RESULTS_PATH.open(encoding="utf-8-sig", newline="") as results_file:
    result = next(csv.DictReader(results_file))

n = int(result["n"])
events = int(result["events"])
hazard_ratio = float(result["hazard_ratio"])
ci_lower = float(result["ci_lower"])
ci_upper = float(result["ci_upper"])
p_value = float(result["p_value"])

document = Document()
section = document.sections[0]
section.page_width = Mm(210)
section.page_height = Mm(297)
section.top_margin = Mm(19)
section.bottom_margin = Mm(18)
section.left_margin = Mm(21)
section.right_margin = Mm(21)
section.header_distance = Mm(9)
section.footer_distance = Mm(9)

normal = document.styles["Normal"]
normal.font.name = "Times New Roman"
normal.font.size = Pt(10.5)
normal._element.rPr.rFonts.set(qn("w:eastAsia"), "宋体")

title = document.add_paragraph()
title.alignment = WD_ALIGN_PARAGRAPH.CENTER
title.paragraph_format.space_after = Pt(8)
add_run(
    title,
    "固定模拟队列中强化治疗方案与无事件生存的关联",
    size=16,
    bold=True,
    east_asia="黑体",
)

abstract = format_body(document.add_paragraph(), after=3)
add_run(abstract, "摘要　", bold=True)
add_run(abstract, "目的：", bold=True)
add_run(abstract, "评估固定模拟队列中强化治疗方案与无事件生存的关联。")
add_run(abstract, "方法：", bold=True)
add_run(
    abstract,
    "生成 1,200 名研究对象的模拟随访数据，随访上限为 36 个月。采用 Cox 比例风险模型评估治疗方案与无事件生存的关联，并调整年龄、性别、疾病分期和生物标志物。",
)
add_run(abstract, "结果：", bold=True)
add_run(
    abstract,
    f"共纳入 {n:,} 名模拟研究对象，随访期间发生 {events:,} 个结局事件。调整年龄、性别、疾病分期和标准化生物标志物后，强化方案组的结局发生风险低于常规方案组（风险比 = {hazard_ratio:.2f}，95% 置信区间：{ci_lower:.2f}～{ci_upper:.2f}，P < 0.001）。",
)
add_run(abstract, "结论：", bold=True)
add_run(
    abstract,
    "在该模拟队列及预设模型条件下，强化方案与较低的结局发生风险相关。模拟结果不构成真实临床证据。",
)

keywords = format_body(document.add_paragraph(), after=4)
add_run(keywords, "关键词　", bold=True)
add_run(keywords, "模拟队列；无事件生存；Cox 比例风险模型")

add_heading(document, "1　资料与方法")
methods = format_body(document.add_paragraph(), first_line=True)
add_run(
    methods,
    "本研究采用固定随机过程生成 1,200 名研究对象的队列资料。主要结局为 36 个月内发生的模拟事件，未发生事件者在 36 个月时行政删失。治疗方案分为常规方案和强化方案。Cox 比例风险模型纳入治疗方案、年龄、性别、疾病分期和标准化生物标志物；报告风险比、95% 置信区间和双侧 P 值。调整后生存曲线在共同协变量取值下估计。",
)

add_heading(document, "2　结果")
results = format_body(document.add_paragraph(), after=2, first_line=True)
add_run(
    results,
    f"分析共观察到 {events:,} 个结局事件。多变量模型显示，强化方案与较低的结局发生风险相关（风险比 = {hazard_ratio:.2f}，95% 置信区间：{ci_lower:.2f}～{ci_upper:.2f}，P = {p_value:.4f}）。两组调整后无事件生存曲线在随访期内逐渐分离，后期估计的不确定性随风险集减少而增加（图 1）。",
)

figure = document.add_paragraph()
figure.alignment = WD_ALIGN_PARAGRAPH.CENTER
figure.paragraph_format.space_before = Pt(2)
figure.paragraph_format.space_after = Pt(1)
figure.add_run().add_picture(str(FIGURE_PATH), width=Mm(156))

caption = document.add_paragraph()
caption.alignment = WD_ALIGN_PARAGRAPH.CENTER
caption.paragraph_format.space_after = Pt(0)
add_run(
    caption,
    "图 1　不同治疗方案的调整后无事件生存曲线",
    size=9,
)

zoom = document.settings._element.xpath("./w:zoom")
if zoom:
    zoom[0].set(qn("w:percent"), "100")

document.core_properties.title = "固定模拟队列中强化治疗方案与无事件生存的关联"
document.core_properties.subject = "模拟队列生存分析"
document.save(DOCX_PATH)
