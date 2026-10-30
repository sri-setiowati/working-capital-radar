select
    ticker,
    fiscal_year,
    revenue,
    cogs,
    trade_receivables,
    inventories,
    trade_payables
from {{ ref('stg_financials') }}
where revenue <= 0
   or cogs <= 0
   or trade_receivables < 0
   or inventories < 0
   or trade_payables < 0
