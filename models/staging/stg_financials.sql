with source as (
    select *
    from {{ ref('financials') }}
)

select
    company,
    upper(ticker) as ticker,
    fiscal_year,
    revenue,
    cogs,
    trade_receivables,
    inventories,
    trade_payables,
    unit,
    case
        when unit = 'IDR full' then revenue / 1e9
        when unit = 'IDR million' then revenue / 1e3
    end as revenue_bn,
    case
        when unit = 'IDR full' then cogs / 1e9
        when unit = 'IDR million' then cogs / 1e3
    end as cogs_bn,
    case
        when unit = 'IDR full' then trade_receivables / 1e9
        when unit = 'IDR million' then trade_receivables / 1e3
    end as trade_receivables_bn,
    case
        when unit = 'IDR full' then inventories / 1e9
        when unit = 'IDR million' then inventories / 1e3
    end as inventories_bn,
    case
        when unit = 'IDR full' then trade_payables / 1e9
        when unit = 'IDR million' then trade_payables / 1e3
    end as trade_payables_bn,
    source_file,
    source_page
from source
