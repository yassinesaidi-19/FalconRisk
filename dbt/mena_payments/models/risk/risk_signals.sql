{{ config(materialized='table') }}

with base as (
  select * from {{ ref('fact_payment_attempts') }}
),

user_avg as (
  select user_id, avg(amount) as avg_amount
  from base
  group by 1
),

velocity as (
  select
    p1.attempt_id,
    p1.user_id,
    'velocity_10min' as rule_name,
    count(p2.attempt_id)::int as txn_count_10min
  from base p1
  join base p2
    on p1.user_id = p2.user_id
   and p2.attempt_ts between p1.attempt_ts - interval '10 minutes' and p1.attempt_ts
  group by 1,2
  having count(p2.attempt_id) > 5
),

high_amount as (
  select
    f.attempt_id,
    f.user_id,
    'high_amount_deviation' as rule_name,
    null::int as txn_count_10min
  from base f
  join user_avg u on f.user_id = u.user_id
  where f.amount > u.avg_amount * 6
),

new_device_high_amount as (
  select
    f.attempt_id,
    f.user_id,
    'new_device_high_amount' as rule_name,
    null::int as txn_count_10min
  from base f
  join {{ ref('dim_device') }} d on f.device_id = d.device_id
  where d.first_seen > current_date - interval '7 days'
    and f.amount > 500
)

select * from velocity
union all
select * from high_amount
union all
select * from new_device_high_amount