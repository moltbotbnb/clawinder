FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy app as a package
COPY . /app/clawinder/

# Set PYTHONPATH
ENV PYTHONPATH=/app
ENV PORT=8000

# Expose port
EXPOSE 8000

# Run - use shell form to expand $PORT
CMD python -m uvicorn clawinder.main:app --host 0.0.0.0 --port $PORT
