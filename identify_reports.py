"""List the newest PDFs in a folder: size, page count, first words of page 1.

Usage: python identify_reports.py [folder]   (default: your Downloads folder)
"""
import sys
from pathlib import Path

try:
    import pymupdf
except ImportError:
    import fitz as pymupdf

folder = Path(sys.argv[1]) if len(sys.argv) > 1 else Path.home() / "Downloads"
newest = sorted(folder.glob("*.pdf"), key=lambda p: p.stat().st_mtime, reverse=True)[:12]

for pdf in newest:
    size_mb = pdf.stat().st_size / 1_000_000
    try:
        with pymupdf.open(str(pdf)) as doc:
            pages = doc.page_count
            first = " ".join(doc[0].get_text().split())[:150] if pages else ""
    except Exception as exc:
        pages, first = 0, f"ERROR: {exc}"
    print(f"{pdf.name} | {size_mb:.2f} MB | {pages} pages | {first}")