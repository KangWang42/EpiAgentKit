#!/usr/bin/env python3

from pathlib import Path

from PIL import Image, ImageOps


DEMO_DIR = Path(__file__).resolve().parent
DOCS_DIR = DEMO_DIR.parent
OUTPUT_DIR = DOCS_DIR / "showcase" / "composites"


def fit_panel(image_path, panel_size, padding=26):
    with Image.open(image_path) as source:
        image = source.convert("RGB")
    available = (panel_size[0] - 2 * padding, panel_size[1] - 2 * padding)
    image.thumbnail(available, Image.Resampling.LANCZOS)
    panel = Image.new("RGB", panel_size, "white")
    x = (panel_size[0] - image.width) // 2
    y = (panel_size[1] - image.height) // 2
    panel.paste(image, (x, y))
    return ImageOps.expand(panel, border=1, fill="#D9E1E8")


def compose(image_paths, output_path, panel_size, gap=28, outer=28):
    panels = [fit_panel(path, panel_size) for path in image_paths]
    width = outer * 2 + sum(panel.width for panel in panels) + gap * (len(panels) - 1)
    height = outer * 2 + max(panel.height for panel in panels)
    canvas = Image.new("RGB", (width, height), "#F4F6F8")
    x = outer
    for panel in panels:
        y = (height - panel.height) // 2
        canvas.paste(panel, (x, y))
        x += panel.width + gap
    output_path.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(output_path, format="PNG", optimize=True)


def main():
    publication_dir = DEMO_DIR / "output" / "publication-figures"
    manuscript_dir = DEMO_DIR / "output" / "academic-publishing"
    sysu_ppt_dir = DEMO_DIR / "output" / "pptx"
    research_dir = DOCS_DIR / "showcase" / "research-visuals"
    academic_ppt_dir = DOCS_DIR / "showcase" / "academic-ppt"

    jobs = (
        (
            (
                publication_dir / "adjusted-survival.png",
                publication_dir / "cox-forest.png",
            ),
            OUTPUT_DIR / "publication-figures.png",
            (1180, 760),
        ),
        (
            (
                research_dir / "multiscale-attention.png",
                DOCS_DIR / "assets" / "research-workflow.webp",
            ),
            OUTPUT_DIR / "research-visuals.png",
            (1180, 820),
        ),
        (
            (
                manuscript_dir / "manuscript-preview-zh.png",
                manuscript_dir / "manuscript-preview-en.png",
            ),
            OUTPUT_DIR / "manuscripts.png",
            (760, 1050),
        ),
        (
            (
                sysu_ppt_dir / "presentation-cover.png",
                sysu_ppt_dir / "presentation-preview.png",
            ),
            OUTPUT_DIR / "sysu-ppt.png",
            (1180, 664),
        ),
        (
            (
                academic_ppt_dir / "survival-analysis-meeting.png",
                academic_ppt_dir / "missing-data-proposal-defense.png",
            ),
            OUTPUT_DIR / "academic-ppt.png",
            (1180, 664),
        ),
    )
    for inputs, output, panel_size in jobs:
        missing = [str(path) for path in inputs if not path.exists()]
        if missing:
            raise FileNotFoundError("缺少拼图输入：" + ", ".join(missing))
        compose(inputs, output, panel_size)
        print(f"已生成 {output.relative_to(DOCS_DIR.parent)}")


if __name__ == "__main__":
    main()
