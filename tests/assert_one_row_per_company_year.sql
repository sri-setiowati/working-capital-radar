select
    ticker,
    fiscal_year,
    count(*) as row_count
from {{ ref('stg_financials') }}
group by ticker, fiscal_year
having count(*) > 1
