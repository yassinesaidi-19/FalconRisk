{{ config(materialized='table') }}

select
  attempt_id,
  user_id,
  count(*) * 40 as risk_score,
  case
    when count(*) >= 3 then 'high'
    when count(*) = 2 then 'medium'
    else 'low'
  end as risk_band
from {{ ref('risk_signals') }}
group by 1,2