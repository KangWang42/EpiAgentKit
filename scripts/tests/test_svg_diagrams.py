from __future__ import annotations

import binascii
import os
import struct
import subprocess
import sys
import tempfile
import unittest
import zlib
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
VALIDATOR = ROOT / "skills" / "svg-diagrams" / "scripts" / "validate_svg.py"


def png_chunk(name: bytes, data: bytes) -> bytes:
    return (
        struct.pack(">I", len(data))
        + name
        + data
        + struct.pack(">I", binascii.crc32(name + data) & 0xFFFFFFFF)
    )


def write_png(path: Path, width: int, height: int, dpi: int = 300) -> None:
    rows = b"".join(b"\x00" + b"\xff\xff\xff" * width for _ in range(height))
    pixels_per_meter = round(dpi / 0.0254)
    payload = b"".join(
        (
            b"\x89PNG\r\n\x1a\n",
            png_chunk(
                b"IHDR",
                struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0),
            ),
            png_chunk(
                b"pHYs",
                struct.pack(">IIB", pixels_per_meter, pixels_per_meter, 1),
            ),
            png_chunk(b"IDAT", zlib.compress(rows)),
            png_chunk(b"IEND", b""),
        )
    )
    path.write_bytes(payload)


def editorial_svg(size_group: str = "") -> str:
    group = f' data-size-group="{size_group}"' if size_group else ""
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 400 200">
  <defs>
    <marker id="arrow" markerWidth="8" markerHeight="8" refX="7" refY="4" orient="auto">
      <path d="M0 0 L8 4 L0 8 z" fill="#737B77" />
    </marker>
  </defs>
  <rect x="0" y="0" width="400" height="200" fill="#FFFFFF"
        data-role="canvas" data-category="covariate" data-tone="neutral" />
  <text x="200" y="30" text-anchor="middle" fill="#333A37"
        font-family="Arial, sans-serif" font-size="18" font-weight="700"
        data-role="figure-title">Semantic graph</text>
  <rect x="25" y="75" width="130" height="60" rx="4" fill="#E7F1ED"
        stroke="#3D7467" stroke-width="1.2" data-role="card"
        data-node-id="input" data-category="exposure" data-tone="primary"
        data-layer="pipeline"{group} />
  <text x="90" y="110" text-anchor="middle" fill="#28594F"
        font-family="Arial, sans-serif" font-size="16" font-weight="600"
        data-role="node-title" data-category="exposure" data-tone="primary">Input</text>
  <rect x="225" y="70" width="150" height="70" rx="4" fill="#F8F1E6"
        stroke="#B98543" stroke-width="1.2" data-role="card"
        data-node-id="output" data-category="outcome" data-tone="secondary"
        data-layer="pipeline"{group} />
  <text x="300" y="110" text-anchor="middle" fill="#7A582E"
        font-family="Arial, sans-serif" font-size="16" font-weight="600"
        data-role="node-title" data-category="outcome" data-tone="secondary">Output</text>
  <path d="M155 105 H225" fill="none" stroke="#737B77" stroke-width="1.5"
        marker-end="url(#arrow)" data-role="connector" data-arrow="true"
        data-source="input" data-target="output" data-relation="flow" />
</svg>
"""


class SvgDiagramValidatorTests(unittest.TestCase):
    def run_validator(self, svg: Path, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(VALIDATOR), str(svg), *args],
            cwd=ROOT,
            env=os.environ.copy(),
            text=True,
            capture_output=True,
            check=False,
        )

    def test_semantic_graph_and_single_title_pass(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            svg = Path(directory) / "valid.svg"
            svg.write_text(editorial_svg(), encoding="utf-8")
            result = self.run_validator(
                svg,
                "--profile",
                "editorial",
                "--purpose",
                "paper",
                "--single-title",
                "--require-semantic-graph",
                "--require-node",
                "input",
                "--require-node",
                "output",
                "--require-edge",
                "input->output",
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("semantic_nodes=2", result.stdout)
            self.assertIn("semantic_edges=1", result.stdout)

    def test_missing_required_edge_fails(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            svg = Path(directory) / "missing-edge.svg"
            svg.write_text(editorial_svg(), encoding="utf-8")
            result = self.run_validator(svg, "--require-edge", "input->missing")
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("required edge missing", result.stderr)

    def test_semantic_layer_does_not_force_equal_sizes(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            svg = Path(directory) / "natural-sizes.svg"
            svg.write_text(editorial_svg(), encoding="utf-8")
            result = self.run_validator(svg, "--profile", "editorial", "--purpose", "paper")
            self.assertEqual(result.returncode, 0, result.stderr)

    def test_size_group_enforces_equal_sizes(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            svg = Path(directory) / "size-group.svg"
            svg.write_text(editorial_svg("peer"), encoding="utf-8")
            result = self.run_validator(svg, "--profile", "editorial", "--purpose", "paper")
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("data-size-group='peer'", result.stderr)

    def test_png_physical_resolution_contract(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            svg = Path(directory) / "figure.svg"
            png = Path(directory) / "figure.png"
            svg.write_text(editorial_svg(), encoding="utf-8")
            write_png(png, 240, 120)
            result = self.run_validator(
                svg,
                "--preview-png",
                str(png),
                "--target-width-mm",
                "20",
                "--target-ppi",
                "300",
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("effective_ppi=304.8", result.stdout)
            self.assertIn("dpi_metadata=300.00x300.00", result.stdout)

    def test_png_with_too_few_pixels_fails(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            svg = Path(directory) / "figure.svg"
            png = Path(directory) / "figure.png"
            svg.write_text(editorial_svg(), encoding="utf-8")
            write_png(png, 200, 100)
            result = self.run_validator(
                svg,
                "--preview-png",
                str(png),
                "--target-width-mm",
                "20",
                "--target-ppi",
                "300",
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("below 237px required", result.stderr)


if __name__ == "__main__":
    unittest.main()
