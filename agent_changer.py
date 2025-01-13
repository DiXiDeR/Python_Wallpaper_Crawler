from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from fake_useragent import UserAgent
import time

# Initialize UserAgent
ua = UserAgent()

def get_random_user_agent():
    """Generate a random User-Agent string."""
    return ua.random

def create_browser_with_random_agent():
    """Create a Selenium WebDriver instance with a random User-Agent."""
    # Generate a random User-Agent
    user_agent = get_random_user_agent()
    
    # Configure Chrome options
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument(f"user-agent={user_agent}")
    
    # Add other options (optional)
    chrome_options.add_argument("--headless")  # Run in headless mode
    chrome_options.add_argument("--disable-gpu")  # Disable GPU acceleration
    chrome_options.add_argument("--no-sandbox")  # Bypass OS security model
    
    # Initialize WebDriver
    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=chrome_options
    )
    
    return driver

def crawl_website(url):
    """Crawl a website using Selenium with a random User-Agent."""
    # Create a browser instance with a random User-Agent
    driver = create_browser_with_random_agent()
    
    try:
        # Navigate to the URL
        driver.get(url)
        print(f"User -Agent: {driver.execute_script('return navigator.userAgent;')}")
        
        # Perform crawling tasks (e.g., extract data)
        title = driver.title
        print(f"Page Title: {title}")
        
        # Add your crawling logic here
        
    finally:
        # Close the browser
        driver.quit()

# Example usage
if __name__ == "__main__":
    url = "https://example.com"
    crawl_website(url)