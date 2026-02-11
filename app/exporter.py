"""Export meeting summaries to various formats."""

import os
from datetime import datetime

from fpdf import FPDF


EXPORT_DIR = "exports"


def _ensure_export_dir():
    os.makedirs(EXPORT_DIR, exist_ok=True)


def _make_filename(subject, ext):
    safe_name = "".join(c if c.isalnum() or c in " -_" else "" for c in subject)
    safe_name = safe_name.strip().replace(" ", "_")[:50]
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"{safe_name}_{timestamp}.{ext}"


def export_markdown(summary, subject="meeting"):
    """Save summary as a Markdown file."""
    _ensure_export_dir()
    filename = _make_filename(subject, "md")
    filepath = os.path.join(EXPORT_DIR, filename)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(summary)
    return filepath


def export_pdf(summary, subject="meeting"):
    """Save summary as a PDF file."""
    _ensure_export_dir()
    filename = _make_filename(subject, "pdf")
    filepath = os.path.join(EXPORT_DIR, filename)

    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_font("Helvetica", size=11)

    # Title
    pdf.set_font("Helvetica", "B", size=16)
    pdf.cell(0, 10, f"Meeting Summary: {subject}", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", size=9)
    pdf.cell(
        0, 6,
        f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        new_x="LMARGIN", new_y="NEXT",
    )
    pdf.ln(5)

    # Body
    pdf.set_font("Helvetica", size=11)
    for line in summary.split("\n"):
        if line.startswith("## "):
            pdf.ln(3)
            pdf.set_font("Helvetica", "B", size=13)
            pdf.cell(0, 8, line.replace("## ", ""), new_x="LMARGIN", new_y="NEXT")
            pdf.set_font("Helvetica", size=11)
        elif line.startswith("- "):
            pdf.cell(5, 6, "")
            pdf.multi_cell(0, 6, line)
        elif line.strip():
            pdf.multi_cell(0, 6, line)
        else:
            pdf.ln(3)

    pdf.output(filepath)
    return filepath


def export_text(summary, subject="meeting"):
    """Save summary as a plain text file."""
    _ensure_export_dir()
    filename = _make_filename(subject, "txt")
    filepath = os.path.join(EXPORT_DIR, filename)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(summary)
    return filepath
