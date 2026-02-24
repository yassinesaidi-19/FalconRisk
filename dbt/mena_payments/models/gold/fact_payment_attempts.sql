{{ config(materialized='table') }}

select
  attempt_id,
  attempt_ts,
  user_id,
  device_id,
  merchant_id,
  amount,
  currency,
  channel,
  status,
  failure_reason
from {{ ref('payment_attempts_clean') }}