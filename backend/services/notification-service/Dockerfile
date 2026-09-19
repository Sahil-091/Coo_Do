# Build context is backend/ for consistency with the other services,
# even though this one doesn't need db/ yet (see this service's README
# for which phase adds real DB access).
FROM python:3.12-slim
WORKDIR /app

COPY services/notification-service/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY services/notification-service/app ./app

ENV PYTHONPATH=/app
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
