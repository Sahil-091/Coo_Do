# Build context is backend/ so the service can use only its own database
# tables while consuming core-api profile data through an internal API.
FROM python:3.12-slim
WORKDIR /app

COPY services/matching-service/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY db ./db
COPY services/matching-service/app ./app

ENV PYTHONPATH=/app
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
