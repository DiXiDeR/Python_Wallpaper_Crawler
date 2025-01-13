import os
import json
import logging
import csv
import random
import imagesize
import filetype
import magic
import aiohttp
import asyncio
import aiofiles
import hashlib
import tkinter as tk
from tkinter import messagebox, filedialog
from typing import Dict, Set, List, Optional, NamedTuple
from contextlib import asynccontextmanager
from datetime import datetime
from dataclasses import dataclass, field
from selenium import webdriver
from asyncio import Semaphore
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from urllib.parse import urlparse
import requests
from PIL import Image
from io import BytesIO
from collections import deque
from aiohttp import ClientTimeout
from tqdm import tqdm
import threading
import time
from logging.handlers import RotatingFileHandler
from typing import Set, List, Tuple, Optional, Dict
from dataclasses import dataclass


@dataclass
class ImageInfo:
    width: int
    height: int
    mime: str
    url: str
    resolution_category: str = None  # Přidáno pro lepší kategorizaci
    hash: str = None  # Pro detekci duplicit


# Konstanty a konfigurace
RESOLUTIONS = {
    "4K": {
        "width": 3840,
        "height": 2160,
        "patterns": ["4k", "2160p", "3840x2160", "4096x2160", "uhd"],
    },
    "2K": {
        "width": 2560,
        "height": 1440,
        "patterns": ["2k", "1440p", "2560x1440", "qhd", "wqhd"],
    },
    "FullHD": {
        "width": 1920,
        "height": 1080,
        "patterns": ["fullhd", "1080p", "1920x1080", "fhd"],
    },
}

OUTPUT_STRUCTURE = {
    "base_dir": "Obtained_Images",
    "logs_dir": "logs",
    "data_dir": "data",
}


class CrawlerMetrics:
    def __init__(self):
        self.start_time = datetime.now()
        self.processed_urls = 0
        self.downloaded_images = 0
        self.failed_downloads = 0
        self.total_bytes = 0
    
    def update(self, bytes_downloaded: int = 0, success: bool = True):
        self.processed_urls += 1
        if success:
            self.downloaded_images += 1
            self.total_bytes += bytes_downloaded
        else:
            self.failed_downloads += 1
    
    @property
    def stats(self) -> Dict:
        duration = (datetime.now() - self.start_time).total_seconds()
        return {
            "duration": duration,
            "processed_urls": self.processed_urls,
            "downloaded_images": self.downloaded_images,
            "failed_downloads": self.failed_downloads,
            "total_mb": self.total_bytes / (1024 * 1024),
            "mb_per_second": (self.total_bytes / duration) / (1024 * 1024) if duration > 0 else 0
        }

class ImageProcessor:
    def __init__(self):
        self.seen_hashes: Set[str] = set()
    
    def get_image_hash(self, content: bytes) -> str:
        return hashlib.md5(content).hexdigest()
    
    def is_duplicate(self, content: bytes) -> bool:
        img_hash = self.get_image_hash(content)
        if img_hash in self.seen_hashes:
            return True
        self.seen_hashes.add(img_hash)
        return False

class ResourceManager:
    def __init__(self, max_concurrent: int = 5):
        self.semaphore = asyncio.Semaphore(max_concurrent)
        self.session: Optional[aiohttp.ClientSession] = None
    
    async def get_session(self) -> aiohttp.ClientSession:
        if self.session is None or self.session.closed:
            timeout = ClientTimeout(total=30)
            self.session = aiohttp.ClientSession(timeout=timeout)
        return self.session
    
    @asynccontextmanager
    async def request(self, url: str):
        async with self.semaphore:
            session = await self.get_session()
            try:
                async with session.get(url) as response:
                    yield response
            except Exception as e:
                logging.error(f"Request failed for {url}: {e}")
                raise

    async def close(self):
        if self.session and not self.session.closed:
            await self.session.close()

class ImageAnalyzer:
    def __init__(self, logger):
        self.logger = logger
        self._setup_dirs()

    def _setup_dirs(self):
        for dir_name in OUTPUT_STRUCTURE.values():
            os.makedirs(dir_name, exist_ok=True)

    async def analyze_image(self, img_url: str) -> Optional[ImageInfo]:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(img_url) as response:
                    if response.status != 200:
                        return None

                    content = await response.read()
                    mime = magic.from_buffer(content, mime=True)

                    if not mime.startswith("image/"):
                        return None

                    try:
                        width, height = imagesize.get_size_from_bytes(content)
                    except:
                        try:
                            img = Image.open(BytesIO(content))
                            width, height = img.size
                        except Exception as e:
                            self.logger.error(f"Failed to get image size: {e}")
                            return None

                    return ImageInfo(width=width, height=height, mime=mime, url=img_url)

        except Exception as e:
            self.logger.error(f"Error analyzing image {img_url}: {str(e)}")
            return None


class DataCollector:
    def __init__(self, base_dir: str):
        self.base_dir = base_dir
        os.makedirs(base_dir, exist_ok=True)
        self.endpoints: Set[str] = set()
        self.subdomains: Set[str] = set()

    def add_url(self, url: str):
        parsed = urlparse(url)
        self.subdomains.add(parsed.netloc)
        self.endpoints.add(parsed.path)

    def save_data(self):
        timestamp = time.strftime("%Y%m%d_%H%M%S")

        # Save endpoints
        with open(
            os.path.join(self.base_dir, f"endpoints_{timestamp}.csv"), "w", newline=""
        ) as f:
            writer = csv.writer(f)
            writer.writerow(["Endpoint"])
            writer.writerows([[endpoint] for endpoint in sorted(self.endpoints)])

        # Save subdomains
        with open(
            os.path.join(self.base_dir, f"subdomains_{timestamp}.csv"), "w", newline=""
        ) as f:
            writer = csv.writer(f)
            writer.writerow(["Subdomain"])
            writer.writerows([[subdomain] for subdomain in sorted(self.subdomains)])
            
class ProxyManager: #TODO: proxy rotation
    def __init__(self, proxy_file='proxies.json'):
        with open(proxy_file, 'r') as f:
            self.proxy_data = json.load(f)
        self.user_agents = self.proxy_data['user_agents']
    
    def get_random_user_agent(self):
        return random.choice(self.user_agents)


class WallpaperCrawler:
    def __init__(self):
        # Setup advanced logging
        self.setup_logging()
        self.metrics = CrawlerMetrics()
        self.image_processor = ImageProcessor()
        self.resource_manager = ResourceManager(max_concurrent=5)

        # Initialize Proxy Manager
        self.proxy_manager = ProxyManager()
        self.semaphore = Semaphore(5)  # Max 5 současných stahování

        # Initialize main GUI
        self.root = tk.Tk()
        self.root.title("Advanced Wallpaper Crawler")
        self.root.geometry("600x500")

        # URL Input
        tk.Label(self.root, text="Enter Website URL:").pack(pady=10)
        self.url_entry = tk.Entry(self.root, width=60)
        self.url_entry.pack(pady=10)

        # Resolution Selection
        self.resolution_var = tk.StringVar(value="ALL")
        tk.Label(self.root, text="Select Resolution:").pack()
        resolutions = ["4K", "2K", "FullHD", "ALL"]
        for res in resolutions:
            tk.Radiobutton(
                self.root, text=res, variable=self.resolution_var, value=res
            ).pack()

        # Depth and Timeout Controls
        tk.Label(self.root, text="Crawl Depth (1-5):").pack()
        self.depth_var = tk.IntVar(value=3)
        tk.Scale(
            self.root, from_=1, to=5, orient=tk.HORIZONTAL, variable=self.depth_var
        ).pack()

        # Timeout Control
        tk.Label(self.root, text="Request Timeout (seconds):").pack()
        self.timeout_var = tk.IntVar(value=10)
        tk.Scale(
            self.root, from_=5, to=30, orient=tk.HORIZONTAL, variable=self.timeout_var
        ).pack()

        # Start, Pause, and Stop Buttons
        self.start_button = tk.Button(
            self.root, text="Start Advanced Crawling", command=self.start_crawl
        )
        self.start_button.pack(pady=10)

        self.pause_button = tk.Button(
            self.root,
            text="Pause Crawling",
            command=self.pause_crawl,
            state=tk.DISABLED,
        )
        self.pause_button.pack(pady=10)

        self.stop_button = tk.Button(
            self.root, text="Stop Crawling", command=self.stop_crawl, state=tk.DISABLED
        )
        self.stop_button.pack(pady=10)

        # Results Display
        self.results_text = tk.Text(self.root, height=10, width=70)
        self.results_text.pack(pady=10)

        # Control variables
        self.crawling = False
        self.paused = False
        self.stop_event = threading.Event()

    def setup_logging(self):
        
        formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - [%(thread)d] - %(message)s'
        )
        # Advanced logging configuration
        log_dir = "logs"
        os.makedirs(log_dir, exist_ok=True)

        # TODO: Create robust logging, error handling

        logging.basicConfig(
            level=logging.INFO,
            format=formatter,
            handlers=[
                logging.FileHandler(os.path.join(log_dir, "crawler.log")),
                logging.StreamHandler(),
                RotatingFileHandler(
                    os.path.join(log_dir, "crawler_rotating.log"),
                    maxBytes=10 * 1024 * 1024,  # 10 MB
                    backupCount=5,
                ),
            ],
        )
        self.logger = logging.getLogger(__name__)

    def start_crawl(self):
        self.crawling = True
        self.paused = False
        self.stop_event.clear()

        self.start_button.config(state=tk.DISABLED)
        self.pause_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.NORMAL)

        url = self.url_entry.get()
        resolution = self.resolution_var.get()
        depth = self.depth_var.get()
        timeout = self.timeout_var.get()

        if not url.startswith("http"):
            messagebox.showerror("Error", "Invalid URL")
            return

        # Start crawling in a separate thread
        self.crawl_thread = threading.Thread(
            target=self.perform_crawl, args=(url, resolution, depth, timeout)
        )
        self.crawl_thread.start()
        logging.info("Crawling started")

    def pause_crawl(self):
        self.paused = not self.paused
        if self.paused:
            self.pause_button.config(text="Resume Crawling")
        else:
            self.pause_button.config(text="Pause Crawling")

    logging.info("Crawling paused")

    def stop_crawl(self):
        self.crawling = False
        self.stop_event.set()
        self.start_button.config(state=tk.NORMAL)
        self.pause_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.DISABLED)

        logging.info("Crawling stopped")

    def perform_crawl(self, url, resolution, depth, timeout):
        try:
            # Setup user agent
            user_agent = self.proxy_manager.get_random_user_agent()
            
            # Create browser using existing method
            driver = self.create_browser(user_agent)

            discovered_urls = set()
            downloaded_images = []

            queue = deque([(url, 0)])

            try:
                while queue and not self.stop_event.is_set():
                    if self.paused:
                        time.sleep(1)
                        continue

                    current_url, current_depth = queue.popleft()

                    if current_depth > depth or current_url in discovered_urls:
                        continue

                    discovered_urls.add(current_url)
                    self.logger.info(f"Crawling : {current_url}")

                    try:
                        driver.get(current_url)
                        time.sleep(2)  # Wait for page load

                        # Image processing
                        images = driver.find_elements(By.TAG_NAME, "img")
                        for img in images:
                            img_url = img.get_attribute("src")
                            if img_url and self.is_valid_image(img_url, resolution):
                                downloaded_img = self.process_image(img_url, resolution)
                                if downloaded_img:
                                    downloaded_images.append(downloaded_img)

                        # Link discovery
                        links = driver.find_elements(By.TAG_NAME, "a")
                        for link in links:
                            href = link.get_attribute("href")
                            if href and urlparse(href).netloc == urlparse(url).netloc:
                                queue.append((href, current_depth + 1))

                    except Exception as e:
                        self.logger.error(f"Error crawling {current_url}: {e}")

                # Save results
                self.display_metrics()


            finally:
                driver.quit()

        except Exception as e:
            self.logger.critical(f"Crawl failed: {e}")
            messagebox.showerror("Crawl Error", str(e))

        self.crawling = False
        self.start_button.config(state=tk.NORMAL)
        self.pause_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.DISABLED)

    def create_browser(self, user_agent):
        """Create a Selenium WebDriver instance with a random User-Agent."""
        options = webdriver.ChromeOptions()
        options.add_argument(f"user-agent={user_agent}")

        driver = webdriver.Chrome(
            service=Service(ChromeDriverManager().install()), options=options
        )
        logging.info("Selenium WebDriver created")

        return driver

    async def get_image_info(self, img_url):
        """Asynchronně získá informace o obrázku včetně rozměrů a typu."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(img_url) as response:
                    if response.status != 200:
                        return None

                    # Získáme první chunk dat pro rychlou detekci
                    chunk = await response.content.read(1024)

                    # Kontrola MIME typu
                    mime = magic.from_buffer(chunk, mime=True)
                    if not mime.startswith("image/"):
                        return None

                    # Stáhneme zbytek obrázku
                    content = chunk + await response.content.read()

                    # Kontrola formátu souboru
                    kind = filetype.guess(content)
                    if not kind or not kind.mime.startswith("image/"):
                        return None

                    try:
                        # Zkusíme rychlou detekci velikosti
                        width, height = imagesize.get_size_from_bytes(content)
                        return {"width": width, "height": height, "mime": mime}
                    except:
                        # Fallback na PIL
                        img = Image.open(BytesIO(content))
                        width, height = img.size
                        return {"width": width, "height": height, "mime": mime}

        except Exception as e:
            self.logger.error(f"Error analyzing image {img_url}: {str(e)}")
            return None

    def is_valid_image(self, img_url, resolution):
        """Check if the image matches the selected resolution."""
        try:
            # Spustíme asynchronní funkci synchronně
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            image_info = loop.run_until_complete(self.get_image_info(img_url))
            loop.close()

            if not image_info:
                return False

            width = image_info["width"]
            height = image_info["height"]
            filename = img_url.split("/")[-1].lower()

            # Vylepšená detekce rozlišení v názvu
            resolution_patterns = {
                "4K": ["4k", "2160p", "3840x2160", "4096x2160"],
                "2K": ["2k", "1440p", "2560x1440"],
                "FullHD": ["fullhd", "1080p", "1920x1080"],
            }

            if resolution == "4K":
                return (width >= 3840 and height >= 2160) or any(
                    pattern in filename for pattern in resolution_patterns["4K"]
                )
            elif resolution == "2K":
                return (width >= 2560 and height >= 1440) or any(
                    pattern in filename for pattern in resolution_patterns["2K"]
                )
            elif resolution == "FullHD":
                return (width >= 1920 and height >= 1080) or any(
                    pattern in filename for pattern in resolution_patterns["FullHD"]
                )
            elif resolution == "ALL":
                return True
            else:
                return False

        except Exception as e:
            self.logger.error(f"Error validating image {img_url}: {str(e)}")
            return False

    async def process_image(self, img_url: str, resolution: str) -> Optional[str]:
        try:
            async with self.resource_manager.request(img_url) as response:
                if response.status != 200:
                    self.metrics.update(success=False)
                    return None
                
                content = await response.read()
                
                # Kontrola duplicit
                if self.image_processor.is_duplicate(content):
                    self.logger.info(f"Duplicate image found: {img_url}")
                    return None
                
                image_info = await self.image_analyzer.analyze_image(content, img_url)
                if not image_info:
                    self.metrics.update(success=False)
                    return None
                
                saved_path = await self.save_image(image_info, content, resolution)
                if saved_path:
                    self.metrics.update(bytes_downloaded=len(content))
                    return saved_path
                
                self.metrics.update(success=False)
                return None
                
        except Exception as e:
            self.logger.error(f"Failed to process image {img_url}: {e}")
            self.metrics.update(success=False)
            return None

    def display_metrics(self):
        stats = self.metrics.stats
        self.results_text.insert(tk.END, 
            f"\nCrawling Statistics:\n"
            f"Duration: {stats['duration']:.2f}s\n"
            f"Processed URLs: {stats['processed_urls']}\n"
            f"Downloaded Images: {stats['downloaded_images']}\n"
            f"Failed Downloads: {stats['failed_downloads']}\n"
            f"Total MB: {stats['total_mb']:.2f}\n"
            f"MB/s: {stats['mb_per_second']:.2f}\n"
        )

    async def cleanup(self):
        await self.resource_manager.close()

    async def process_images_batch(self, images: List[str], resolution: str):
        tasks = [self.process_image(img, resolution) for img in images]
        return await asyncio.gather(*tasks, return_exceptions=True)

    async def save_image(self, image_info: ImageInfo, resolution: str) -> Optional[str]:
        try:
            output_dir = os.path.join(OUTPUT_STRUCTURE["base_dir"], resolution)
            os.makedirs(output_dir, exist_ok=True)

            filename = f"{int(time.time())}_{os.path.basename(image_info.url)}"
            output_path = os.path.join(output_dir, filename)

            async with aiohttp.ClientSession() as session:
                async with session.get(image_info.url) as response:
                    if response.status != 200:
                        return None

                    content = await response.read()
                    with open(output_path, "wb") as f:
                        f.write(content)

            self.logger.info(f"Saved image: {output_path}")
            return output_path

        except Exception as e:
            self.logger.error(f"Failed to save image {image_info.url}: {e}")
            return None

    def run(self):
        self.data_collector = DataCollector(OUTPUT_STRUCTURE["data_dir"])
        self.image_analyzer = ImageAnalyzer(self.logger)
        self.root.mainloop()


if __name__ == "__main__":
    crawler = WallpaperCrawler()
    crawler.run()
