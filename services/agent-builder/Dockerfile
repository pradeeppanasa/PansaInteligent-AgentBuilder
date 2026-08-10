FROM python:3.11-slim

WORKDIR /app

COPY services/agent-builder/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY shared /app/shared
COPY services/agent-builder/app /app/app

ENV PYTHONPATH=/app:/app/shared

EXPOSE 8001

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8001"]
