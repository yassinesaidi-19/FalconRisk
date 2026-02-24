{{ config(materialized='table') }}

select
  attempt_id,
  ts::timestamp as attempt_ts,
  user_id,
  device_id,
  merchant_id,
  amount::numeric(12,2) as amount,
  currency,
  channel,
  status,
  failure_reason
from bronze.payment_attempts