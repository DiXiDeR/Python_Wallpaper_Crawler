import asyncio
import aiohttp
import logging
from bs4 import BeautifulSoup
from typing import List, Set

from .config import CrawlerConfig
from .utils import generate_unique_filename
from .image_processor import ImageProcessor

class AdvancedCrawler:
    def __init__(self, base_url: str, max_workers: int = 10):
        self.base_url = base_url
        self.max_workers = max_workers
        self.discovered_urls: Set[str] = set()
        self.image_urls: Set[str] = set()
        self.api_endpoints: Set[str] = set()
        self.download_dir = CrawlerConfig.DOWNLOAD_DIR

    async def fetch_page(self, session: aiohttp.ClientSession, url: str) -> str:
        """Async page fetching with error handling"""
        try:
            async with session.get(url, timeout=10) as response:
                return await response.text()
        except Exception as e:
            logging.error(f"Error fetching {url}: {e}")
            return ""

    async def extract_links(self, html_content: str) -> List[str]:
        """Extract links, images, and API endpoints"""
        soup = BeautifulSoup(html_content, 'html.parser')
        links = []
        
        # Extract image links
        for img in soup.find_all('img'):
            img_url = img.get('src')
            if img_url and img_url.startswith(('http', 'https')):
                self.image_urls.add(img_url)

        # Extract other links
        for link in soup.find_all(['a', 'link']):
            href = link.get('href', '')
            if href and href.startswith(('http', 'https')):
                links.append(href)
                
                # Detect potential API endpoints
                if any(keyword in href.lower() for keyword in ['api', 'endpoint', 'v1', 'v2']):
                    self.api_endpoints.add(href)

        return links

    async def download_image(self, session: aiohttp.ClientSession, url: str):
        """Download single image"""
        try:
            async with session.get(url) as response:
                if response.status == 200:
                    filename = generate_unique_filename(url, self.download_dir)
                    with open(filename , 'wb') as f:
                        f.write(await response.read())
                    logging.info(f"Downloaded image: {filename}")
        except Exception as e:
            logging.error(f"Error downloading image {url}: {e}")

    async def download_images(self):
        """Async image downloader with semaphore"""
        semaphore = asyncio.Semaphore(self.max_workers)
        
        async def download_image_with_semaphore(url):
            async with semaphore:
                await self.download_image(url)

        async with aiohttp.ClientSession() as session:
            tasks = [download_image_with_semaphore(url) for url in self.image_urls]
            await asyncio.gather(*tasks)

    async def crawl_site(self, depth: int = 3):
        """Recursive async site crawling"""
        async with aiohttp.ClientSession() as session:
            await self._crawl_recursive(session, self.base_url, depth)

    async def _crawl_recursive(self, session: aiohttp.ClientSession, url: str, depth: int):
        if depth == 0 or url in self.discovered_urls:
            return

        self.discovered_urls.add(url)
        
        html_content = await self.fetch_page(session, url)
        links = await self.extract_links(html_content)

        # Async crawling of discovered links
        tasks = [
            self._crawl_recursive(session, link, depth - 1)
            for link in links[:10]  # Limit to prevent infinite crawling
        ]
        await asyncio.gather(*tasks)

    async def run(self):
        """Run the crawler"""
        await self.crawl_site()
        await self.download_images()
        await ImageProcessor.bulk_process_images(self.download_dir)