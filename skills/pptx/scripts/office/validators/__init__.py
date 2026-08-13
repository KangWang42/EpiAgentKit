"""PPTX package validation."""

from .base import BaseSchemaValidator
from .pptx import PPTXSchemaValidator

__all__ = [
    "BaseSchemaValidator",
    "PPTXSchemaValidator",
]
