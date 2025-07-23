
from datetime import datetime

# Mapping nomor bulan ke nama bulan Indonesia
NAMA_BULAN = {
    1: "Januari", 2: "Februari", 3: "Maret", 4: "April",
    5: "Mei", 6: "Juni", 7: "Juli", 8: "Agustus",
    9: "September", 10: "Oktober", 11: "November", 12: "Desember"
}

def format_date_for_kai(date_obj: datetime.date) -> str:
    """
    Format tanggal Python (date) ke format string yang digunakan situs KAI, contoh: 2025-07-25 → "25-Juli-2025"
    """
    day = date_obj.day
    month_name = NAMA_BULAN[date_obj.month]
    year = date_obj.year
    return f"{day}-{month_name}-{year}"