FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Create non-root user
RUN useradd -m appuser

COPY app/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY app/ /app/

EXPOSE 5000

USER appuser

# Production-ish server
# main:app => file main.py, Flask object named app
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "main:app"]