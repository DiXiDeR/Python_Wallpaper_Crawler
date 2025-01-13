import os
import logging
import asyncio
import requests
import aiohttp
import tkinter as tk
from tkinter import messagebox
from urllib.parse import urlparse
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from PIL import Image
from io import BytesIO
from dataclasses import dataclass
from typing import Optional, List, Set
from collections import deque
import threading
import time
import imagesize
import magic

# Konfigurace
OUTPUT_DIR = "Obtained_Images"
RESOLUTIONS = {
    "4K": {"width": 3840, "height": 2160},
    "2K": {"width": 2560, "height": 1440},
    "FullHD": {"width": 1920, "height": 1080},
}

@dataclass
class ImageInfo:
    url: str
    width: int
    height: int
    mime: str

class WallpaperCrawler:
    def __init__(self):
        self.setup_logging()
        self.setup_gui()

    def setup_logging(self):
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(levelname)s - %(message)s",
            handlers=[
                logging.FileHandler("crawler.log"),
                logging.StreamHandler(),
            ],
        )
        self.logger = logging.getLogger(__name__)

    def setup_gui(self):
        self.root = tk.Tk()
        self.root.title("Wallpaper Crawler")
        self.root.geometry("500x400")

        # URL Input
        tk.Label(self.root, text="Enter Website URL:").pack(pady=10)
        self.url_entry = tk.Entry(self.root, width=50)
        self.url_entry.pack(pady=10)

        # Resolution Selection
        self.resolution_var = tk.StringVar(value="ALL")
        tk.Label(self.root, text="Select Resolution:").pack()
        for res in ["4K", "2K", "FullHD", "ALL"]:
            tk.Radiobutton(self.root, text=res, variable=self.resolution_var, value=res).pack()

        # Start Button
        self.start_button = tk.Button(self.root, text="Start Crawling", command=self.start_crawl)
        self.start_button.pack(pady=20)

        # Results Display
        self.results_text = tk.Text(self.root, height=10, width=60)
        self.results_text.pack(pady=10)

        # Control variables
        self.crawling = False
        self.stop_event = threading.Event()

    def start_crawl(self):
        if self.crawling:
            return

        url = self.url_entry.get()
        resolution = self.resolution_var.get()

        if not url.startswith("http"):
            messagebox.showerror("Error", "Invalid URL")
            return

        self.crawling = True
        self.stop_event.clear()
        self.start_button.config(state=tk.DISABLED)

        self.crawl_thread = threading.Thread(target=self.perform_crawl, args=(url, resolution))
        self.crawl_thread.start()

    def perform_crawl(self, url, resolution):
        try:
            driver = self.create_browser()
            discovered_urls = set()
            queue = deque([(url, 0)])
            max_depth = 3  # Omezení hloubky crawlování

            while queue and not self.stop_event.is_set():
                current_url, current_depth = queue.popleft()

                if current_depth > max_depth:
                    continue

                if current_url in discovered_urls:
                    continue

                discovered_urls.add(current_url)
                self.logger.info(f"Crawling: {current_url}")

                try:
                    driver.get(current_url)
                    time.sleep(2)  # Wait for page load

                    # Process images
                    images = driver.find_elements(By.TAG_NAME, "img")
                    for img in images:
                        try:
                            img_url = img.get_attribute("src")
                            if img_url and img_url.startswith(('http', 'https')) and self.is_valid_image(img_url, resolution):
                                self.download_image(img_url, resolution)
                        except Exception as img_error:
                            self.logger.error(f"Error processing image: {img_error}")

                    # Discover new URLs
                    links = driver.find_elements(By.TAG_NAME, "a")
                    for link in links:
                        try:
                            href = link.get_attribute("href")
                            if href and urlparse(href).netloc == urlparse(url).netloc:
                                queue.append((href, current_depth + 1))
                        except Exception as link_error:
                            self.logger.error(f"Error processing link: {link_error}")

                except Exception as e:
                    self.logger.error(f"Error crawling {current_url}: {e}")

            driver.quit()

        except Exception as e:
            self.logger.critical(f"Crawl failed: {e}")
            messagebox.showerror("Crawl Error", str(e))

        self.crawling = False
        self.start_button.config(state=tk.NORMAL)

    def create_browser(self):
        options = webdriver.ChromeOptions()
        return webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

    def is_valid_image(self, img_url, resolution):
        try:
            image_info = self.get_image_info(img_url)
            if not image_info:
                return False

            width = image_info.width
            height = image_info.height

            if resolution == "4K":
                return width >= 3840 and height >= 2160
            elif resolution == "2K":
                return width >= 2560 and height >= 1440
            elif resolution == "FullHD":
                return width >= 1920 and height >= 1080
            elif resolution == "ALL":
                return True
            else:
                return False

        except Exception as e:
            self.logger.error(f"Error validating image {img_url}: {str(e)}")
            return False

    def get_image_info(self, img_url) -> Optional[ImageInfo]:
        try:
            response = requests.get(img_url, timeout=5)
            if response.status_code != 200:
                return None

            content = response.content
            mime = magic.from_buffer(content, mime=True)
            
            # Použití PIL pro zjištění rozměrů
            with Image.open(BytesIO(content)) as img:
                width, height = img.size

            return ImageInfo(url=img_url, width=width, height=height, mime=mime)

        except Exception as e:
            self.logger.error(f"Error getting image info {img_url}: {str(e)}")
            return None

    def download_image(self, img_url, resolution):
        try:
            response = requests.get(img_url)
            if response.status_code == 200:
                os.makedirs(OUTPUT_DIR, exist_ok=True)
                filename = os.path.join(OUTPUT_DIR, os.path.basename(img_url))
                with open(filename, "wb") as f:
                    f.write(response.content)
                self.logger.info(f"Downloaded image: {filename}")

        except Exception as e:
            self.logger.error(f"Failed to download image {img_url}: {e}")

    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    crawler = WallpaperCrawler()
    crawler.run()