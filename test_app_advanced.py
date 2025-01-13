import os
import re
import logging
import asyncio
import aiohttp
import tkinter as tk
from tkinter import messagebox, filedialog
from urllib.parse import urljoin, urlparse
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from PIL import Image
from io import BytesIO
from dataclasses import dataclass
from typing import Optional, List, Set, Dict
from collections import deque
import threading
import time
import requests
import magic
import numpy as np
import cv2
import imagehash

# Pokročilá konfigurace detekce obrázků
class AdvancedImageDetector:
    @staticmethod
    def is_high_resolution(image_path: str, min_width: int = 3840, min_height: int = 2160) -> bool:
        """
        Pokročilá detekce rozlišení obrazku
        """
        try:
            with Image.open(image_path) as img:
                width, height = img.size
                return width >= min_width and height >= min_height
        except Exception as e:
            logging.error(f"Resolution detection error: {e}")
            return False

    @staticmethod
    def detect_image_quality(image_path: str) -> Dict[str, float]:
        """
        Detekce kvality obrazku pomoci pocitacoveho videni
        """
        try:
            img = cv2.imread(image_path)
            
            # Detekce ostrosti
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            fm = cv2.variance_of_laplacian(gray)
            
            # Detekce kontrastu
            contrast = np.std(gray)
            
            # Detekce barevnosti
            hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
            color_variance = np.std(hsv[:,:,1])
            
            return {
                "sharpness": fm,
                "contrast": contrast,
                "color_variance": color_variance
            }
        except Exception as e:
            logging.error(f"Image quality detection error: {e}")
            return {}

    @staticmethod
    def detect_similar_images(image_path: str, threshold: int = 5) -> List[str]:
        """
        Detekce podobnych obrazku pomoci hash funkce
        """
        try:
            hash_value = imagehash.phash(Image.open(image_path))
            
            similar_images = []
            for existing_image in os.listdir('Obtained_Images'):
                existing_path = os.path.join('Obtained_Images', existing_image)
                existing_hash = imagehash.phash(Image.open(existing_path))
                
                if hash_value - existing_hash < threshold:
                    similar_images.append(existing_path)
            
            return similar_images
        except Exception as e:
            logging.error(f"Similar image detection error: {e}")
            return []

class AdvancedWebCrawler:
    def __init__(self):
        # Konfigurace webdriveru
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        
        self.driver = webdriver.Chrome(
            service=Service(ChromeDriverManager().install()), 
            options=chrome_options
        )
        
        # Pokročilé strategie vyhledávání
        self.image_selectors = [
            "img[src*='4k']",
            "img[src*='high-res']", 
            "img[src*='highres']",
            "img[class*='high-resolution']",
            "img[data-src*='4k']",
            "div[style*='background-image']"
        ]
        
        # Regex pro detekci URL obrázků
        self.image_url_patterns = [
            r'https?://.*\.(jpg|jpeg|png|gif|bmp|webp).*4k',
            r'https?://.*\.(jpg|jpeg|png|gif|bmp|webp).*highres',
            r'https?://.*\.(jpg|jpeg|png|gif|bmp|webp).*\d{4}x\d{4}'
        ]

    def find_hidden_images(self, url: str) -> List[str]:
        """
        Pokročilé vyhledávání skrytých obrázků
        """
        hidden_images = []
        
        try:
            self.driver.get(url)
            
            # Dynamické vyhledávání pomocí ruznych selektoru
            for selector in self.image_selectors:
                images = self.driver.find_elements(By.CSS_SELECTOR, selector)
                for img in images:
                    try:
                        # Extrakce URL z ruznych atributu
                        src = img.get_attribute('src') or \
                              img.get_attribute('data-src') or \
                              img.get_attribute('style')
                        
                        if src:
                            # Extrakce URL z background-image
                            if 'background-image' in src:
                                src = re.findall(r'url\([\'"]?([^\'"]+)[\'"]?\)', src)
                                src = src[0] if src else None
                            
                            if src and self._validate_image_url(src):
                                hidden_images.append(src)
                    except Exception as e:
                        logging.warning(f"Image extraction error: {e}")
            
            # Hledání pomocí regulárních výrazů
            page_source = self.driver.page_source
            for pattern in self.image_url_patterns:
                matches = re.findall(pattern, page_source, re.IGNORECASE)
                hidden_images.extend(matches)
        
        except Exception as e:
            logging.error(f"Hidden image search error: {e}")
        
        return list(set(hidden_images))

    def _validate_image_url(self, url: str) -> bool:
        """
        Validace URL obrázku
        """
        try:
            # Kontrola URL, velikosti, přípony
            return (
                url.startswith(('http', 'https')) and
                any(url.lower().endswith(ext) for ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp']) and
                len(url) < 500
            )
        except Exception as e:
            logging.warning(f"URL validation error: {e}")
            return False

    def download_image(self, url: str, output_dir: str = 'Obtained_Images') -> Optional[str]:
        """
        Stažení a uložení obrázku s pokročilou validací
        """
        try:
            response = requests.get(url, timeout=10)
            
            if response.status_code != 200:
                return None
            
            # Kontrola MIME typu
            content_type = response.headers.get('content-type', '')
            if not content_type.startswith('image/'):
                return None
            
            # Uložení obrázku
            os.makedirs(output_dir, exist_ok=True)
            filename = os.path.join(output_dir, os.path.basename(url))
            
            with open(filename, 'wb') as f:
                f.write(response.content)
            
            # Pokročilá analýza obrázku
            if self.is ```python
            high_resolution(filename):
                quality_metrics = AdvancedImageDetector.detect_image_quality(filename)
                similar_images = AdvancedImageDetector.detect_similar_images(filename)
                logging.info(f"Downloaded high-resolution image: {filename}, Quality Metrics: {quality_metrics}, Similar Images: {similar_images}")
            else:
                logging.info(f"Downloaded image is not high-resolution: {filename}")

            return filename

        except Exception as e:
            logging.error(f"Error downloading image {url}: {e}")
            return None

    def perform_crawl(self, url: str):
        """
        Hlavní metoda pro provedení crawlování
        """
        try:
            hidden_images = self.find_hidden_images(url)
            for img_url in hidden_images:
                self.download_image(img_url)

        except Exception as e:
            logging.critical(f"Crawl failed: {e}")

    def close(self):
        """
        Ukončení webdriveru
        """
        self.driver.quit()

# Příklad použití
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    crawler = AdvancedWebCrawler()
    crawler.perform_crawl("https://www.example.com")
    crawler.close()