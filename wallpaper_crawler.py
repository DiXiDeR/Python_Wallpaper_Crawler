import os
import json
import logging
import csv
import random
import base64
import tkinter as tk
from tkinter import messagebox, filedialog
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from urllib.parse import urlparse
import requests
from PIL import Image
from io import BytesIO
from collections import deque
import concurrent.futures
import threading
import time
from logging.handlers import RotatingFileHandler

class ProxyManager:
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
        
        # Initialize Proxy Manager
        self.proxy_manager = ProxyManager()
        
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
                self.root, 
                text=res, 
                variable=self.resolution_var, 
                value=res
            ).pack()
        
        # Depth and Timeout Controls
        tk.Label(self.root, text="Crawl Depth (1-5):").pack()
        self.depth_var = tk.IntVar(value=3)
        tk.Scale(
            self.root, 
            from_=1, to=5, 
            orient=tk.HORIZONTAL, 
            variable=self.depth_var
        ).pack()
        
        # Timeout Control
        tk.Label(self.root, text="Request Timeout (seconds):").pack()
        self.timeout_var = tk.IntVar(value=10)
        tk.Scale(
            self.root, 
            from_=5, to=30, 
            orient=tk.HORIZONTAL, 
            variable=self.timeout_var
        ).pack()
        
        # Start, Pause, and Stop Buttons
        self.start_button = tk.Button(self.root, text="Start Advanced Crawling", command=self.start_crawl)
        self.start_button.pack(pady=10)
        
        self.pause_button = tk.Button(self.root, text="Pause Crawling", command=self.pause_crawl, state=tk.DISABLED)
        self.pause_button.pack(pady=10)
        
        self.stop_button = tk.Button(self.root, text="Stop Crawling", command=self.stop_crawl, state=tk.DISABLED)
        self.stop_button.pack(pady=10)
        
        # Results Display
        self.results_text = tk.Text(self.root, height=10, width=70)
        self.results_text.pack(pady=10)
        
        # Control variables
        self.crawling = False
        self.paused = False
        self.stop_event = threading.Event()
        
    def setup_logging(self):
        # Advanced logging configuration
        log_dir = 'logs'
        os.makedirs(log_dir, exist_ok=True)
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s: %(message)s',
            handlers=[
                logging.FileHandler(os.path.join(log_dir, 'crawler.log')),
                logging.StreamHandler(),
                RotatingFileHandler(
                    os.path.join(log_dir, 'crawler_rotating.log'),
                    maxBytes=10*1024*1024,  # 10 MB
                    backupCount=5
                )
            ]
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
        
        if not url.startswith('http'):
            messagebox.showerror("Error", "Invalid URL")
            return
        
        # Start crawling in a separate thread
        self.crawl_thread = threading.Thread(
            target=self.perform_crawl, 
            args=(url, resolution, depth, timeout)
        )
        self.crawl_thread.start()
    
    def pause_crawl(self):
        self.paused = not self.paused
        if self.paused:
            self.pause_button.config(text="Resume Crawling")
        else:
            self.pause_button.config(text="Pause Crawling")
    
    def stop_crawl(self):
        self.crawling = False
        self.stop_event.set()
        self.start_button.config(state=tk.NORMAL)
        self.pause_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.DISABLED)
    
    def perform_crawl(self, url, resolution, depth, timeout):
        try:
            # Setup user agent
            user_agent = self.proxy_manager.get_random_user_agent()
            
            driver = self.create_browser(user_agent)
            
            discovered_urls = set()
            downloaded_images = []
            
            queue = deque([(url, 0)])
            
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
                    images = driver.find_elements(By.TAG_NAME, 'img')
                    for img in images:
                        img_url = img.get_attribute('src')
                        if img_url and self.is_valid_image(img_url, resolution):
                            downloaded_img = self.download_image(img_url, resolution)
                            if downloaded_img:
                                downloaded_images.append(downloaded_img)
                    
                    # Link discovery
                    links = driver.find_elements(By.TAG_NAME, 'a')
                    for link in links: 
                        href = link.get_attribute('href')
                        if href and urlparse(href).netloc == urlparse(url).netloc:
                            queue.append((href, current_depth + 1))
                
                except Exception as e:
                    self.logger.error(f"Error crawling {current_url}: {e}")
            
            # Save results
            self.save_results(discovered_urls, downloaded_images)
            
            # Update GUI
            self.update_results_display(
                len(discovered_urls), 
                len(downloaded_images)
            )
            
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
        options.add_argument(f'user-agent={user_agent}')
        
        driver = webdriver.Chrome(
            service=Service(ChromeDriverManager().install()), 
            options=options
        )
        
        return driver

    def get_image_dimensions(self, img_url):
        """Fetch image dimensions (width and height) from the URL."""
        try:
            if img_url.startswith('data:image'):
                # Extract base64 data from the URL
                base64_data = img_url.split(',')[1]
                image_data = base64.b64decode(base64_data)
                img = Image.open(BytesIO(image_data))
            else:
                response = requests.get(img_url)
                img = Image.open(BytesIO(response.content))
            return img.size  # Returns (width, height)
        except Exception as e:
            self.logger.error(f"Error fetching image dimensions: {e}")
            return None

    def is_valid_image(self, img_url, resolution):
        """Check if the image matches the selected resolution."""
        dimensions = self.get_image_dimensions(img_url)
        if not dimensions:
            return False
        
        width, height = dimensions
        filename = img_url.split('/')[-1].lower()
        
        if resolution == "4K":
            return width >= 3840 and height >= 2160 or "4k" in filename
        elif resolution == "2K":
            return width >= 2560 and height >= 1440 or "2k" in filename
        elif resolution == "FullHD":
            return width >= 1920 and height >= 1080 or "fullhd" in filename
        elif resolution == "ALL":
            return True
        else:
            return False
    
    def download_image(self, img_url, resolution):
        output_dir = os.path.join("Obtained_Wallpapers", resolution)
        os.makedirs(output_dir, exist_ok=True)
        
        try:
            response = requests.get(img_url)
            filename = os.path.join(output_dir, img_url.split('/')[-1])
            with open(filename, 'wb') as f:
                f.write(response.content)
            return filename
        except Exception as e:
            self.logger.error(f"Image download error: {e}")
            return None
    
    def save_results(self, urls, images):
        # Save to CSV
        with open('crawl_results.csv', 'w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(["Discovered URLs", "Downloaded Images"])
            writer.writerows(zip(urls, images))
    
    def update_results_display(self, url_count, image_count):
        self.results_text.insert(tk.END, 
            f"Discovered URLs: {url_count}\n"
            f"Downloaded Images: {image_count}\n"
        )
    
    def run(self):
        self.root.mainloop()

# Main execution
if __name__ == "__main__":
    crawler = WallpaperCrawler()
    crawler.run()