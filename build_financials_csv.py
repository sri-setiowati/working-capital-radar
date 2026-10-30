from __future__ import annotations

import csv
import re
import warnings
from pathlib import Path

import pandas as pd

warnings.filterwarnings("ignore", category=UserWarning)

BASE = Path(__file__).resolve().parent
REPORTS = BASE / "reports"
SEEDS = BASE / "seeds"
SEEDS.mkdir(exist_ok=True)

FINANCIALS_PATH = SEEDS / "financials.csv"
AUDIT_PATH = BASE / "extraction_audit.csv"

FINANCIAL_FIELDS = [
    "company",
    "ticker",
    "fiscal_year",
    "revenue",
    "cogs",
    "trade_receivables",
    "inventories",
    "trade_payables",
    "unit",
    "source_file",
    "source_page",
]
AUDIT_FIELDS = [
    "ticker",
    "fiscal_year",
    "field",
    "label_baris",
    "nilai_mentah",
    "sheet",
    "nomor_baris",
    "kolom",
]
VALUE_FIELDS = ["revenue", "cogs", "trade_receivables", "inventories", "trade_payables"]

CURRENT = "current"
PRIOR = "prior"

SCALE_LABELS = {
    "satuan penuh": "IDR full",
    "full amount": "IDR full",
    "ribuan": "IDR thousand",
    "in thousand": "IDR thousand",
    "jutaan": "IDR million",
    "in million": "IDR million",
    "miliaran": "IDR billion",
    "in billion": "IDR billion",
}


def to_number(value):
    if value is None:
        return None
    if isinstance(value, (int, float)):
        if pd.isna(value):
            return None
        return int(value) if float(value).is_integer() else float(value)
    text = str(value).strip()
    if not text:
        return None
    negative = text.startswith("(") and text.endswith(")")
    text = text.replace("(", "").replace(")", "").replace(",", "").replace(" ", "")
    text = text.replace(".", "")
    if text in {"", "-"}:
        return None
    try:
        number = float(text)
    except ValueError:
        return None
    if negative:
        number = -number
    return int(number) if number.is_integer() else number


def format_number(value):
    if value is None:
        return ""
    if isinstance(value, float) and not value.is_integer():
        return repr(value)
    return str(int(value))


def label_at(frame, row_index):
    if row_index >= len(frame) or frame.shape[1] == 0:
        return ""
    value = frame.iat[row_index, 0]
    return "" if pd.isna(value) else str(value).strip()


def row_candidates(frame, predicate, current_col, prior_col):
    found = []
    for i in range(len(frame)):
        label = label_at(frame, i)
        if not predicate(label):
            continue
        cur = to_number(frame.iat[i, current_col])
        pri = to_number(frame.iat[i, prior_col])
        if cur is None and pri is None:
            continue
        found.append(
            {
                "row": i + 1,
                "label": label,
                "current": cur,
                "prior": pri,
                "current_col": current_col,
                "prior_col": prior_col,
            }
        )
    return found


def exact_labels(*labels):
    wanted = {label.lower() for label in labels}
    return lambda label: label.lower() in wanted


def starts_with(prefix):
    return lambda label: label.lower().startswith(prefix.lower())


def distinct_values(candidates, period):
    return {c[period] for c in candidates if c[period] is not None}


def read_meta(sheets):
    general = sheets["1000000"]
    company = str(general.iat[5, 1]).strip()
    ticker = str(general.iat[7, 1]).strip().upper()
    current_date = str(general.iat[23, 1]).strip()
    prior_date = str(general.iat[24, 1]).strip()
    currency = str(general.iat[28, 1]).strip()
    scale = str(general.iat[30, 1]).strip()

    current_year = int(re.match(r"(\d{4})", current_date).group(1))
    prior_year = int(re.match(r"(\d{4})", prior_date).group(1))

    if "rupiah" not in currency.lower() and "idr" not in currency.lower():
        raise RuntimeError(f"{ticker}: non-rupiah currency {currency!r}")

    scale_key = next(
        (key for key in SCALE_LABELS if key in scale.lower()),
        None,
    )
    if scale_key is None:
        raise RuntimeError(f"{ticker}: unknown scale {scale!r}")

    return {
        "company": company,
        "ticker": ticker,
        "current_year": current_year,
        "prior_year": prior_year,
        "currency": currency,
        "scale": scale,
        "unit": SCALE_LABELS[scale_key],
    }


def pick_value(candidates, period, fallback_candidates=None):
    values = distinct_values(candidates, period)
    used = candidates
    if not values and fallback_candidates is not None:
        used = fallback_candidates
        values = distinct_values(used, period)
    if len(values) == 1:
        value = next(iter(values))
        source = next(c for c in used if c[period] == value)
        return value, source, None
    if len(values) > 1:
        return None, None, f"multiple distinct values {sorted(values)}"
    return None, None, "no numeric value"


def column_letter(index):
    letters = ""
    index += 1
    while index:
        index, remainder = divmod(index - 1, 26)
        letters = chr(65 + remainder) + letters
    return letters


def cell_ref(sheet, row, col_index):
    return f"{sheet}!{column_letter(col_index)}{row}"


def extract_period(sheets, period, audit_rows):
    current = period == CURRENT
    cur_idx = 1
    pri_idx = 2

    revenue_candidates = []
    cogs_candidates = []
    for sheet_name in ["1311000", "1321000"]:
        frame = sheets.get(sheet_name)
        if frame is None:
            continue
        revenue_candidates += [
            {**c, "sheet": sheet_name}
            for c in row_candidates(
                frame,
                exact_labels("Penjualan dan pendapatan usaha"),
                cur_idx,
                pri_idx,
            )
        ]
        cogs_candidates += [
            {**c, "sheet": sheet_name}
            for c in row_candidates(
                frame,
                exact_labels("Beban pokok penjualan dan pendapatan"),
                cur_idx,
                pri_idx,
            )
        ]

    note_revenue = []
    for sheet_name in ["1617000", "1618000"]:
        frame = sheets.get(sheet_name)
        if frame is None:
            continue
        note_revenue += [
            {**c, "sheet": sheet_name}
            for c in row_candidates(
                frame,
                exact_labels(
                    "Pendapatan dari produk",
                    "Tipe pendapatan",
                    "Sumber pendapatan",
                ),
                2,
                6,
            )
        ]

    note_cogs = []
    frame = sheets.get("1670000")
    if frame is not None:
        note_cogs = [
            {**c, "sheet": "1670000"}
            for c in row_candidates(
                frame,
                exact_labels("Beban pokok penjualan dan pendapatan"),
                cur_idx,
                pri_idx,
            )
        ]

    balance = sheets["1210000"]
    inventory_candidates = [
        {**c, "sheet": "1210000"}
        for c in row_candidates(
            balance,
            exact_labels("Persediaan lancar"),
            cur_idx,
            pri_idx,
        )
    ]

    note_inventory = []
    frame = sheets.get("1630000")
    if frame is not None:
        note_inventory = [
            {**c, "sheet": "1630000"}
            for c in row_candidates(
                frame,
                exact_labels("Persediaan", "Persediaan lancar"),
                cur_idx,
                pri_idx,
            )
        ]

    receivables = [
        {**c, "sheet": "1210000"}
        for c in row_candidates(
            balance,
            starts_with("Piutang usaha pihak"),
            cur_idx,
            pri_idx,
        )
    ]
    if not receivables:
        receivables = [
            {**c, "sheet": "1210000"}
            for c in row_candidates(
                balance,
                exact_labels("Piutang usaha"),
                cur_idx,
                pri_idx,
            )
        ]

    payables = [
        {**c, "sheet": "1210000"}
        for c in row_candidates(
            balance,
            starts_with("Utang usaha pihak"),
            cur_idx,
            pri_idx,
        )
    ]
    if not payables:
        payables = [
            {**c, "sheet": "1210000"}
            for c in row_candidates(
                balance,
                exact_labels("Utang usaha"),
                cur_idx,
                pri_idx,
            )
        ]

    values = {}
    refs = {}
    ambiguous = {}

    for field, primary, fallback in [
        ("revenue", revenue_candidates, note_revenue),
        ("cogs", cogs_candidates, note_cogs),
        ("inventories", inventory_candidates, note_inventory),
    ]:
        value, source, error = pick_value(primary, period, fallback)
        values[field] = value
        if source is not None:
            refs[field] = [source]
            audit_rows.append(
                {
                    "field": field,
                    "label_baris": source["label"],
                    "nilai_mentah": value,
                    "sheet": source["sheet"],
                    "nomor_baris": source["row"],
                    "kolom": column_letter(
                        source[f"{period}_col"]
                    ),
                }
            )
        else:
            ambiguous[field] = error
            audit_rows.append(
                {
                    "field": field,
                    "label_baris": error,
                    "nilai_mentah": "AMBIGUOUS",
                    "sheet": "",
                    "nomor_baris": "",
                    "kolom": "",
                }
            )

    for field, candidates in [
        ("trade_receivables", receivables),
        ("trade_payables", payables),
    ]:
        selected = [c for c in candidates if c[period] is not None]
        if selected:
            values[field] = sum(c[period] for c in selected)
            refs[field] = selected
            for source in selected:
                audit_rows.append(
                    {
                        "field": field,
                        "label_baris": source["label"],
                        "nilai_mentah": source[period],
                        "sheet": source["sheet"],
                        "nomor_baris": source["row"],
                        "kolom": column_letter(source[f"{period}_col"]),
                    }
                )
        else:
            values[field] = None
            ambiguous[field] = "no numeric value"
            audit_rows.append(
                {
                    "field": field,
                    "label_baris": "no numeric value",
                    "nilai_mentah": "AMBIGUOUS",
                    "sheet": "",
                    "nomor_baris": "",
                    "kolom": "",
                }
            )

    ref_text = []
    for field in VALUE_FIELDS:
        if field not in refs:
            ref_text.append(f"{field}=AMBIGUOUS")
            continue
        parts = [
            cell_ref(source["sheet"], source["row"], source[f"{period}_col"])
            for source in refs[field]
        ]
        ref_text.append(f"{field}={'+'.join(parts)}")

    return values, "; ".join(ref_text), ambiguous


def main():
    financial_rows = []
    audit_rows = []
    warnings_list = []

    for path in sorted(REPORTS.glob("FinancialStatement-*.xlsx")):
        sheets = pd.read_excel(path, sheet_name=None, header=None)
        meta = read_meta(sheets)

        if meta["ticker"] not in path.stem:
            warnings_list.append(
                f"{path.name}: filename ticker does not match entity code {meta['ticker']}"
            )

        for period, year in [
            (CURRENT, meta["current_year"]),
            (PRIOR, meta["prior_year"]),
        ]:
            period_audit = []
            values, source_page, ambiguous = extract_period(
                sheets, period, period_audit
            )
            row = {
                "company": meta["company"],
                "ticker": meta["ticker"],
                "fiscal_year": year,
                **{field: values[field] for field in VALUE_FIELDS},
                "unit": meta["unit"],
                "source_file": path.name,
                "source_page": source_page,
            }
            financial_rows.append(row)
            for entry in period_audit:
                audit_rows.append(
                    {
                        "ticker": meta["ticker"],
                        "fiscal_year": year,
                        **entry,
                    }
                )
            for field, reason in ambiguous.items():
                warnings_list.append(
                    f"{meta['ticker']} {year} {field}: {reason}"
                )

    latest_company = {}
    for row in financial_rows:
        ticker = row["ticker"]
        current = latest_company.get(ticker)
        if current is None or row["fiscal_year"] >= current[0]:
            latest_company[ticker] = (row["fiscal_year"], row["company"])
    for row in financial_rows:
        row["company"] = latest_company[row["ticker"]][1]

    financial_rows.sort(key=lambda r: (r["ticker"], r["fiscal_year"]))
    audit_rows.sort(
        key=lambda r: (
            r["ticker"],
            r["fiscal_year"],
            VALUE_FIELDS.index(r["field"]),
            str(r["nomor_baris"]),
        )
    )

    with FINANCIALS_PATH.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FINANCIAL_FIELDS)
        writer.writeheader()
        for row in financial_rows:
            writer.writerow(
                {
                    key: format_number(row[key]) if key in VALUE_FIELDS else row[key]
                    for key in FINANCIAL_FIELDS
                }
            )

    with AUDIT_PATH.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=AUDIT_FIELDS)
        writer.writeheader()
        for row in audit_rows:
            writer.writerow(
                {
                    **row,
                    "nilai_mentah": (
                        row["nilai_mentah"]
                        if row["nilai_mentah"] == "AMBIGUOUS"
                        else format_number(row["nilai_mentah"])
                    ),
                }
            )

    print("SANITY CHECK")
    print(
        f"{'ticker':<7}{'year':<6}{'unit':<12}{'revenue':>20}{'cogs':>20}"
        f"{'receivables':>20}{'inventories':>20}{'payables':>20}"
        f"{'DSO':>8}{'DIO':>8}{'DPO':>8}  flag"
    )
    for row in financial_rows:
        revenue = row["revenue"]
        cogs = row["cogs"]
        receivables = row["trade_receivables"]
        inventories = row["inventories"]
        payables = row["trade_payables"]

        dso = receivables / revenue * 365 if revenue else None
        dio = inventories / cogs * 365 if cogs else None
        dpo = payables / cogs * 365 if cogs else None

        flags = []
        for field in VALUE_FIELDS:
            value = row[field]
            if value is not None and value < 0:
                flags.append(f"{field}<0")
        for name, value in [("DSO", dso), ("DIO", dio), ("DPO", dpo)]:
            if value is not None and (value < 0 or value > 365):
                flags.append(f"{name} out of range")
        flag_text = "OK" if not flags else "; ".join(flags)

        def fmt(value):
            return "" if value is None else f"{value:,.0f}"

        print(
            f"{row['ticker']:<7}{row['fiscal_year']:<6}{row['unit']:<12}"
            f"{fmt(revenue):>20}{fmt(cogs):>20}{fmt(receivables):>20}"
            f"{fmt(inventories):>20}{fmt(payables):>20}"
            f"{(dso if dso is not None else float('nan')):>8.1f}"
            f"{(dio if dio is not None else float('nan')):>8.1f}"
            f"{(dpo if dpo is not None else float('nan')):>8.1f}  {flag_text}"
        )

    print(f"\nWrote {FINANCIALS_PATH} ({len(financial_rows)} rows)")
    print(f"Wrote {AUDIT_PATH} ({len(audit_rows)} rows)")
    if warnings_list:
        print("\nWARNINGS")
        for warning in warnings_list:
            print(f"- {warning}")


if __name__ == "__main__":
    main()
