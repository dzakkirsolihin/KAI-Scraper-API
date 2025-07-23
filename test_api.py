
import pytest
import requests
from datetime import date, timedelta

# URL API lokal
BASE_URL = "http://127.0.0.1:8000"

# =====================
# Test endpoint root
# =====================
def test_root_endpoint():
    """Cek endpoint root (/) merespons dengan benar."""
    response = requests.get(f"{BASE_URL}/")
    assert response.status_code == 200
    assert response.json() == {"status": "KAI Ticket Checker API is running!"}
    print("\n[SUCCESS] Root endpoint test passed.")

# =====================
# Test endpoint /stations
# =====================
def test_get_all_stations():
    """Cek endpoint /stations mengembalikan semua stasiun."""
    print("\n[INFO] Testing GET /stations (all stations)...")
    response = requests.get(f"{BASE_URL}/stations")
    assert response.status_code == 200
    json_response = response.json()
    assert isinstance(json_response, list)
    assert len(json_response) > 100
    first_station = json_response[0]
    assert "code" in first_station
    assert "name" in first_station
    assert "city" in first_station
    assert "cityname" in first_station
    print(f"[SUCCESS] Get all stations test passed. Found {len(json_response)} stations.")

def test_search_stations_successful():
    """Cek pencarian stasiun dengan query berhasil."""
    search_query = "bandung"
    print(f"\n[INFO] Testing GET /stations?search={search_query}...")
    response = requests.get(f"{BASE_URL}/stations", params={"search": search_query})
    assert response.status_code == 200
    json_response = response.json()
    assert isinstance(json_response, list)
    for station in json_response:
        assert search_query in station["name"].lower() or \
               search_query in station["city"].lower() or \
               search_query in station["cityname"].lower()
    print(f"[SUCCESS] Search stations test passed. Found {len(json_response)} results for '{search_query}'.")

def test_search_stations_no_results():
    """Cek pencarian stasiun yang tidak ada hasilnya mengembalikan list kosong."""
    search_query = "kota_fiksi_xyz"
    print(f"\n[INFO] Testing GET /stations?search={search_query}...")
    response = requests.get(f"{BASE_URL}/stations", params={"search": search_query})
    assert response.status_code == 200
    json_response = response.json()
    assert isinstance(json_response, list)
    assert len(json_response) == 0
    print("[SUCCESS] Search with no results test passed.")

# =====================
# Test endpoint /search (termasuk validasi)
# =====================
def test_search_successful_with_valid_codes():
    """Cek pencarian jadwal dengan kode stasiun valid."""
    departure_date = date.today() + timedelta(days=45)
    date_str = departure_date.strftime("%Y-%m-%d")
    params = {
        'origin': 'GMR',
        'destination': 'BD',
        'departure_date': date_str
    }
    print(f"\n[INFO] Testing successful search for GMR -> BD on {date_str}...")
    response = requests.get(f"{BASE_URL}/search", params=params, timeout=60)
    assert response.status_code == 200
    json_response = response.json()
    assert isinstance(json_response, list)
    print("[SUCCESS] Successful search test with valid codes passed.")

def test_search_invalid_origin_code():
    """Cek pencarian dengan kode origin tidak valid (harus 400)."""
    departure_date = date.today() + timedelta(days=10)
    params = {'origin': 'XXX', 'destination': 'BD', 'departure_date': departure_date.strftime("%Y-%m-%d")}
    print("\n[INFO] Testing search with invalid origin code (XXX)...")
    response = requests.get(f"{BASE_URL}/search", params=params)
    assert response.status_code == 400
    assert "Invalid origin station code" in response.json().get("detail", "")
    print("[SUCCESS] Invalid origin code test passed (received 400 as expected).")

def test_search_invalid_destination_code():
    """Cek pencarian dengan kode destination tidak valid (harus 400)."""
    departure_date = date.today() + timedelta(days=10)
    params = {'origin': 'GMR', 'destination': 'YYY', 'departure_date': departure_date.strftime("%Y-%m-%d")}
    print("\n[INFO] Testing search with invalid destination code (YYY)...")
    response = requests.get(f"{BASE_URL}/search", params=params)
    assert response.status_code == 400
    assert "Invalid destination station code" in response.json().get("detail", "")
    print("[SUCCESS] Invalid destination code test passed (received 400 as expected).")

def test_search_same_origin_destination():
    """Cek pencarian dengan origin dan destination sama (harus 400)."""
    departure_date = date.today() + timedelta(days=10)
    params = {'origin': 'GMR', 'destination': 'GMR', 'departure_date': departure_date.strftime("%Y-%m-%d")}
    print("\n[INFO] Testing search with same origin and destination (GMR)...")
    response = requests.get(f"{BASE_URL}/search", params=params)
    assert response.status_code == 400
    assert "cannot be the same" in response.json().get("detail", "")
    print("[SUCCESS] Same origin/destination test passed (received 400 as expected).")

def test_search_invalid_date_format_remains():
    """Cek validasi format tanggal dari FastAPI (harus 422)."""
    params = {'origin': 'GMR', 'destination': 'BD', 'departure_date': '25-12-2025'}
    print("\n[INFO] Testing search with invalid date format...")
    response = requests.get(f"{BASE_URL}/search", params=params)
    assert response.status_code == 422
    print("[SUCCESS] Invalid date format test passed (received 422 as expected).")