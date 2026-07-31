import os
import subprocess
import tempfile
import shutil
import logging
from typing import Optional

logger = logging.getLogger(__name__)


def find_latex_compiler() -> Optional[str]:
    for cmd in ["tectonic", "pdflatex", "latexmk"]:
        if shutil.which(cmd):
            return cmd
    return None


def compile_pdf(latex_string: str) -> Optional[bytes]:
    """Compiles LaTeX string in a temporary directory and returns PDF bytes.

    Zero custom files are persisted to the project workspace.
    """
    compiler = find_latex_compiler()
    if not compiler:
        logger.info("No local LaTeX compiler (pdflatex / tectonic / latexmk) found.")
        return None

    with tempfile.TemporaryDirectory() as temp_dir:
        tex_path = os.path.join(temp_dir, "resume.tex")
        pdf_path = os.path.join(temp_dir, "resume.pdf")

        with open(tex_path, "w", encoding="utf-8") as f:
            f.write(latex_string)

        try:
            if compiler == "tectonic":
                cmd = [compiler, tex_path]
            elif compiler == "pdflatex":
                cmd = ["pdflatex", "-interaction=nonstopmode", "-output-directory", temp_dir, tex_path]
            else:  # latexmk
                cmd = ["latexmk", "-pdf", "-interaction=nonstopmode", f"-output-dir={temp_dir}", tex_path]

            subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True, cwd=temp_dir)

            if os.path.exists(pdf_path):
                with open(pdf_path, "rb") as f:
                    return f.read()
        except Exception as e:
            logger.warning(f"PDF compilation with {compiler} failed: {e}")
            return None

    return None


def open_pdf_in_viewer(pdf_bytes: bytes):
    """Saves PDF bytes to an OS temp file and opens it in default PDF viewer."""
    if not pdf_bytes:
        return

    # Use a named temporary file that gets auto-deleted or managed
    temp_dir = tempfile.mkdtemp()
    temp_pdf_path = os.path.join(temp_dir, "resume.pdf")

    with open(temp_pdf_path, "wb") as f:
        f.write(pdf_bytes)

    try:
        if os.name == "nt":  # Windows
            os.startfile(temp_pdf_path)
        elif os.name == "posix":  # macOS / Linux
            subprocess.run(["open" if shutil.which("open") else "xdg-open", temp_pdf_path])
    except Exception as e:
        logger.warning(f"Could not auto-open PDF viewer: {e}")
