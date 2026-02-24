FROM python:3.11-slim

WORKDIR /app

RUN pip install --no-cache-dir streamlit pandas psycopg2-binary python-dotenv

CMD ["streamlit", "run", "streamlit_app/app.py", "--server.address=0.0.0.0", "--server.port=8501"]