FROM python:3.11-slim

WORKDIR /app

RUN pip install --no-cache-dir \
    pandas \
    pyarrow \
    psycopg2-binary \
    sqlalchemy \
    python-dotenv

CMD ["python", "-m", "src.loader.load_parquet_to_postgres"]