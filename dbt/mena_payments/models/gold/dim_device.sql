{{ config(materialized='table') }}

select distinct
  device_id,
  user_id,
  device_type,
  first_seen
from bronze.devices