import os
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

load_dotenv()

PROJECT_ROOT = Path(__file__).resolve().parents[2]  # mena-payments-analytics/
DATA_DIR = PROJECT_ROOT / "data"

FILES = {
    "users": "users.parquet",
    "merchants": "merchants.parquet",
    "devices": "devices.parquet",
    "payment_attempts": "payment_attempts.parquet",
}


def get_engine():
    host = os.getenv("PG_HOST", "localhost")
    port = int(os.getenv("PG_PORT", "5432"))
    db = os.getenv("PG_DB", "mena_payments")
    user = os.getenv("PG_USER", "mena")
    pwd = os.getenv("PG_PASSWORD", "mena")

    url = f"postgresql+psycopg2://{user}:{pwd}@{host}:{port}/{db}"
    return create_engine(url, pool_pre_ping=True)


def ensure_bronze_schema(engine):
    with engine.begin() as conn:
        conn.execute(text("CREATE SCHEMA IF NOT EXISTS bronze;"))


def load_one(engine, table_name: str, parquet_name: str):
    path = DATA_DIR / parquet_name
    if not path.exists():
        print(f"[SKIP] {parquet_name} not found in {DATA_DIR}")
        return

    print(f"[LOAD] Reading {path}")
    df = pd.read_parquet(path)

    # Optional: normalize column names to snake_case
    df.columns = [c.strip().lower() for c in df.columns]

    print(f"[WRITE] bronze.{table_name} rows={len(df):,} cols={len(df.columns)}")
    df.to_sql(
        table_name,
        engine,
        schema="bronze",
        if_exists="replace",   # reproducible
        index=False,
        chunksize=50_000,
        method="multi",
    )


def main():
    engine = get_engine()
    ensure_bronze_schema(engine)

    for table, fname in FILES.items():
        load_one(engine, table, fname)

    print("[DONE] Loaded parquet files into Postgres schema: bronze")


if __name__ == "__main__":
    main()