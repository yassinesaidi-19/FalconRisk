{{ config(materialized='table') }}

select distinct
  user_id,
  country,
  city,
  persona,
  signup_date,
  risk_profile
from bronze.users