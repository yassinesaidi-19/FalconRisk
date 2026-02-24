import os
from sqlalchemy import create_engine
from dotenv import load_dotenv

load_dotenv()

def pg_engine():
    host = os.getenv("PG_HOST", "localhost")
    port = os.getenv("PG_PORT", "5432")
    db = os.getenv("PG_DB", "mena_payments")
    user = os.getenv("PG_USER", "mena")
    pwd = os.getenv("PG_PASSWORD", "mena")

    return create_engine(
        f"postgresql+psycopg2://{user}:{pwd}@{host}:{port}/{db}"
    )