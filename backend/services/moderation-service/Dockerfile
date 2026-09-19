# Build context is backend/ so this service owns its moderation tables while
# calling safety-service and core-api through authenticated internal APIs.
FROM python:3.12-slim
WORKDIR /app

COPY services/moderation-service/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY db ./db
COPY services/moderation-service/app ./app

ENV PYTHONPATH=/app
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
