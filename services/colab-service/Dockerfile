FROM python:3.11-slim

# Establecer directorio de trabajo
WORKDIR /app

# Actualizar pip
RUN pip install --upgrade pip

COPY requirements.txt ./
RUN apt-get update && apt-get install -y build-essential python3-dev libglib2.0-0 libsm6 libxrender1 libxext6 && rm -rf /var/lib/apt/lists/*
RUN pip install --no-cache-dir -r requirements.txt

COPY src/ ./src/

# Crear directorio de almacenamiento
RUN mkdir -p /app/storage

# Crear usuario no root
RUN useradd --create-home --shell /bin/bash app \
    && chown -R app:app /app
USER app

# Exponer puerto
EXPOSE 8004

# Variables de entorno
ENV HOST=0.0.0.0
ENV PORT=8004
ENV DEBUG=true

# Comando para ejecutar la aplicación
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8004"]