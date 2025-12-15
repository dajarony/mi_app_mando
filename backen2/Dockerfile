# Dockerfile para Core SUME Observabilidad
FROM python:3.13-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["uvicorn", "core2.core_dajarony.entradas.api_app:app", "--host", "0.0.0.0", "--port", "8080"]
