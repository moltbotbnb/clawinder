FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . /app/clawinder/

ENV PYTHONPATH=/app

CMD ["sh", "-c", "python -m uvicorn clawinder.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
