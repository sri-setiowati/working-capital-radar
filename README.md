# Working Capital of Four IDX-Listed Building-Materials Companies, FY2022-2025

Sri Setiowati, October 2026

## The question

How long does each company wait to turn spending into cash, and where does the waiting come from: customers, inventory or suppliers? I measure it with the cash conversion cycle (CCC): days sales outstanding (DSO) plus days inventory outstanding (DIO) minus days payables outstanding (DPO). The four companies are ACES, ARNA, INTP and SMGR, using their consolidated annual statements.

## Short answer

Each company ties up cash in a different place. ACES holds it in inventory, ARNA in receivables from an affiliated distributor, INTP in a fairly even mix, and SMGR passes most of the burden to its suppliers.

| Company | DSO | DIO | DPO | CCC (days) |
| :-- | --: | --: | --: | --: |
| ACES | 6.2 | 256.0 | 13.0 | 249.2 |
| ARNA | 110.9 | 21.3 | 59.1 | 73.1 |
| INTP | 56.6 | 66.4 | 49.1 | 74.0 |
| SMGR | 58.9 | 63.7 | 101.6 | 21.0 |

FY2025, in days.

## What stands out

**ACES.** Customers pay almost at once, in 6 days, but stock sits for 256 days and suppliers are paid in 13. Ten percent less inventory would release about Rp 317 billion. Ten percent faster collection would release about Rp 15 billion. For a retailer like this, collection is not where the cash is stuck.

**SMGR and INTP.** Both collect in 57 to 59 days and hold stock for 64 to 66 days. SMGR's cycle is 21 days and INTP's is 74. The difference comes from payables: SMGR pays suppliers in 102 days, INTP in 49.

**ARNA.** Collection takes 111 days. In FY2023, 94% of trade receivables were owed by related parties and 78% by one distributor, which also bought 72% of net sales (audited statements, Notes 6 and 22). A collection period this long points to how much ARNA's sales depend on one affiliated distributor. Separately, inventory fell from Rp 254.5 billion in FY2023 to Rp 118.5 billion in FY2025, which took DIO from 60 to 21 days. I have not looked into the reason.

**INTP.** The cycle shortened from 92 to 74 days since FY2022, mostly through inventory: DIO went from 92 to 66 days.

## What a 10% improvement is worth

The rule is simple: 10% less receivables or 10% less inventory releases 10% of that balance. This is a scenario, not a forecast.

| Company | Faster collection (Rp billion) | Less inventory (Rp billion) |
| :-- | --: | --: |
| ACES | 14.7 | 317.2 |
| ARNA | 88.5 | 11.9 |
| INTP | 275.1 | 217.7 |
| SMGR | 568.9 | 491.4 |

## Method and checks

The data comes from the IDX annual financial statements in Excel, consolidated. For each company and year I use five items: net sales, cost of goods sold, trade receivables, inventories and trade payables, all at year-end, with a 365-day year. A dbt project on DuckDB loads the 16 company-years, runs six data tests and builds the table behind the dashboard. An audit file records the source sheet and row of every extracted number. ARNA's FY2022 and FY2023 figures were checked line by line against the audited FY2023 statements. ACES changed its name during the period and appears under its current name.

## Limits

Four companies are too few for sector averages. Year-end balances can distort seasonal businesses, a retailer in particular, and averages would be better. The related-party split was examined for ARNA FY2022-2023 only. This is an analysis of public information, not investment advice.
