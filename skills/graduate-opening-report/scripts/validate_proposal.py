#!/usr/bin/env python3
"""Deterministic preflight for a graduate thesis opening-report draft."""

from __future__ import annotations

import argparse
import json
import re
import sys
import zipfile
from pathlib import Path
from xml.etree import ElementTree


SECTION_GROUPS = {
    "background": ("立题背景", "研究背景", "立题依据", "研究意义"),
    "state_of_art": ("研究现状", "国内外研究", "文献综述", "研究进展", "研究空白", "证据缺口"),
    "significance": ("研究意义", "理论意义", "实际意义", "应用价值"),
    "purpose": ("研究目的", "研究问题"),
    "hypotheses": ("研究假设", "科学问题", "estimand"),
    "content": ("研究内容", "研究方案"),
    "methods": ("研究方法", "研究设计"),
    "population": ("研究对象", "目标人群", "研究场景", "来源人群"),
    "eligibility": ("纳入标准", "排除标准", "退出标准", "失访定义"),
    "exposure": ("暴露", "干预", "比较组", "对照组"),
    "outcomes": ("主要结局", "主要终点", "次要结局", "次要终点"),
    "measurement": ("测量工具", "操作性定义", "变量定义", "测量方法"),
    "sample_size": ("样本量", "精度依据", "把握度", "效能"),
    "data_management": ("数据管理", "数据安全", "数据来源", "变量字典"),
    "quality_control": ("质量控制", "质控", "标准操作", "逻辑核查"),
    "bias": ("偏倚", "混杂", "选择偏倚", "信息偏倚"),
    "missing": ("缺失数据", "缺失值", "失访", "敏感性分析"),
    "analysis_plan": ("统计分析", "分析计划", "主模型", "效应量", "置信区间"),
    "ethics": ("伦理", "知情同意", "隐私保护", "受试者保护"),
    "limitations": ("局限性", "风险应对", "研究风险", "应对措施"),
    "route": ("技术路线", "研究流程"),
    "expected": ("预期结果", "预期成果"),
    "innovation": ("创新", "研究亮点", "研究特色"),
    "feasibility": ("可行性",),
    "plan": ("工作计划", "研究计划", "各阶段", "工作安排"),
    "references": ("参考文献", "文献名录"),
    "appendix": ("附件", "附录", "导师意见", "评议意见", "签字"),
}

DESIGN_GROUPS = {
    "observational": {
        "terms": ("观察性", "队列", "横断面", "病例对照"),
        "required": {
            "time_zero": ("时间零点", "索引日期", "基线"),
            "follow_up": ("随访", "失访", "随访窗口"),
            "confounding": ("混杂", "混杂控制", "调整变量"),
            "noncausal": ("非因果", "不能解释为因果", "关联性解释", "不作因果"),
        },
    },
    "randomized": {
        "terms": ("随机对照", "随机分组", "随机化", "平行组"),
        "required": {
            "randomization": ("随机序列", "分配隐藏", "随机分配"),
            "fidelity": ("实施忠实度", "干预实施", "依从性"),
            "analysis_set": ("意向性分析", "符合方案分析", "分析集"),
            "safety": ("安全性", "不良事件", "暂停条件"),
        },
    },
    "prediction": {
        "terms": ("预测模型", "预后模型", "诊断准确性", "模型研究"),
        "required": {
            "validation": ("内部验证", "外部验证", "训练集", "验证集"),
            "performance": ("性能指标", "区分度", "校准"),
            "overfit": ("过拟合", "模型复杂度", "变量选择"),
        },
    },
    "qualitative": {
        "terms": ("质性研究", "访谈", "焦点小组", "混合方法"),
        "required": {
            "sampling": ("目的性抽样", "理论抽样", "参与者"),
            "coding": ("编码", "主题分析", "分析框架"),
            "credibility": ("可信度", "三角互证", "成员核对"),
        },
    },
}

MIN_DRAFT_TEXT_CHARS = 5000
MIN_ARCHIVE_TEXT_CHARS = 18000
MIN_SHOWCASE_TEXT_CHARS = 80000
MIN_DOCX_TABLES = 6
MIN_SHOWCASE_FILL_BLOCKS = 18
MIN_SHOWCASE_FILL_CHARS = 70000

PLACEHOLDER_PATTERNS = (
    r"\[待补充[^\]]*\]",
    r"\[待核验[^\]]*\]",
    r"【待补充[^】]*】",
    r"【待核验[^】]*】",
    r"【引文待核验[^】]*】",
    r"\[NEED\s+CONFIRMATION[^\]]*\]",
    r"\b(?:TODO|TBD|FIXME)\b",
    r"_{3,}",
    r"待定",
)

SHOWCASE_FILL_MARKER = re.compile(r"【结构测试填充：[^】]+】")
SHOWCASE_X_FILL = re.compile(r"(?i)x{12,}")
CITATION_PENDING = re.compile(r"【引文待核验(?:：[^】]+)?】")
SHOWCASE_REQUIRED_LABELS = ("结构完整性测试模板", "不得用于学院归档")

TOOL_LEAKAGE = re.compile(
    r"(?:ChatGPT|OpenAI|Codex|GPT[- ]?\d|prompt|large language model|LLM|AI生成|模型输出|提示词)",
    re.IGNORECASE,
)

W_NS = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"


def extract_text(path: Path) -> tuple[str, dict[str, int | None]]:
    if path.suffix.lower() in {".md", ".markdown", ".txt"}:
        return path.read_text(encoding="utf-8"), {"paragraphs": None, "tables": None}
    if path.suffix.lower() == ".docx":
        with zipfile.ZipFile(path) as package:
            xml = package.read("word/document.xml")
        root = ElementTree.fromstring(xml)
        paragraphs = []
        for paragraph in root.iter(f"{W_NS}p"):
            chunks = [node.text or "" for node in paragraph.iter(f"{W_NS}t")]
            if chunks:
                paragraphs.append("".join(chunks))
        tables = len(list(root.iter(f"{W_NS}tbl")))
        return "\n".join(paragraphs), {"paragraphs": len(paragraphs), "tables": tables}
    raise ValueError("仅支持 .md、.markdown、.txt 和 .docx")


def find_sections(text: str) -> dict[str, bool]:
    normalized = re.sub(r"\s+", "", text)
    return {
        key: any(term in normalized for term in alternatives)
        for key, alternatives in SECTION_GROUPS.items()
    }


def detect_design(text: str) -> tuple[str, dict[str, bool]]:
    normalized = re.sub(r"\s+", "", text)
    candidates = []
    for design, definition in DESIGN_GROUPS.items():
        score = sum(term in normalized for term in definition["terms"])
        candidates.append((score, design))
    score, design = max(candidates)
    if score == 0:
        return "general", {}
    required = DESIGN_GROUPS[design]["required"]
    return design, {
        key: any(term in normalized for term in alternatives)
        for key, alternatives in required.items()
    }


def count_references(text: str) -> int:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    start = next((index for index, line in enumerate(lines) if "参考文献" in re.sub(r"\s+", "", line) or "文献名录" in re.sub(r"\s+", "", line)), None)
    if start is None:
        return 0
    end = len(lines)
    for index in range(start + 1, len(lines)):
        normalized = re.sub(r"\s+", "", lines[index])
        if any(term in normalized for term in ("附件与评议", "附件清单", "附录", "导师意见", "专家评议")):
            end = index
            break
    reference_lines = lines[start + 1 : end]
    return sum(bool(re.match(r"^(?:\[\d+\]|\d+[、.])\s*\S+", line)) for line in reference_lines)


def validate(path: Path, mode: str = "draft", min_text_chars: int | None = None) -> dict:
    text, document_stats = extract_text(path)
    sections = find_sections(text)
    errors = []
    warnings = []
    completeness_issues = []
    if not sections["background"] or not sections["purpose"] or not sections["methods"]:
        errors.extend(f"缺少核心部分：{key}" for key, present in sections.items() if key in {"background", "purpose", "methods"} and not present)
    completeness_missing = [key for key, present in sections.items() if not present and key not in {"background", "purpose", "methods"}]
    if completeness_missing:
        completeness_issues.append("缺少完整报告模块：" + ", ".join(completeness_missing))
    design_branch, design_hits = detect_design(text)
    design_missing = [key for key, present in design_hits.items() if not present]
    if design_missing:
        completeness_issues.append(f"{design_branch} 研究缺少设计特异模块：" + ", ".join(design_missing))
    placeholder_count = sum(len(re.findall(pattern, text, flags=re.IGNORECASE)) for pattern in PLACEHOLDER_PATTERNS)
    showcase_fill_blocks = len(SHOWCASE_FILL_MARKER.findall(text))
    showcase_fill_matches = SHOWCASE_X_FILL.findall(text)
    showcase_fill_chars = sum(len(item) for item in showcase_fill_matches)
    citation_pending_count = len(CITATION_PENDING.findall(text))
    tool_hits = len(TOOL_LEAKAGE.findall(text))
    if tool_hits:
        completeness_issues.append(f"可能包含生成过程或工具归因词：{tool_hits} 处")
    default_text_chars = {
        "draft": MIN_DRAFT_TEXT_CHARS,
        "showcase": MIN_SHOWCASE_TEXT_CHARS,
        "archive": MIN_ARCHIVE_TEXT_CHARS,
    }[mode]
    required_text_chars = min_text_chars if min_text_chars is not None else default_text_chars
    if len(text.strip()) < required_text_chars:
        completeness_issues.append(f"正文仅 {len(text.strip())} 个字符，低于 {mode} 模式预检下限 {required_text_chars}；当前篇幅不足以证明完整报告深度")
    if sections["references"] and count_references(text) == 0:
        completeness_issues.append("检测到参考文献标题，但未识别到编号条目；请核对格式")
    reference_count = count_references(text)
    if sections["references"] and reference_count < 5:
        completeness_issues.append(f"参考文献编号条目约 {reference_count} 条，完整报告预检至少需要 5 条编号条目")
    if path.suffix.lower() == ".docx" and document_stats["tables"] is not None and document_stats["tables"] < MIN_DOCX_TABLES:
        completeness_issues.append(f"DOCX 仅检测到 {document_stats['tables']} 张表格，完整报告预检至少需要 {MIN_DOCX_TABLES} 张可核对表格")

    if mode == "showcase":
        if path.suffix.lower() != ".docx":
            errors.append("showcase 模式只验收可编辑 DOCX 展示成果")
        errors.extend(completeness_issues)
        missing_labels = [label for label in SHOWCASE_REQUIRED_LABELS if label not in text]
        if missing_labels:
            errors.append("缺少结构测试用途和归档禁用标识：" + ", ".join(missing_labels))
        if showcase_fill_blocks < MIN_SHOWCASE_FILL_BLOCKS:
            errors.append(f"结构测试填充块仅 {showcase_fill_blocks} 处，至少需要 {MIN_SHOWCASE_FILL_BLOCKS} 处以覆盖完整报告模块")
        if showcase_fill_chars < MIN_SHOWCASE_FILL_CHARS:
            errors.append(f"结构测试填充字符仅 {showcase_fill_chars} 个，至少需要 {MIN_SHOWCASE_FILL_CHARS} 个以检验长文装配")
        if citation_pending_count == 0:
            errors.append("未检测到【引文待核验】标记，无法确认测试模板没有伪造参考文献")
    elif mode == "archive":
        if path.suffix.lower() != ".docx":
            errors.append("archive 模式只验收可编辑 DOCX 正式报告")
        errors.extend(completeness_issues)
        if placeholder_count:
            errors.append(f"存在未解决占位符或空字段：{placeholder_count} 处")
        if showcase_fill_blocks or showcase_fill_chars:
            errors.append(f"存在结构测试填充：{showcase_fill_blocks} 块、{showcase_fill_chars} 个 x 字符")
    else:
        warnings.extend(completeness_issues)
        if placeholder_count:
            warnings.append(f"存在未解决占位符或空字段：{placeholder_count} 处")
        if showcase_fill_blocks or showcase_fill_chars:
            warnings.append(f"存在结构测试填充：{showcase_fill_blocks} 块、{showcase_fill_chars} 个 x 字符")
    status = "pass" if not errors and not warnings else "pass_with_warnings" if not errors else "fail"
    return {
        "file": str(path),
        "mode": mode,
        "status": status,
        "character_count": len(text.strip()),
        "minimum_character_count": required_text_chars,
        "word_count_approx": len(re.findall(r"\S+", text)),
        "section_hits": sections,
        "design_branch": design_branch,
        "design_hits": design_hits,
        "document_stats": document_stats,
        "reference_entries_approx": reference_count,
        "placeholder_count": placeholder_count,
        "showcase_fill_blocks": showcase_fill_blocks,
        "showcase_fill_chars": showcase_fill_chars,
        "citation_pending_count": citation_pending_count,
        "tool_leakage_count": tool_hits,
        "errors": errors,
        "warnings": warnings,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="检查研究生开题报告草稿的结构和未解决占位符")
    parser.add_argument("draft", type=Path, help=".md、.txt 或 .docx 文件")
    parser.add_argument(
        "--mode",
        choices=("draft", "showcase", "archive"),
        default="draft",
        help="draft 用于早期诊断；showcase 验证显式占位的完整结构 DOCX；archive 阻断所有占位并检查正式 DOCX",
    )
    parser.add_argument(
        "--min-text-chars",
        type=int,
        help="仅在官方模板已明确不同篇幅要求时覆盖当前模式的默认正文字符下限",
    )
    parser.add_argument("--strict", action="store_true", help="兼容旧命令，等同于 --mode archive")
    args = parser.parse_args()
    if args.strict and args.mode != "draft":
        parser.error("--strict 不能与显式 --mode 同时使用")
    mode = "archive" if args.strict else args.mode
    try:
        result = validate(args.draft, mode=mode, min_text_chars=args.min_text_chars)
    except (OSError, ValueError, KeyError, zipfile.BadZipFile, ElementTree.ParseError) as exc:
        result = {"file": str(args.draft), "status": "error", "errors": [str(exc)], "warnings": []}
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if result["status"] == "error" or result["errors"]:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
