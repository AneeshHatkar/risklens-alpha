from pathlib import Path

import pytest

from backend.app.main import run_simulation
from backend.app.services.pdf_report import html_to_pdf_with_browser, render_risk_report_pdf


def test_pdf_report_module_imports():
    assert callable(render_risk_report_pdf)
    assert callable(html_to_pdf_with_browser)


def test_html_to_pdf_raises_clear_error_for_missing_file_or_browser(tmp_path):
    html_path = tmp_path / "sample.html"
    html_path.write_text("<html><body>RiskLens Alpha</body></html>", encoding="utf-8")

    output_path = tmp_path / "sample.pdf"

    try:
        pdf_path = html_to_pdf_with_browser(
            html_path=str(html_path),
            pdf_path=str(output_path),
        )
        assert Path(pdf_path).exists()
    except RuntimeError as error:
        assert "browser" in str(error).lower() or "pdf export" in str(error).lower()
