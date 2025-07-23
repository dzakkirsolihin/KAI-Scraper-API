
import cloudscraper
from bs4 import BeautifulSoup
import structlog
from cachetools import cached, TTLCache

from config import settings

# Logger aplikasi
logger = structlog.get_logger()

# Inisialisasi cache global untuk KAIScraper
cache = TTLCache(maxsize=settings.CACHE_MAX_SIZE, ttl=settings.CACHE_TTL)


class KAIScraper:
    """
    Scraper jadwal kereta KAI berbasis cloudscraper dan BeautifulSoup.
    Otomatis mengelola sesi dan cookies.
    """
    def __init__(self):
        self.scraper = cloudscraper.create_scraper(
            browser={'browser': 'chrome', 'platform': 'windows', 'mobile': False}
        )
        logger.info("Initializing session and getting cookies...")
        # Inisialisasi sesi dengan timeout dari konfigurasi
        self.scraper.get(settings.KAI_BASE_URL, timeout=settings.REQUEST_TIMEOUT)
        logger.info("Session initialized successfully.")

    @cached(cache)
    def _get_schedule_page_html(self, origin_code: str, destination_code: str, date_str: str) -> str:
        """
        Mendapatkan HTML hasil pencarian jadwal (2 langkah, otomatis follow redirect).
        Hasil fungsi ini di-cache.
        """
        search_params = {
            'origination': origin_code,
            'destination': destination_code,
            'tanggal': date_str,
            'adult': '1', 'infant': '0', 'submit': 'Cari+&+Pesan+Tiket'
        }
        log = logger.bind(params=search_params)
        log.info("Step 1: Sending initial search request")

        response_step1 = self.scraper.get(
            settings.KAI_BASE_URL,
            params=search_params,
            allow_redirects=True,
            timeout=settings.REQUEST_TIMEOUT
        )

        if response_step1.url.startswith(f"{settings.KAI_BASE_URL}/search"):
            log.info("Redirect followed automatically. Final page fetched.")
            return response_step1.text

        soup_step1 = BeautifulSoup(response_step1.text, 'lxml')
        meta_refresh = soup_step1.find("meta", attrs={"http-equiv": "refresh"})

        if not meta_refresh:
            raise ConnectionError("Failed to find redirect URL. KAI website might have changed.")

        redirect_url = meta_refresh['content'].split('url=')[1].strip("'\"")
        log.info("Step 2: Following redirect", url=redirect_url)

        response_step2 = self.scraper.get(redirect_url, timeout=settings.REQUEST_TIMEOUT)

        return response_step2.text

    def _parse_schedule_html(self, html_content: str, origin_code_req: str, destination_code_req: str) -> list:
        """
        Mengekstrak dan memvalidasi data jadwal dari HTML hasil pencarian.
        """
        soup = BeautifulSoup(html_content, 'lxml')
        schedules = []

        # Defensive: Ambil nama stasiun dari input field (jika ada)
        origin_input_flex = soup.find("input", {"name": "flexdatalist-origination"})
        origin_name_full = origin_input_flex.get('value', '').upper() if origin_input_flex else ''

        destination_input_flex = soup.find("input", {"name": "flexdatalist-destination"})
        destination_name_full = destination_input_flex.get('value', '').upper() if destination_input_flex else ''

        logger.info("Page header shows route", origin=origin_name_full, destination=destination_name_full)

        ticket_cards = soup.find_all("div", class_="data-block list-kereta")
        logger.info("Found potential ticket cards to check and parse", count=len(ticket_cards))

        for card in ticket_cards:
            try:
                # Validasi nama stasiun pada kartu tiket
                dep_station_div = card.find("div", class_="station-start")
                arr_station_div = card.find("div", class_="station-end")

                dep_station_name = dep_station_div.find(text=True, recursive=False).strip().upper() if dep_station_div else ''
                arr_station_name = arr_station_div.find(text=True, recursive=False).strip().upper() if arr_station_div else ''

                # Cek kecocokan nama stasiun kartu dengan input
                if origin_name_full not in dep_station_name and dep_station_name not in origin_name_full:
                    logger.warning("Skipping card. Mismatched origin", card_origin=dep_station_name, requested_origin=origin_name_full)
                    continue
                if destination_name_full not in arr_station_name and arr_station_name not in destination_name_full:
                    logger.warning("Skipping card. Mismatched destination", card_destination=arr_station_name, requested_destination=destination_name_full)
                    continue

                # Ambil data utama tiket
                train_name_div = card.find("div", class_="name")
                train_name = train_name_div.get_text(strip=True) if train_name_div else "N/A"

                price_div = card.find("div", class_="price")
                price = price_div.get_text(strip=True) if price_div else "N/A"

                dep_time_div = card.find("div", class_="time-start")
                arr_time_div = card.find("div", class_="time-end")
                departure_time = dep_time_div.get_text(strip=True) if dep_time_div else "N/A"
                arrival_time = arr_time_div.get_text(strip=True) if arr_time_div else "N/A"

                duration_div = card.find("div", class_="long-time")
                duration = duration_div.get_text(strip=True) if duration_div else "N/A"

                status_small = card.find("small", class_="sisa-kursi")
                status = status_small.get_text(strip=True) if status_small else "N/A"

                schedules.append({
                    "train_name": train_name,
                    "departure_time": departure_time,
                    "arrival_time": arrival_time,
                    "duration": duration,
                    "price": price,
                    "status": status
                })
            except Exception as e:
                logger.error("Error parsing a ticket card", error=str(e), exc_info=True)
                continue

        logger.info("Finished parsing. Found valid schedules", count=len(schedules))
        return schedules

    def search_schedule(self, origin: str, destination: str, date: str) -> list:
        """
        Fungsi publik utama untuk mencari jadwal kereta.
        """
        try:
            html_result = self._get_schedule_page_html(origin, destination, date)
            parsed_data = self._parse_schedule_html(html_result, origin, destination)
            return parsed_data
        except Exception as e:
            logger.error("An error occurred during scraping", error=str(e), exc_info=True)
            return []