select distinct
    unit,
    ticker,
    fiscal_year
from {{ ref('stg_financials') }}
where unit not in ('IDR full', 'IDR million')
