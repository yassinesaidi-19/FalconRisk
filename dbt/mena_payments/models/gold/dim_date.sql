{{ config(materialized='table') }}

select distinct
  attempt_ts::date as date,
  extract(year from attempt_ts) as year,
  extract(month from attempt_ts) as month,
  extract(day from attempt_ts) as day,
  extract(dow from attempt_ts) as day_of_week
from {{ ref('payment_attempts_clean') }}