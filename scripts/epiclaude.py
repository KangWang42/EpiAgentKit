#!/usr/bin/env python3
"""Compatibility entry point for the former EpiClaude command name."""

from epiagentkit import main


if __name__ == "__main__":
    raise SystemExit(main())
