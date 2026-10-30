import duckdb

DB_PATH = "wcr.duckdb"
OUT_PATH = "ccc_by_company_year.csv"

con = duckdb.connect(DB_PATH)
con.execute(
    f"COPY (SELECT * FROM ccc_by_company_year ORDER BY ticker, fiscal_year) "
    f"TO '{OUT_PATH}' (HEADER, DELIMITER ',')"
)
con.close()

print(f"Exported ccc_by_company_year to {OUT_PATH}")
