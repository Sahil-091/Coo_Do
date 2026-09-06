# Build context is backend/ (see docker-compose.yml) so this can reach
# the shared db/ package as well as its own service code.
FROM python:3.12-slim
WORKDIR /app

COPY services/safety-service/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY db ./db
COPY services/safety-service/app ./app

ENV PYTHONPATH=/app
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
