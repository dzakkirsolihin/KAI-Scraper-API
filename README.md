# 🚂 KAI Scraper API

Sebuah API tidak resmi yang andal dan cepat untuk melakukan scraping jadwal kereta api dari situs resmi Kereta Api Indonesia. Dibangun dengan Python, FastAPI, Cloudscraper, dan dilengkapi dengan caching serta update otomatis.

[![MIT License](https://img.shields.io/badge/License-MIT-green.svg)](https://choosealicense.com/licenses/mit/)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Framework](https://img.shields.io/badge/Framework-FastAPI-blueviolet)](https://fastapi.tiangolo.com/)

---


## ✨ Fitur Utama

- **Pencarian Jadwal**: Temukan jadwal kereta api berdasarkan stasiun asal, tujuan, dan tanggal.
- **Daftar Stasiun**: Akses daftar lengkap stasiun kereta api di Indonesia, lengkap dengan fitur pencarian.
- **Caching Cerdas**: Menggunakan cache in-memory (TTL 15 menit) untuk memberikan respons super cepat pada pencarian yang sama.
- **Update Otomatis**: Daftar stasiun diperbarui secara otomatis setiap 24 jam untuk menjaga data tetap relevan.
- **Validasi Input**: Validasi kode stasiun di awal untuk respons error yang cepat dan efisien.
- **Dokumentasi Interaktif**: Dokumentasi API yang digenerate secara otomatis dan interaktif menggunakan Swagger UI.
- **Logging Terstruktur**: Output log dalam format JSON dengan `request_id` untuk kemudahan debugging dan monitoring.
- **�️ Rate Limiting**: Melindungi API dari penyalahgunaan dengan batas permintaan 30 kali per menit.
- **📦 Siap Produksi dengan Docker**: Dilengkapi dengan `Dockerfile` dan `docker-compose.yml` untuk deployment yang mudah dan konsisten.


## 🚀 Menjalankan dengan Docker (Direkomendasikan)

Cara termudah dan paling konsisten untuk menjalankan API ini adalah menggunakan Docker.

1.  **Prasyarat:** Pastikan Anda telah menginstal [Docker Desktop](https://www.docker.com/products/docker-desktop/).

2.  **Clone repository ini:**
    ```bash
    git clone https://github.com/dzakwanalifi/kai-scraper-api.git
    cd kai-scraper-api
    ```

3.  **Bangun dan Jalankan Container:**
    Dari direktori root proyek, jalankan perintah berikut:
    ```bash
    docker-compose up --build
    ```
    Perintah ini akan membangun Docker image dan menjalankan container di latar belakang.

4.  **Akses API:**
    - Buka browser Anda dan pergi ke `http://localhost:8000`.
    - Untuk melihat dokumentasi interaktif, buka `http://localhost:8000/docs`.

5.  **Untuk Menghentikan:**
    Tekan `Ctrl + C` di terminal, lalu jalankan:
    ```bash
    docker-compose down
    ```

### Menjalankan Secara Lokal (Tanpa Docker)

Jika Anda tidak ingin menggunakan Docker, Anda masih bisa menjalankannya secara lokal.

1.  Ikuti langkah-langkah instalasi virtual environment dan `pip install -r requirements.txt` seperti biasa.
2.  Jalankan server development:
    ```bash
    uvicorn main:app --reload
    ```

## ⚙️ Endpoint API

### 1. Dapatkan Daftar Stasiun

Mengembalikan daftar stasiun. Sangat berguna untuk menemukan kode stasiun yang benar.

- **Endpoint:** `GET /stations`
- **Contoh Request (semua stasiun):**
  ```
  GET http://127.0.0.1:8000/stations
  ```
- **Contoh Request (dengan pencarian):**
  ```
  GET http://127.0.0.1:8000/stations?search=jakarta
  ```

### 2. Cari Jadwal Kereta

Melakukan pencarian jadwal kereta api.

- **Endpoint:** `GET /search`
- **Parameter:**
  - `origin` (string, wajib): Kode stasiun asal (misal: `GMR`).
  - `destination` (string, wajib): Kode stasiun tujuan (misal: `BD`).
  - `departure_date` (string, wajib): Tanggal keberangkatan format `YYYY-MM-DD`.
- **Contoh Request:**
  ```
  GET http://127.0.0.1:8000/search?origin=GMR&destination=BD&departure_date=2025-12-25
  ```
- **Contoh Respons Sukses (200 OK):**
  ```json
  [
    {
      "train_name": "ARGO PARAHYANGAN (44)",
      "departure_time": "06:30",
      "arrival_time": "09:15",
      "duration": "2j 45m",
      "price": "Rp 250.000,-",
      "status": "Tersedia"
    }
  ]
  ```
- **Contoh Respons Gagal (404 Not Found):**
  ```json
  {
    "detail": "No schedules found for route GMR to BD."
  }
  ```
  
## 🧪 Menjalankan Tes

Proyek ini dilengkapi dengan serangkaian tes menggunakan `pytest`.

```bash
pytest -v
```

## 📜 Lisensi

Proyek ini dilisensikan di bawah [Lisensi MIT](LICENSE).