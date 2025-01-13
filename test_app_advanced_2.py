from datetime import datetime
import asyncio
import aiohttp
import aiofiles
import hashlib
import json
import logging
import os
import re
import threading
from collections import defaultdict
from io import BytesIO
from logging.handlers import RotatingFileHandler
from PIL import Image
from queue import Queue
from urllib.parse import urlparse, urljoin
import dns.resolver
import tkinter as tk
from tkinter import ttk, messagebox


class ImageResolution:
    RESOLUTIONS = {"4K": (3840, 2160), "2K": (2560, 1440), "FHD": (1920, 1080)}

    @staticmethod
    def meets_criteria(width, height, target_res, min_ratio=1.3, max_ratio=2.1):
        if target_res == "ALL":
            return True

        aspect_ratio = width / height
        if not (min_ratio <= aspect_ratio <= max_ratio):
            return False

        target = ImageResolution.RESOLUTIONS.get(target_res)
        return target and width >= target[0] and height >= target[1]


class AdvancedImageCrawler:
    def __init__(self, gui_callback=None):
        self.init_attributes(gui_callback)
        self.setup_storage()
        self.setup_logging()

    def init_attributes(self, gui_callback):
        self.url_queue = asyncio.Queue()
        self.image_queue = asyncio.Queue()
        self.download_queue = asyncio.Queue()

        self.stats = defaultdict(int)
        self.gui_callback = gui_callback
        self.target_resolution = "ALL"

        self.found_endpoints = set()
        self.found_subdomains = set()
        self.processed_urls = set()
        self.downloaded_hashes = set()

        self.is_running = False
        self.is_paused = False
        self.session = None
        
    HEADERS = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'cs,en-US;q=0.7,en;q=0.3',
        'DNT': '1',
    }

    CONSENT_PATTERNS = {
        'banners': [
            'cookie-banner', 'cookie-consent', 'cookie-notice',
            'consent-banner', 'consent-modal', 'gdpr-banner',
            'privacy-banner', 'privacy-notice'
        ],
        'buttons': {
            'decline': [
                'decline', 'reject', 'odmítnout', 'nesouhlasím', 
                'reject all', 'decline all', 'disable all',
                'no, thanks', 'ne, děkuji'
            ],
            'close': [
                'close', 'zavřít', '×', '✕', 'dismiss'
            ]
        },
        'selectors': [
            '#cookie-banner button', '.consent-banner button',
            '[aria-label*="cookie"] button', '[class*="cookie"] button',
            '[id*="cookie"] button', '[class*="consent"] button',
            '[id*="consent"] button', '[class*="gdpr"] button'
        ]
    }

    async def monitor_consent_blocks(self):
        """Async monitoring pro blokující prvky"""
        while self.is_running and not self.is_paused:
            try:
                if self.session:
                    async with self.session.get(self.current_url) as response:
                        if response.status == 200:
                            html = await response.text()
                            if await self.detect_and_handle_consent(html, response.url):
                                self.logger.info(f"Handled consent for {response.url}")
            except Exception as e:
                self.logger.error(f"Consent monitoring error: {e}")
            await asyncio.sleep(2)

    async def detect_and_handle_consent(self, html, url):
        """Detekce a zpracování consent/cookie bannerů"""
        for banner in self.CONSENT_PATTERNS['banners']:
            if banner in html.lower():
                # Zkusit najít decline tlačítko
                for decline in self.CONSENT_PATTERNS['buttons']['decline']:
                    if decline in html.lower():
                        return await self.handle_consent_action(url, 'decline')
                
                # Zkusit najít close tlačítko jako záložní řešení
                for close in self.CONSENT_PATTERNS['buttons']['close']:
                    if close in html.lower():
                        return await self.handle_consent_action(url, 'close')
        return False

    async def handle_consent_action(self, url, action_type):
        """Zpracování konkrétní consent akce"""
        try:
            async with self.session.post(
                url,
                data={
                    'consent': 'decline',
                    'action': action_type,
                    'timestamp': datetime.now().isoformat()
                },
                headers={
                    **self.HEADERS,
                    'X-Requested-With': 'XMLHttpRequest'
                },
                timeout=5
            ) as response:
                return response.status == 200
        except Exception as e:
            self.logger.error(f"Consent action error: {e}")
            return False

    def setup_storage(self):
        for directory in ["logs", "obtained_images", "reports"]:
            os.makedirs(directory, exist_ok=True)

    def setup_logging(self):
        log_file = f"logs/crawler_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        handlers = [
            RotatingFileHandler(log_file, maxBytes=1024 * 1024, backupCount=3),
            logging.StreamHandler(),
        ]
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(levelname)s - %(message)s",
            handlers=handlers,
        )
        self.logger = logging.getLogger(__name__)

    async def extract_urls(self, html, base_url):
        try:
            patterns = {
                "urls": r'href=["\'](https?://[^"\']+)',
                "images": r'src=["\'](https?://[^"\']+\.(?:jpg|jpeg|png|webp))["\']',
            }

            urls = re.findall(patterns["urls"], html)
            image_urls = re.findall(patterns["images"], html)

            new_urls = [
                url for url in urls + image_urls if url not in self.processed_urls
            ]

            for url in new_urls:
                await self.url_queue.put(url)

            self.stats["found_images"] += len(image_urls)

        except Exception as e:
            self.logger.error(f"URL extraction error: {e}")

    async def find_subdomains(self, domain):
        resolver = dns.resolver.Resolver()
        resolver.timeout = resolver.lifetime = 1

        for subdomain in ["www", "api", "img", "images", "static", "media"]:
            try:
                full_domain = f"{subdomain}.{domain}"
                if await self.resolve_domain(resolver, full_domain):
                    self.found_subdomains.add(full_domain)
                    await self.url_queue.put(f"https://{full_domain}")
            except Exception:
                continue

    async def resolve_domain(self, resolver, domain):
        try:
            return bool(resolver.resolve(domain, "A"))
        except Exception:
            return False

    async def scan_endpoints(self, base_url):
        endpoints = ["api", "images", "media", "static", "upload", "files"]
        async with aiohttp.ClientSession() as session:
            tasks = [
                self.check_endpoint(session, f"{base_url.rstrip('/')}/{endpoint}")
                for endpoint in endpoints
            ]
            await asyncio.gather(*tasks)

    async def check_endpoint(self, session, url):
        try:
            async with session.get(url) as response:
                if response.status == 200:
                    self.found_endpoints.add(url)
                    await self.url_queue.put(url)
        except Exception:
            pass

    async def process_image(self, url, response):
        try:
            image_data = await response.read()
            image_hash = hashlib.md5(image_data).hexdigest()

            if image_hash in self.downloaded_hashes:
                return

            img = Image.open(BytesIO(image_data))
            width, height = img.size

            if ImageResolution.meets_criteria(width, height, self.target_resolution):
                self.save_image(url, image_data, image_hash, width, height)

        except Exception as e:
            self.logger.error(f"Image processing error: {e}")

    def save_image(self, url, image_data, image_hash, width, height):
        safe_filename = re.sub(r'[<>:"/\\|?*]', "", url.split("/")[-1])
        filename = f"obtained_images/{image_hash[:8]}_{safe_filename}"

        with open(filename, "wb") as f:
            f.write(image_data)

        self.downloaded_hashes.add(image_hash)
        self.stats["downloaded_images"] += 1
        self.stats["allowed_images"] += 1

        self.logger.info(f"Downloaded: {url} ({width}x{height})")

        if self.gui_callback:
            self.gui_callback(self.stats)

    async def crawl_process(self, start_url, num_workers=5):
        self.is_running = True
        self.start_time = datetime.now()
        self.current_url = start_url

        async with aiohttp.ClientSession(headers=self.HEADERS) as self.session:
            try:
                # Spustit monitoring consent bloků
                consent_monitor = asyncio.create_task(self.monitor_consent_blocks())
                
                domain = urlparse(start_url).netloc
                await asyncio.gather(
                    self.find_subdomains(domain),
                    self.scan_endpoints(start_url)
                )
                await self.url_queue.put(start_url)

                workers = [self.crawl_worker() for _ in range(num_workers)]
                await asyncio.gather(*workers)

            finally:
                self.save_report()
                self.session = None

    async def crawl_worker(self):
        while self.is_running and not self.is_paused:
            try:
                url = await self.url_queue.get_nowait()
                if url not in self.processed_urls:
                    self.processed_urls.add(url)
                    await self.process_url(url)
                self.url_queue.task_done()
            except asyncio.QueueEmpty:
                await asyncio.sleep(0.1)
            except Exception as e:
                self.logger.error(f"Crawl worker error: {e}")

    # Upravit process_url metodu:
    async def process_url(self, url):
        try:
            async with self.session.get(url) as response:
                if response.status == 200:
                    await self.handle_cookies(response)
                    content_type = response.headers.get("content-type", "")
                    if "image" in content_type:
                        await self.process_image(url, response)
                    elif "text/html" in content_type:
                        html = await response.text()
                        await self.extract_urls(html, url)
                        self.stats["crawled_sites"] += 1
        except Exception as e:
            self.logger.error(f"URL processing error: {e}")

    def save_report(self):
        report_data = {
            "stats": dict(self.stats),
            "endpoints": list(self.found_endpoints),
            "subdomains": list(self.found_subdomains),
        }

        filename = f"reports/report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(filename, "w") as f:
            json.dump(report_data, f, indent=4)

    def start_crawl(self, url):
        asyncio.create_task(self.crawl_process(url))

    async def pause(self):
        self.is_paused = True
        self.logger.info("Crawler paused")

    async def resume(self):
        self.is_paused = False
        self.logger.info("Crawler resumed")

    async def stop(self):
        self.is_running = False
        self.logger.info("Crawler stopping...")
        self.save_report()


# GUI třída zůstává beze změny, protože je dobře navržená


class CrawlerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Advanced Image Crawler")
        self.root.geometry("600x800")
        
        # Vytvoření event loop pro async operace
        self.loop = asyncio.new_event_loop()
        self.thread = None
        
        self.crawler = AdvancedImageCrawler(gui_callback=self.update_stats)
        self.create_gui_elements()
        
    def create_gui_elements(self):
        # URL Frame
        url_frame = ttk.LabelFrame(self.root, text="URL")
        url_frame.pack(pady=5, padx=10, fill="x")

        self.url_entry = ttk.Entry(url_frame)
        self.url_entry.pack(pady=5, padx=5, fill="x")
        self.url_entry.insert(0, "https://example.com")

        # Resolution Frame
        res_frame = ttk.LabelFrame(self.root, text="Target Resolution")
        res_frame.pack(pady=5, padx=10, fill="x")

        self.resolution_var = tk.StringVar(value="ALL")
        resolutions = [
            ("All Images", "ALL"),
            ("4K", "4K"),
            ("2K", "2K"),
            ("Full HD", "FHD"),
        ]

        for text, value in resolutions:
            ttk.Radiobutton(
                res_frame,
                text=text,
                value=value,
                variable=self.resolution_var,
                
            ).pack(side="left", padx=5)

        # Control Buttons Frame
        ctrl_frame = ttk.LabelFrame(self.root, text="Controls")
        ctrl_frame.pack(pady=5, padx=10, fill="x")

        self.start_button = ttk.Button(
            ctrl_frame, text="Start", command=self.start_crawl
        )
        self.start_button.pack(side="left", padx=5, pady=5)

        self.pause_button = ttk.Button(
            ctrl_frame, text="Pause", command=self.pause_crawl
        )
        self.pause_button.pack(side="left", padx=5, pady=5)

        self.resume_button = ttk.Button(
            ctrl_frame, text="Resume", command=self.resume_crawl
        )
        self.resume_button.pack(side="left", padx=5, pady=5)

        self.stop_button = ttk.Button(ctrl_frame, text="Stop", command=self.stop_crawl)
        self.stop_button.pack(side="left", padx=5, pady=5)

        # Progress Frame
        progress_frame = ttk.LabelFrame(self.root, text="Progress")
        progress_frame.pack(pady=5, padx=10, fill="x")

        self.progress_bar = ttk.Progressbar(progress_frame, mode="indeterminate")
        self.progress_bar.pack(fill="x", pady=5, padx=5)

        # Stats Frame
        stats_frame = ttk.LabelFrame(self.root, text="Statistics")
        stats_frame.pack(pady=5, padx=10, fill="x")

        self.stats_labels = {
            "crawling_time": ttk.Label(stats_frame, text="Crawling time: 0 sec"),
            "crawled_sites": ttk.Label(stats_frame, text="Crawled sites: 0"),
            "found_images": ttk.Label(stats_frame, text="Found images: 0"),
            "allowed_images": ttk.Label(stats_frame, text="Allowed images: 0"),
            "downloaded_images": ttk.Label(stats_frame, text="Downloaded images: 0"),
        }

        for label in self.stats_labels.values():
            label.pack(pady=2)

        # Log Frame
        log_frame = ttk.LabelFrame(self.root, text="Logs")
        log_frame.pack(pady=5, padx=10, fill="both", expand=True)

        self.log_text = tk.Text(log_frame, height=10, wrap=tk.WORD)
        self.log_text.pack(pady=5, padx=5, fill="both", expand=True)

        scrollbar = ttk.Scrollbar(log_frame, command=self.log_text.yview)
        scrollbar.pack(side="right", fill="y")
        self.log_text.config(yscrollcommand=scrollbar.set)

    def run_async_loop(self):
        asyncio.set_event_loop(self.loop)
        self.loop.run_forever()

    def start_crawl(self):
        url = self.url_entry.get()
        if not url.startswith(("http://", "https://")):
            messagebox.showerror("Error", "Invalid URL format")
            return

        # Spustit async loop v novém vlákně pokud ještě neběží
        if not self.thread or not self.thread.is_alive():
            self.thread = threading.Thread(target=self.run_async_loop, daemon=True)
            self.thread.start()

        self.progress_bar.start()
        self.start_button.state(["disabled"])

        # Spustit crawler
        asyncio.run_coroutine_threadsafe(
            self.crawler.crawl_process(url),
            self.loop
        )

    def pause_crawl(self):
        if self.loop and self.crawler:
            future = asyncio.run_coroutine_threadsafe(
                self.crawler.pause(),
                self.loop
            )
            future.result()  # Počkat na dokončení
            self.progress_bar.stop()
            self.log_text.insert("end", "Crawler paused\n")
            self.log_text.see("end")

    def resume_crawl(self):
        if self.loop and self.crawler:
            future = asyncio.run_coroutine_threadsafe(
                self.crawler.resume(),
                self.loop
            )
            future.result()
            self.progress_bar.start()
            self.log_text.insert("end", "Crawler resumed\n")
            self.log_text.see("end")

    def stop_crawl(self):
        if self.loop and self.crawler:
            future = asyncio.run_coroutine_threadsafe(
                self.crawler.stop(),
                self.loop
            )
            future.result()
            self.progress_bar.stop()
            self.start_button.state(["!disabled"])
            self.log_text.insert("end", "Crawler stopped\n")
            self.log_text.see("end")

    def update_stats(self, stats):
        # Použít after pro thread-safe aktualizaci GUI
        self.root.after(0, self._update_stats_safe, stats)

    def _update_stats_safe(self, stats):
        for key, value in stats.items():
            if key == "crawling_time":
                text = f"Crawling time: {value} sec"
            else:
                text = f"{key.replace('_', ' ').title()}: {value}"
            self.stats_labels[key].config(text=text)

        self.log_text.insert("end", f"Stats updated: {stats}\n")
        self.log_text.see("end")

    def on_closing(self):
        if self.crawler:
            if self.loop and self.loop.is_running():
                asyncio.run_coroutine_threadsafe(
                    self.crawler.stop(),
                    self.loop
                )
            self.loop.stop()
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = CrawlerGUI(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()