import os
import logging
import asyncio
from PIL import Image
from typing import Dict, Tuple

from .config import CrawlerConfig
from .utils import generate_unique_filename

class ImageProcessor:
    @staticmethod
    async def process_image(image_path: str, config: Dict[str, Tuple[int, int]] = None):
        """
        Process and categorize images by resolution
        
        Args:
            image_path (str): Path to the image file
            config (Dict): Resolution configuration
        """
        config = config or CrawlerConfig.IMAGE_RESOLUTIONS
        
        try:
            with Image.open(image_path) as img:
                pixels = img.width * img.height
                
                for res_category, (min_pixels, max_pixels) in config.items():
                    if min_pixels <= pixels < max_pixels:
                        dest_dir = os.path.join(os.path.dirname(image_path), res_category)
                        os.makedirs(dest_dir, exist_ok=True)
                        
                        new_path = os.path.join(dest_dir, os.path.basename(image_path))
                        os.rename(image_path, new_path)
                        
                        logging.info(f"Categorized {os.path.basename(image_path)} as {res_category}")
                        break
        except Exception as e:
            logging.error(f"Error processing image {image_path}: {e}")

    @staticmethod
    async def bulk_process_images(image_dir: str):
        """
        Process multiple images asynchronously
        
        Args:
            image_dir (str): Directory containing images
        """
        tasks = []
        for filename in os.listdir(image_dir):
            filepath = os.path.join(image_dir, filename)
            if os.path.isfile(filepath):
                tasks.append(ImageProcessor.process_image(filepath))
        
        await asyncio.gather(*tasks)