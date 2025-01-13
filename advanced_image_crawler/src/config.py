# src/config.py
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class CrawlerConfig:
    # Crawler configuration
    MAX_WORKERS = int(os.getenv('MAX_WORKERS', 10))
    DOWNLOAD_DIR = os.path.join(os.getcwd(), 'downloads')
    
    # Image processing config
    IMAGE_RESOLUTIONS = {
        'low': (0, 1280 * 720),
        'medium': (1280 * 720, 1920 * 1080),
        'high': (1920 * 1080, float('inf'))
    }
    
    # Logging config
    LOG_FILE = os.path.join(os.getcwd(), 'crawler.log')
    
    # Network config
    USER_AGENTS = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
    ]
    
    # Proxy settings
    PROXIES = []  # Can be populated dynamically