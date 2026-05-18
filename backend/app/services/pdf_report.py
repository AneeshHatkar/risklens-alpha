from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

from backend.app.schemas import SimulationResult
from backend.app.services.report_generator import render_risk_report_html


def html_to_pdf_with_browser(
    html_path: str,
    pdf_path: str,
) -> Path:
    output = Path(pdf_path)
    output.parent.mkdir(parents=True, exist_ok=True)

    html_file = Path(html_path).resolve()
    pdf_file = output.resolve()

    chromium = (
        shutil.which("chromium")
        or shutil.which("chromium-browser")
        or shutil.which("google-chrome")
        or shutil.which("google-chrome-stable")
        or shutil.which("msedge")
    )

    macos_chrome = Path("/Applications/Google Chrome.app/Contents/MacOS/Google Chrome")
    macos_chromium = Path("/Applications/Chromium.app/Contents/MacOS/Chromium")
    macos_edge = Path("/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge")

    if chromium is None:
        if macos_chrome.exists():
            chromium = str(macos_chrome)
        elif macos_chromium.exists():
            chromium = str(macos_chromium)
        elif macos_edge.exists():
            chromium = str(macos_edge)

    if chromium is not None:
        command = [
            chromium,
            "--headless",
            "--disable-gpu",
            "--no-sandbox",
            f"--print-to-pdf={pdf_file}",
            f"file://{html_file}",
        ]

        subprocess.run(command, check=True)

        if not pdf_file.exists() or pdf_file.stat().st_size == 0:
            raise RuntimeError("PDF export failed or produced an empty file.")

        return pdf_file

    return html_to_pdf_with_playwright(
        html_path=str(html_file),
        pdf_path=str(pdf_file),
    )


def html_to_pdf_with_playwright(
    html_path: str,
    pdf_path: str,
) -> Path:
    try:
        from playwright.sync_api import sync_playwright
    except ImportError as error:
        raise RuntimeError(
            "PDF export requires either Chrome/Chromium or Playwright. "
            "Run: pip install playwright && python -m playwright install chromium"
        ) from error

    html_file = Path(html_path).resolve()
    pdf_file = Path(pdf_path).resolve()
    pdf_file.parent.mkdir(parents=True, exist_ok=True)

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        page = browser.new_page()
        page.goto(f"file://{html_file}", wait_until="networkidle")
        page.pdf(
            path=str(pdf_file),
            format="A4",
            print_background=True,
            margin={
                "top": "0.4in",
                "right": "0.4in",
                "bottom": "0.4in",
                "left": "0.4in",
            },
        )
        browser.close()

    if not pdf_file.exists() or pdf_file.stat().st_size == 0:
        raise RuntimeError("PDF export failed or produced an empty file.")

    return pdf_file


def render_risk_report_pdf(
    result: SimulationResult,
    html_output_path: str = "reports/html/latest_report.html",
    pdf_output_path: str = "reports/pdf/latest_report.pdf",
) -> Path:
    html_path = render_risk_report_html(
        result=result,
        output_path=html_output_path,
    )

    return html_to_pdf_with_browser(
        html_path=str(html_path),
        pdf_path=pdf_output_path,
    )
