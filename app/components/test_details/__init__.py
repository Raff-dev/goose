"""Public interface for test detail components."""

from __future__ import annotations

from app.components.test_details.detail_view import render_test_detail_view
from app.components.test_details.grid import render_test_details

__all__ = ["render_test_details", "render_test_detail_view"]
