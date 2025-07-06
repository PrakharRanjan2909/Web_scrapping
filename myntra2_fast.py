import json
import csv
import os
import time
from dataclasses import dataclass
from typing import List, Dict, Optional
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.common.keys import Keys

@dataclass
class ProductInfo:
    """Data class to store product information"""
    search_term: str
    brand_name: str = "N/A"
    current_price: str = "N/A"
    product_rating: str = "N/A"
    product_title: str = "N/A"
    original_price: str = "N/A"
    sale_price: str = "N/A"
    discount_percent: str = "N/A"
    category_path: str = "N/A"
    product_link: str = "N/A"
    image_link: str = "N/A"
    review_count: str = "N/A"
    size_options: str = "N/A"

class MyntraWebScraper:
    """Web scraper class for Myntra e-commerce site"""
    
    def __init__(self, headless: bool = False):
        self.driver = None
        self.headless_mode = headless
        self.wait_time = 10
        self.page_delay = 2
        
    def initialize_browser(self):
        """Initialize Chrome browser with custom settings"""
        options = Options()
        
        if self.headless_mode:
            options.add_argument("--headless")
            
        # Browser optimization arguments
        browser_args = [
            "--no-sandbox",
            "--disable-gpu",
            "--window-size=1920x1080",
            "--disable-dev-shm-usage",
            "--disable-blink-features=AutomationControlled"
        ]
        
        for arg in browser_args:
            options.add_argument(arg)
            
        # Custom user agent
        options.add_argument(
            "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        )
        
        self.driver = webdriver.Chrome(options=options)
        return self.driver
    
    def search_and_get_url(self, search_query: str) -> Optional[str]:
        """Perform search and return the results page URL"""
        try:
            print(f"Searching for: {search_query}")
            
            # Navigate to homepage
            self.driver.get("https://www.myntra.com")
            time.sleep(1)
            
            # Locate and use search functionality
            search_input = self.driver.find_element(By.CLASS_NAME, "desktop-searchBar")
            search_input.clear()
            search_input.send_keys(search_query)
            search_input.send_keys(Keys.RETURN)
            
            time.sleep(1)
            return self.driver.current_url
            
        except Exception as error:
            print(f"Search failed for '{search_query}': {error}")
            return None
    
    def extract_product_details(self, product_element, search_term: str) -> ProductInfo:
        """Extract all product information from a product element"""
        product = ProductInfo(search_term=search_term)
        
        # Define extraction methods
        extraction_map = {
            "brand_name": ("product-brand", "text"),
            "current_price": ("product-discountedPrice", "text"),
            "product_rating": ("product-ratingsContainer", "text"),
            "product_title": ("product-product", "text"),
            "original_price": ("product-strike", "text"),
            "sale_price": ("product-discountedPrice", "text"),
            "discount_percent": ("product-discountPercentage", "text"),
        }
        
        # Extract basic product information
        for field, (class_name, attr_type) in extraction_map.items():
            try:
                element = product_element.find_element(By.CLASS_NAME, class_name)
                setattr(product, field, element.text if attr_type == "text" else element.get_attribute(attr_type))
            except NoSuchElementException:
                pass  # Keep default "N/A" value
        
        # Extract product URL
        try:
            link_element = product_element.find_element(By.CSS_SELECTOR, "a[data-refreshpage='true']")
            product.product_link = link_element.get_attribute("href")
        except NoSuchElementException:
            pass
        
        # Extract image URL
        try:
            img_element = product_element.find_element(By.CSS_SELECTOR, "img.img-responsive")
            product.image_link = img_element.get_attribute("src")
        except NoSuchElementException:
            pass
        
        # Extract review count
        try:
            review_element = product_element.find_element(By.CSS_SELECTOR, ".product-ratingsCount")
            product.review_count = review_element.text.strip("()")
        except NoSuchElementException:
            pass
        
        # Extract breadcrumb/category
        try:
            breadcrumb_element = self.driver.find_element(By.CSS_SELECTOR, "span.breadcrumbs-crumb[style='font-size: 14px; margin: 0px;']")
            product.category_path = breadcrumb_element.text
        except NoSuchElementException:
            pass
        
        return product
    
    def scrape_products_from_page(self, search_term: str, page_url: str) -> List[ProductInfo]:
        """Scrape all products from a single page"""
        try:
            self.driver.get(page_url)
            
            # Wait for products to load
            product_elements = WebDriverWait(self.driver, self.wait_time).until(
                EC.presence_of_all_elements_located((By.CLASS_NAME, "product-base"))
            )
            
            if not product_elements:
                return []
            
            products = []
            for element in product_elements:
                try:
                    product_info = self.extract_product_details(element, search_term)
                    products.append(product_info)
                except Exception as error:
                    print(f"Error extracting product: {error}")
                    continue
            
            return products
            
        except TimeoutException:
            print(f"Timeout: Page failed to load - {page_url}")
            return []
    
    def save_to_csv(self, products: List[ProductInfo], filename: str, append_mode: bool = False):
        """Save product data to CSV file"""
        mode = 'a' if append_mode and os.path.exists(f"{filename}.csv") else 'w'
        
        with open(f"{filename}.csv", mode, newline='', encoding="utf-8") as file:
            fieldnames = [
                "search_term", "brand_name", "current_price", "product_rating",
                "product_title", "original_price", "sale_price", "discount_percent",
                "category_path", "product_link", "image_link", "review_count", "size_options"
            ]
            
            writer = csv.DictWriter(file, fieldnames=fieldnames)
            
            if mode == 'w':
                writer.writeheader()
            
            for product in products:
                writer.writerow(product.__dict__)
    
    def run_scraping_session(self, search_terms: List[str], max_pages: int, output_file: str):
        """Main scraping workflow"""
        search_urls = {}
        all_products = []
        
        # Generate search URLs
        print("Generating search URLs...")
        for term in search_terms:
            url = self.search_and_get_url(term)
            search_urls[term] = url
            print(f"URL for '{term}': {url}")
        
        # Save URLs to JSON
        with open('search_urls.json', 'w', encoding='utf-8') as f:
            json.dump(search_urls, f, indent=4, ensure_ascii=False)
        
        # Scrape products for each search term
        try:
            for search_term, base_url in search_urls.items():
                if not base_url:
                    print(f"Skipping '{search_term}' - no URL available")
                    continue
                
                print(f"\nScraping products for: {search_term}")
                
                current_page = 1
                pages_to_scrape = max_pages if max_pages > 0 else float('inf')
                
                while current_page <= pages_to_scrape:
                    page_url = f"{base_url}&p={current_page}"
                    print(f"Processing page {current_page}: {page_url}")
                    
                    page_products = self.scrape_products_from_page(search_term, page_url)
                    
                    if not page_products:
                        print(f"No products found on page {current_page}")
                        break
                    
                    all_products.extend(page_products)
                    
                    # Save after each page
                    self.save_to_csv(page_products, output_file, append_mode=True)
                    print(f"Saved {len(page_products)} products from page {current_page}")
                    
                    current_page += 1
                    time.sleep(self.page_delay)
                
                print(f"Completed scraping for '{search_term}'")
        
        except Exception as error:
            print(f"Scraping error: {error}")
        
        finally:
            self.close_browser()
        
        print(f"\nScraping completed! Total products: {len(all_products)}")
        return all_products
    
    def close_browser(self):
        """Clean up browser resources"""
        if self.driver:
            self.driver.quit()

def main():
    """Main execution function"""
    # User input
    max_pages = int(input("Enter number of pages to scrape (0 for all): "))
    output_filename = input("Enter output filename: ")
    browser_mode = input("Enter 'headless' for headless mode, or press Enter: ")
    
    headless = browser_mode.lower() == 'headless'
    
    # Define search terms
    search_items = [
        "white shirt",
        "black dress", 
        "denim jeans",
        "summer kurti",
        "co-ord set",
        "oversized t-shirt",
        "sneakers",
        "blue linen pants",
        "pink blazer for women",
        "yellow maxi dress"
    ]
    
    # Initialize and run scraper
    scraper = MyntraWebScraper(headless=headless)
    scraper.initialize_browser()
    
    try:
        scraper.run_scraping_session(search_items, max_pages, output_filename)
    except KeyboardInterrupt:
        print("\nScraping interrupted by user")
    except Exception as e:
        print(f"Unexpected error: {e}")
    finally:
        scraper.close_browser()

if __name__ == "__main__":
    main()