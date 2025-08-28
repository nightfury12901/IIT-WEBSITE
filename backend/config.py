import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'scholar-api-secret-key-2024-abhishek-dixit'

    DEBUG = os.environ.get('DEBUG', 'False').lower() == 'true'
    SCHOLAR_ID = 'CjJ84BwAAAAJ' 
    CACHE_TTL = 3600  
    MAX_PUBLICATIONS = 50 
    REQUEST_TIMEOUT = 120
