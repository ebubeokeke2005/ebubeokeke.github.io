"""Renders a .docx resume to PDF using LibreOffice headless."""
import shutil
import subprocess
from pathlib import Path


def render_pdf(docx_path: Path) -> Path:
    soffice = shutil.which("soffice") or shutil.which("libreoffice")
    if not soffice:
        raise RuntimeError(
            "LibreOffice not found on PATH. Install it (e.g. `apt install "
            "libreoffice` or `brew install --cask libreoffice`) so `soffice` "
            "is available for headless PDF conversion."
        )

    output_dir = docx_path.parent
    result = subprocess.run(
        [
            soffice,
            "--headless",
            "--convert-to",
            "pdf",
            "--outdir",
            str(output_dir),
            str(docx_path),
        ],
        capture_output=True,
        text=True,
        timeout=120,
    )
    if result.returncode != 0:
        raise RuntimeError(f"LibreOffice PDF conversion failed:\n{result.stderr}")

    pdf_path = output_dir / (docx_path.stem + ".pdf")
    if not pdf_path.exists():
        raise RuntimeError(f"Expected PDF at {pdf_path} but it was not created.")
    return pdf_path
