# limiter.py

from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

# Inisialisasi Limiter. 
# get_remote_address akan menggunakan alamat IP klien sebagai kunci unik.
limiter = Limiter(key_func=get_remote_address)
