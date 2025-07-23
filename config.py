
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    """
    Konfigurasi aplikasi menggunakan Pydantic.
    Pengaturan dapat diambil dari environment variables atau file .env.
    """
    # URL dasar untuk endpoint KAI
    KAI_BASE_URL: str = "https://booking.kai.id"
    # Timeout permintaan HTTP (dalam detik)
    REQUEST_TIMEOUT: int = 60

    # Pengaturan cache: jumlah maksimum item dan TTL (detik)
    CACHE_MAX_SIZE: int = 128
    CACHE_TTL: int = 900

    # Level logging aplikasi (misal: DEBUG, INFO, WARNING, ERROR)
    LOG_LEVEL: str = "INFO"

    # Konfigurasi pemuatan dari file .env (jika tersedia)
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding='utf-8')

# Instance tunggal settings untuk diimpor oleh modul lain
settings = Settings()