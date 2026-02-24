{{ config(materialized='view') }}

select
  attempt_id,
  user_id,
  string_agg(rule_name, ', ' order by rule_name) as triggered_rules,
  count(*) as rule_count
from {{ ref('risk_signals') }}
group by 1,2