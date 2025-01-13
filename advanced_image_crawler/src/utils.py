# src/utils.py
import os
import hashlib
import logging
from typing import Optional

def generate_unique_filename(url: str, base_dir: str) -> str:
    """
    Generate a unique filename based on URL hash
    
    Args:
        url (str): Source URL of the image
        base_dir (str): Base directory for saving
    
    Returns:
        str: Full path to the unique filename
    """
    # Create downloads directory if it doesn't exist
    os.makedirs(base_dir, exist_ok=True)
    
    # Generate hash of the URL
    url_hash = hashlib.md5(url.encode()).hexdigest()
    
    # Create unique filename
    filename = f"{url_hash}.jpg"
    return os.path.join(base_dir, filename)

def setup_logging(log_file: Optional[str] = None):
    """
    Configure logging for the application
    
    Args:
        log_file (Optional[str]): Path to log file
    """
    logging_config = {
        'level': logging.INFO,
        'format': '%(asctime)s - %(levelname)s: %(message)s',
        'datefmt': '%Y-%m-%d %H:%M:%S'
    }
    
    if log_file:
        logging_config['filename'] = log_file
    
    logging.basicConfig(**logging_config)