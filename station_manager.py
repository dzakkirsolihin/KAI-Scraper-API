
import json
from pathlib import Path
import structlog
from typing import List, Dict, Optional

from config import settings
from kai_scraper import KAIScraper

logger = structlog.get_logger()
STATIONS_FILE = Path("stations.json")

class StationManager:
    """
    Manajer data stasiun: memuat, mencari, validasi, dan update data stasiun KAI.
    """
    def __init__(self):
        self._stations: List[Dict] = []
        self._station_codes: set = set()
        self.load_stations()

    def load_stations(self):
        """
        Memuat daftar stasiun dari file JSON lokal. Jika file tidak ada atau rusak, akan mencoba update otomatis.
        """
        if not STATIONS_FILE.exists():
            logger.warn("stations.json not found. Attempting to fetch it now.")
            self.update_station_list()
        else:
            try:
                with open(STATIONS_FILE, "r") as f:
                    self._stations = json.load(f)
                self._station_codes = {s["code"] for s in self._stations}
                logger.info("Successfully loaded stations from file.", count=len(self._stations))
            except (json.JSONDecodeError, KeyError) as e:
                logger.error("Failed to load or parse stations.json. Refetching.", error=str(e))
                self.update_station_list()

    def get_all_stations(self) -> List[Dict]:
        """
        Mengembalikan seluruh data stasiun yang tersedia.
        """
        return self._stations

    def search_stations(self, query: str) -> List[Dict]:
        """
        Cari stasiun berdasarkan nama, kode, atau nama kota/kabupaten (case-insensitive).
        """
        query = query.lower()
        return [
            s for s in self._stations
            if query in s["name"].lower() or
               query in s["code"].lower() or
               query in s["cityname"].lower()
        ]

    def is_valid_station(self, code: str) -> bool:
        """
        Cek apakah kode stasiun valid (ada di data).
        """
        return code.upper() in self._station_codes

    def update_station_list(self):
        """
        Mengambil daftar stasiun terbaru dari API KAI dan menyimpannya ke file lokal.
        Fungsi ini dipanggil periodik oleh scheduler.
        """
        logger.info("Attempting to fetch latest station list from KAI...")
        try:
            # Gunakan session dari KAIScraper yang sudah "di-pemanasan"
            scraper_session = KAIScraper().scraper
            stations_url = f"{settings.KAI_BASE_URL}/api/stations2"
            response = scraper_session.post(stations_url, timeout=settings.REQUEST_TIMEOUT)
            response.raise_for_status()
            new_stations = response.json()
            if not isinstance(new_stations, list) or not all("code" in s and "name" in s for s in new_stations):
                logger.error("Fetched station data is not in the expected format.")
                return
            with open(STATIONS_FILE, "w", encoding='utf-8') as f:
                json.dump(new_stations, f, indent=2, ensure_ascii=False)
            self._stations = new_stations
            self._station_codes = {s["code"].upper() for s in self._stations}
            logger.info("Successfully updated and saved new station list.", count=len(self._stations))
        except Exception as e:
            logger.error("Failed to update station list.", error=str(e), exc_info=True)

# Instance global yang digunakan aplikasi
station_manager = StationManager()