FROM python:3.12-slim

WORKDIR /app

# Primero copiamos solo las dependencias
# Esto permite que Docker cachee esta capa si requirements.txt no cambia
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Recién después copiamos el código fuente
COPY . .

EXPOSE 8000

CMD ["uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
