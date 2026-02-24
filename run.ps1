docker compose up -d
docker compose run --rm loader
docker compose run --rm dbt run --full-refresh
docker compose run --rm dbt test

Write-Host "Pipeline complete ✅"