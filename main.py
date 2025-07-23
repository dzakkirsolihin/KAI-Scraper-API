
from fastapi import FastAPI, HTTPException, Response, status, Request, Depends, Query
from datetime import date
from typing import List, Optional
from pydantic import BaseModel, Field
import uuid
import structlog
import time
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from config import settings
from logging_config import setup_logging
from kai_scraper import KAIScraper
from utils import format_date_for_kai
from station_manager import station_manager

# Inisialisasi logging dan logger utama
setup_logging(log_level=settings.LOG_LEVEL)
logger = structlog.get_logger(__name__)

# Inisialisasi scheduler background
scheduler = AsyncIOScheduler()

# ====================
# Pydantic Models untuk dokumentasi dan validasi
# ====================
class Station(BaseModel):
    code: str = Field(..., description="Kode unik 3 huruf untuk stasiun.", example="GMR")
    name: str = Field(..., description="Nama lengkap stasiun.", example="GAMBIR")
    city: str = Field(..., description="Nama kota atau kabupaten stasiun.", example="GAMBIR")
    cityname: str = Field(..., description="Nama resmi kota/kabupaten.", example="JAKARTA")

class Schedule(BaseModel):
    train_name: str = Field(..., description="Nama kereta dan nomor KA.", example="ARGO BROMO ANGGREK (2)")
    departure_time: str = Field(..., description="Waktu keberangkatan (HH:MM).", example="08:20")
    arrival_time: str = Field(..., description="Waktu kedatangan (HH:MM).", example="17:15")
    duration: str = Field(..., description="Estimasi durasi perjalanan.", example="8j 55m")
    price: str = Field(..., description="Harga tiket yang diformat.", example="Rp 650.000,-")
    status: str = Field(..., description="Ketersediaan tiket.", example="Tersedia")

class ErrorDetail(BaseModel):
    detail: str

# ====================
# Deskripsi API (Markdown untuk dokumentasi Swagger)
# ====================
api_description = """
🚂 **API Pengecek Jadwal Kereta Api Indonesia**

API ini memungkinkan Anda untuk melakukan scraping jadwal kereta api dari situs resmi KAI.
Fitur utama:
*   ✅ **Pencarian Jadwal**: Temukan jadwal berdasarkan rute dan tanggal.
*   🚉 **Daftar Stasiun**: Dapatkan daftar lengkap stasiun beserta kodenya.
*   ⚡ **Caching**: Respons cepat untuk pencarian yang berulang.
*   🔄 **Update Otomatis**: Daftar stasiun diperbarui secara berkala.

Dibuat dengan FastAPI, Cloudscraper, dan Structlog.
"""

# ====================
# Inisialisasi FastAPI
# ====================
app = FastAPI(
    title="KAI Scraper API",
    description=api_description,
    version="1.2.1-documented",
    contact={
        "name": "Dzakwan Alifi",
        "url": "https://github.com/dzakwanalifi/kai-scraper-api",
        "email": "dzakwanalifi@apps.ipb.ac.id",
    },
    license_info={
        "name": "MIT License",
        "url": "https://opensource.org/licenses/MIT",
    },
)

# ====================
# Event Handler untuk scheduler update stasiun
# ====================
@app.on_event("startup")
async def startup_event():
    station_manager.update_station_list()
    scheduler.add_job(station_manager.update_station_list, 'interval', hours=24)
    scheduler.start()
    logger.info("Scheduler started. Station list will be updated periodically.")

@app.on_event("shutdown")
def shutdown_event():
    scheduler.shutdown()
    logger.info("Scheduler shut down.")

# ====================
# Middleware: inject request_id dan logging request
# ====================
@app.middleware("http")
async def logging_middleware(request: Request, call_next):
    structlog.contextvars.clear_contextvars()
    request_id = str(uuid.uuid4())
    structlog.contextvars.bind_contextvars(
        request_id=request_id,
        path=request.url.path,
        method=request.method,
        client_host=request.client.host
    )
    start_time = time.time()
    logger.info("Request started")
    response = await call_next(request)
    process_time = (time.time() - start_time) * 1000
    response.headers["X-Request-ID"] = request_id
    logger.info(
        "Request finished",
        status_code=response.status_code,
        process_time_ms=f"{process_time:.2f}"
    )
    return response

# ====================
# Endpoint: /stations (daftar stasiun, bisa search)
# ====================
@app.get(
    "/stations",
    response_model=List[Station],
    tags=["Stations"],
    summary="Dapatkan Daftar Stasiun Kereta Api",
    description="Mengembalikan daftar semua stasiun kereta api di Indonesia. Gunakan parameter `search` untuk memfilter hasil."
)
async def get_stations(
    search: Optional[str] = Query(None, description="Teks untuk mencari stasiun berdasarkan nama, kode, atau kota.", example="jakarta")
):
    if search:
        logger.info("Searching for stations", query=search)
        return station_manager.search_stations(search)
    logger.info("Fetching all stations")
    return station_manager.get_all_stations()

# ====================
# Dependency: validasi kode stasiun
# ====================
async def validate_station_codes(origin: str, destination: str):
    if not station_manager.is_valid_station(origin):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid origin station code: '{origin}'. Use the /stations endpoint to find valid codes."
        )
    if not station_manager.is_valid_station(destination):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid destination station code: '{destination}'. Use the /stations endpoint to find valid codes."
        )
    if origin.upper() == destination.upper():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Origin and destination cannot be the same."
        )
    return {"origin": origin, "destination": destination}

# ====================
# Endpoint: /search (cari jadwal kereta)
# ====================
@app.get(
    "/search",
    response_model=List[Schedule],
    tags=["Search"],
    summary="Cari Jadwal Kereta Api",
    description="Melakukan pencarian jadwal kereta berdasarkan stasiun asal, tujuan, dan tanggal keberangkatan.",
    responses={
        200: {"description": "Pencarian berhasil dan jadwal ditemukan."},
        400: {"model": ErrorDetail, "description": "Parameter input tidak valid (misal: kode stasiun salah)."},
        404: {"model": ErrorDetail, "description": "Tidak ada jadwal yang ditemukan untuk rute dan tanggal yang diminta."},
        422: {"description": "Error validasi (misal: format tanggal salah)."},
    }
)
async def search_tickets(
    response: Response,
    request: Request,
    validated_params: dict = Depends(validate_station_codes),
    departure_date: date = Query(..., description="Tanggal keberangkatan dalam format YYYY-MM-DD.", example="2025-12-25")
):
    """
    Cari jadwal kereta berdasarkan stasiun asal, tujuan, dan tanggal keberangkatan.
    Kode stasiun akan divalidasi sebelum melakukan scraping.
    """
    origin = validated_params["origin"]
    destination = validated_params["destination"]
    logger.info("Search endpoint called with valid station codes", origin=origin, destination=destination, date=str(departure_date))
    try:
        scraper = KAIScraper()
        kai_date_str = format_date_for_kai(departure_date)
        results = scraper.search_schedule(origin, destination, kai_date_str)

        if not isinstance(results, list):
            logger.error("Scraper returned a non-list type", type=str(type(results)))
            raise HTTPException(status_code=500, detail="Internal scraper error: unexpected data type returned.")

        if len(results) == 0:
            logger.warning("No valid schedules found. Returning 404.")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No schedules found for route {origin} to {destination} on {departure_date}."
            )
        logger.info("Successfully found schedules", count=len(results))
        return results

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Unhandled exception in /search endpoint", exc_info=True)
        raise HTTPException(status_code=500, detail="An unexpected internal server error occurred.")

# ====================
# Endpoint: root (cek status API)
# ====================
@app.get("/")
def read_root():
    return {"status": "KAI Ticket Checker API is running!"}