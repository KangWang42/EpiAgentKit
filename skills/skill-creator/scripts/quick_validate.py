#!/usr/bin/env python3
"""
Quick validation script for skills - minimal version
"""

import re
import sys
from urllib.parse import unquote

import yaml
from pathlib import Path


MAX_DESCRIPTION_CHARS = 512
PLACEHOLDER_FILES = {
    "scripts/example.py",
    "references/api_reference.md",
    "assets/example_asset.txt",
}
PROJECT_OUTPUT_ROOTS = {
    "01_data",
    "02_code",
    "03_tables",
    "04_figures",
    "05_reports",
    "06_results",
    "07_paper",
    "09_backup",
    "output",
    "dist",
}


def local_markdown_targets(content, skill_path):
    """Yield relative Markdown link targets outside fenced code blocks."""
    in_fence = False
    for line_number, line in enumerate(content.splitlines(), start=1):
        if line.lstrip().startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        for match in re.finditer(r"!?\[[^\]]*\]\(([^)]+)\)", line):
            raw = match.group(1).strip()
            if raw.startswith("<") and raw.endswith(">"):
                raw = raw[1:-1]
            raw = raw.split(maxsplit=1)[0].strip('"\'')
            target = unquote(raw.split("#", 1)[0])
            if not target or re.match(r"^[a-z][a-z0-9+.-]*:", target, re.I):
                continue
            normalized = target.replace("\\", "/")
            if normalized.split("/", 1)[0] in PROJECT_OUTPUT_ROOTS:
                continue
            yield line_number, target, (skill_path / target).resolve()

def validate_skill(skill_path):
    """Basic validation of a skill"""
    skill_path = Path(skill_path)

    # Check SKILL.md exists
    skill_md = skill_path / 'SKILL.md'
    if not skill_md.exists():
        return False, "SKILL.md not found"

    # Read and validate frontmatter
    content = skill_md.read_text(encoding='utf-8')
    if not content.startswith('---'):
        return False, "No YAML frontmatter found"

    # Extract frontmatter
    match = re.match(r'^---\n(.*?)\n---', content, re.DOTALL)
    if not match:
        return False, "Invalid frontmatter format"

    frontmatter_text = match.group(1)

    # Parse YAML frontmatter
    try:
        frontmatter = yaml.safe_load(frontmatter_text)
        if not isinstance(frontmatter, dict):
            return False, "Frontmatter must be a YAML dictionary"
    except yaml.YAMLError as e:
        return False, f"Invalid YAML in frontmatter: {e}"

    # Define allowed properties
    ALLOWED_PROPERTIES = {
        'name',
        'description',
        'license',
        'allowed-tools',
        'disable-model-invocation',
        'metadata',
    }

    # Check for unexpected properties (excluding nested keys under metadata)
    unexpected_keys = set(frontmatter.keys()) - ALLOWED_PROPERTIES
    if unexpected_keys:
        return False, (
            f"Unexpected key(s) in SKILL.md frontmatter: {', '.join(sorted(unexpected_keys))}. "
            f"Allowed properties are: {', '.join(sorted(ALLOWED_PROPERTIES))}"
        )

    # Check required fields
    if 'name' not in frontmatter:
        return False, "Missing 'name' in frontmatter"
    if 'description' not in frontmatter:
        return False, "Missing 'description' in frontmatter"

    disable_model_invocation = frontmatter.get('disable-model-invocation')
    if disable_model_invocation is not None and not isinstance(
        disable_model_invocation, bool
    ):
        return False, "'disable-model-invocation' must be a boolean"

    # Extract name for validation
    name = frontmatter.get('name', '')
    if not isinstance(name, str):
        return False, f"Name must be a string, got {type(name).__name__}"
    name = name.strip()
    if not name:
        return False, "Name cannot be empty"
    # Check naming convention (hyphen-case: lowercase with hyphens)
    if not re.match(r'^[a-z0-9-]+$', name):
        return False, f"Name '{name}' should be hyphen-case (lowercase letters, digits, and hyphens only)"
    if name.startswith('-') or name.endswith('-') or '--' in name:
        return False, f"Name '{name}' cannot start/end with hyphen or contain consecutive hyphens"
    # Check name length (max 64 characters per spec)
    if len(name) > 64:
        return False, f"Name is too long ({len(name)} characters). Maximum is 64 characters."
    if name != skill_path.name:
        return False, (
            f"Name '{name}' must match skill directory '{skill_path.name}'."
        )

    # Extract and validate description
    description = frontmatter.get('description', '')
    if not isinstance(description, str):
        return False, f"Description must be a string, got {type(description).__name__}"
    description = description.strip()
    if not description:
        return False, "Description cannot be empty"
    # Check for angle brackets
    if '<' in description or '>' in description:
        return False, "Description cannot contain angle brackets (< or >)"
    if len(description) > MAX_DESCRIPTION_CHARS:
        return False, (
            f"Description is too long ({len(description)} characters). "
            f"Maximum is {MAX_DESCRIPTION_CHARS}; move conditional detail into the body."
        )

    body = content[match.end():].lstrip('\r\n')
    body_lines = len(body.splitlines())
    if body_lines >= 500:
        return False, (
            f"SKILL.md body is too long ({body_lines} lines). "
            "Keep it under 500 lines and move conditional detail into references/."
        )

    for relative in sorted(PLACEHOLDER_FILES):
        if (skill_path / relative).is_file():
            return False, f"Initializer placeholder must be removed or replaced: {relative}"

    missing = [
        f"line {line_number}: {target}"
        for line_number, target, resolved in local_markdown_targets(content, skill_path)
        if not resolved.exists()
    ]
    if missing:
        return False, "Missing local Markdown target(s): " + "; ".join(missing)

    return True, "Skill is valid!"

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python quick_validate.py <skill_directory>")
        sys.exit(1)
    
    valid, message = validate_skill(sys.argv[1])
    print(message)
    sys.exit(0 if valid else 1)
