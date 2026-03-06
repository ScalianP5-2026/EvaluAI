FROM python:3.11-slim

WORKDIR /app


# Increase pip timeout for large package downloads
ENV PIP_DEFAULT_TIMEOUT=300
COPY backend/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY backend ./backend

ENV PYTHONPATH=/app

EXPOSE 8000

CMD ["/bin/sh", "-c", "uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 & sleep 5 && python backend/scripts/test_populate_supabase.py && wait %1"]
