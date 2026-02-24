{{ config(materialized='table') }}

select distinct
  merchant_id,
  country,
  city,
  category,
  onboarding_date
from bronze.merchants