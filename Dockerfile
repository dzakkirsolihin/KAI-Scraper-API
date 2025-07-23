# Dockerfile

# --- Tahap 1: Base Image ---
FROM python:3.11-slim

# --- Konfigurasi Lingkungan ---
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# --- Siapkan Direktori Kerja ---
WORKDIR /app

# --- Instalasi Dependensi ---
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# --- Salin Kode Aplikasi ---
COPY . .

# --- Perintah untuk Menjalankan Aplikasi ---
CMD ["gunicorn", "-w", "4", "-k", "uvicorn.workers.UvicornWorker", "-b", "0.0.0.0:8000", "main:app"]
