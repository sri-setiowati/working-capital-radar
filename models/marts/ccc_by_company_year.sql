with base as (
    select
        company,
        ticker,
        fiscal_year,
        revenue,
        cogs,
        trade_receivables,
        inventories,
        trade_payables,
        revenue_bn,
        cogs_bn,
        trade_receivables_bn,
        inventories_bn,
        trade_payables_bn
    from {{ ref('stg_financials') }}
),

ratios as (
    select
        company,
        ticker,
        fiscal_year,
        trade_receivables / nullif(revenue, 0) * 365 as dso,
        inventories / nullif(cogs, 0) * 365 as dio,
        trade_payables / nullif(cogs, 0) * 365 as dpo,
        trade_receivables_bn + inventories_bn - trade_payables_bn as operating_wc_bn,
        trade_receivables_bn * 0.10 as cash_freed_dso_10pct_bn,
        inventories_bn * 0.10 as cash_freed_dio_10pct_bn
    from base
)

select
    company,
    ticker,
    fiscal_year,
    round(dso, 1) as dso,
    round(dio, 1) as dio,
    round(dpo, 1) as dpo,
    round(dso + dio - dpo, 1) as ccc_days,
    round(operating_wc_bn, 2) as operating_wc_bn,
    round(cash_freed_dso_10pct_bn, 2) as cash_freed_dso_10pct_bn,
    round(cash_freed_dio_10pct_bn, 2) as cash_freed_dio_10pct_bn
from ratios
