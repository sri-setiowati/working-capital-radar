"""Find the five working-capital line items in IDX FinancialStatement .xlsx files.

Usage:  python find_in_xlsx.py "reports\\FinancialStatement-2025-Tahunan-ACES.xlsx"
Output: xlsx_candidates_<file name>.txt (sheet, row and cells of each matching row)
"""
import sys
from pathlib import Path

import pandas as pd

KEYWORDS = {
    "revenue": ["pendapatan", "penjualan neto", "penjualan bersih", "net sales", "revenue"],
    "cogs": ["beban pokok", "harga pokok", "cost of goods sold", "cost of revenue"],
    "trade_receivables": ["piutang usaha", "trade receivables", "accounts receivable"],
    "inventories": ["persediaan", "inventories"],
    "trade_payables": ["utang usaha", "trade payables", "accounts payable"],
}


def is_numeric(value) -> bool:
    if pd.isna(value):
        return False
    if pd.api.types.is_number(value):
        return True
    cleaned = (
        str(value).replace(",", "").replace(".", "").replace("-", "")
        .replace("(", "").replace(")", "").strip()
    )
    return cleaned.isdigit() and len(cleaned) >= 4


def main(path: str) -> None:
    sheets = pd.read_excel(path, sheet_name=None, header=None)
    found = []
    for sheet_name, frame in sheets.items():
        for row_no, row in frame.iterrows():
            values = row.tolist()
            cells = [str(v).strip() for v in values if pd.notna(v) and str(v).strip()]
            if not cells or not any(is_numeric(v) for v in values):
                continue
            text = " ".join(cells).lower()
            for item, words in KEYWORDS.items():
                if any(word in text for word in words):
                    found.append(
                        f"[{item}] sheet {sheet_name} row {row_no + 1}: "
                        + " | ".join(cells)[:260]
                    )
                    break
    out_path = Path(f"xlsx_candidates_{Path(path).stem}.txt")
    out_path.write_text("\n".join(found), encoding="utf-8")
    print(f"sheets: {list(sheets.keys())}")
    print(f"{len(found)} candidate rows written to {out_path}")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit('Usage: python find_in_xlsx.py "reports\\FinancialStatement-2025-Tahunan-ACES.xlsx"')
    main(sys.argv[1])