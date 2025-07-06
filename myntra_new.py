import json
import csv
import os
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.common.keys import Keys

class MyntraProductScraper:
    def __init__(self, headless=False):
        """Initialize the scraper with Chrome driver configuration"""
        self.driver = self._configure_driver(headless)
        self.base_url = "https://www.myntra.com"
        self.scraped_data = []
        
    def _configure_driver(self, headless):
           
        """Configure and return Chrome WebDriver instance"""
        options = Options()
        if headless:
            options.add_argument("--headless")
        
        # Essential arguments/anti bot
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-gpu")
        options.add_argument("--window-size=1920x1080")
        options.add_argument("--disable-dev-shm-usage")
        
        # Fix WebGL errors--fingerprint prevention
        options.add_argument("--disable-webgl")
        options.add_argument("--disable-software-rasterizer")
        options.add_argument("--disable-extensions")
        
        options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
        
        return webdriver.Chrome(options=options)
    
    def search_products(self, search_term):
        """Search for products using the given search term"""
        try:
            self.driver.get(self.base_url)
            time.sleep(2)
            
            search_box = self.driver.find_element(By.CLASS_NAME, "desktop-searchBar")
            search_box.clear()
            search_box.send_keys(search_term)
            search_box.send_keys(Keys.RETURN)
            time.sleep(3)
            
            return self.driver.current_url
        except Exception as e:
            print(f"Search failed for '{search_term}': {e}")
            return None
    
    def collect_product_urls(self, search_url, max_products=10):
        """Collect product URLs from search results"""
        product_urls = []
        
        try:
            self.driver.get(search_url)
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_all_elements_located((By.XPATH, "//li[@class='product-base']"))
            )
            
            product_elements = self.driver.find_elements(By.XPATH, "//li[@class='product-base']")
            
            for element in product_elements[:max_products]:
                try:
                    product_link = element.find_element(By.TAG_NAME, "a").get_attribute("href")
                    product_urls.append(product_link)
                except:
                    continue
                    
        except TimeoutException:
            print("Failed to load product listings")
            
        return product_urls
    
    def extract_product_image(self):
        """Extract product image URL from various possible locations"""
        image_strategies = [
            # Strategy 1: CSS background-image
            lambda: self._extract_background_image(".image-grid-image"),
            lambda: self._extract_background_image(".image-grid-imageContainer"),
            
            # Strategy 2: Traditional img elements
            lambda: self._extract_img_src("img.img-responsive"),
            lambda: self._extract_img_src(".pdp-main-container img"),
            
            # Strategy 3: Fallback search
            lambda: self._find_product_image_fallback()
        ]
        
        for strategy in image_strategies:
            try:
                result = strategy()
                if result and result.startswith("http"):
                    return result.split("?")[0]  # Remove query parameters
            except:
                continue
                
        return "Image not available"
    
    def _extract_background_image(self, selector):
        """Extract image URL from CSS background-image property"""
        element = self.driver.find_element(By.CSS_SELECTOR, selector)
        style_attr = element.get_attribute("style")
        
        if style_attr and "background-image: url(" in style_attr:
            start_pos = style_attr.find("background-image: url(\"") + len("background-image: url(\"")
            end_pos = style_attr.find("\")", start_pos)
            if start_pos > 0 and end_pos > start_pos:
                return style_attr[start_pos:end_pos]
        return None
    
    def _extract_img_src(self, selector):
        """Extract image URL from img element src attribute"""
        img_element = self.driver.find_element(By.CSS_SELECTOR, selector)
        return img_element.get_attribute("src")
    
    def _find_product_image_fallback(self):
        """Fallback method to find any product image"""
        all_images = self.driver.find_elements(By.TAG_NAME, "img")
        for img in all_images:
            src = img.get_attribute("src")
            if src and any(keyword in src.lower() for keyword in ["myntra", "assets"]):
                return src
        return None
    
    def extract_product_details(self, product_url, search_keyword):
        """Extract detailed information from a product page"""
        try:
            self.driver.get(product_url)
            time.sleep(2)
            
            product_info = {
                "search_keyword": search_keyword,
                "product_url": product_url,
                "brand": self._safe_extract(By.CLASS_NAME, "pdp-title"),
                "name": self._safe_extract(By.CLASS_NAME, "pdp-name"),
                "discounted_price": self._safe_extract(By.CLASS_NAME, "pdp-price"),
                "original_price": self._safe_extract(By.CLASS_NAME, "pdp-mrp"),
                "rating": self._safe_extract(By.CLASS_NAME, "index-overallRating"),
                "image_url": self.extract_product_image(),
                "reviews": self._extract_reviews(),
                "available_sizes": self._extract_size_options(),
                "breadcrumb": self._extract_breadcrumb()
            }
            
            # Handle missing original price
            if not product_info["original_price"]:
                product_info["original_price"] = product_info["discounted_price"]
            
            return product_info
            
        except Exception as e:
            print(f"Error extracting details from {product_url}: {e}")
            return None
    
    def _safe_extract(self, by_type, selector):
        """Safely extract text from element, return 'N/A' if not found"""
        try:
            element = self.driver.find_element(by_type, selector)
            return element.text.strip()
        except:
            return "N/A"
    
    def _extract_reviews(self):
        """Extract product reviews"""
        try:
            review_elements = self.driver.find_elements(By.XPATH, "//div[@class='user-review-reviewTextWrapper']")
            return [review.text.strip() for review in review_elements if review.text.strip()]
        except:
            return []
    
    def _extract_size_options(self):
        """Extract available sizes with stock status"""
        try:
            size_buttons = self.driver.find_elements(By.CLASS_NAME, "size-buttons-size-button")
            size_info = []
            
            for button in size_buttons:
                size_text = button.text.strip()
                if size_text:
                    is_disabled = "disabled" in button.get_attribute("class") or button.get_attribute("aria-disabled") == "true"
                    stock_status = "Out of Stock" if is_disabled else "In Stock"
                    size_info.append(f"{size_text} ({stock_status})")
            
            return size_info
        except:
            return []
    
    def _extract_breadcrumb(self):
        """Extract breadcrumb navigation"""
        try:
            breadcrumb_elements = self.driver.find_elements(By.CSS_SELECTOR, ".breadcrumbs-crumb")
            breadcrumb_text = [elem.text.strip() for elem in breadcrumb_elements if elem.text.strip()]
            return " > ".join(breadcrumb_text)
        except:
            return "N/A"
    
    def save_data(self, filename):
        """Save scraped data to both CSV and JSON formats"""
        if not self.scraped_data:
            print("No data to save")
            return
        
        # Save as CSV
        csv_filename = f"{filename}.csv"
        with open(csv_filename, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ["search_keyword", "brand", "name", "product_url", "image_url", 
                         "original_price", "discounted_price", "rating", "reviews", 
                         "available_sizes", "breadcrumb" ]
            
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            
            for product in self.scraped_data:
                csv_row = product.copy()
                csv_row["reviews"] = " | ".join(product["reviews"]) if product["reviews"] else "No reviews"
                csv_row["available_sizes"] = "; ".join(product["available_sizes"]) if product["available_sizes"] else "No sizes"
                writer.writerow(csv_row)
        
        # Save as JSON
        json_filename = f"{filename}.json"
        with open(json_filename, 'w', encoding='utf-8') as jsonfile:
            json.dump(self.scraped_data, jsonfile, indent=4, ensure_ascii=False)
        
        print(f"Data saved to {csv_filename} and {json_filename}")
    
    def run_scraping_session(self, search_terms, max_products_per_term=10):
        """Execute complete scraping session for given search terms"""
        print("Starting Myntra product scraping session...")
        
        for term in search_terms:
            print(f"\nProcessing search term: '{term}'")
            
            # Get search results URL
            search_url = self.search_products(term)
            if not search_url:
                continue
            
            # Collect product URLs
            product_urls = self.collect_product_urls(search_url, max_products_per_term)
            print(f"Found {len(product_urls)} products for '{term}'")
            
            # Extract details from each product
            for idx, url in enumerate(product_urls, 1):
                print(f"Scraping product {idx}/{len(product_urls)}")
                product_details = self.extract_product_details(url, term)
                
                if product_details:
                    self.scraped_data.append(product_details)
                
                time.sleep(1)  # Rate limiting
        
        print(f"\nScraping complete! Total products scraped: {len(self.scraped_data)}")
    
    def close(self):
        """Close the webdriver"""
        self.driver.quit()

def main():
    """Main execution function"""
    # Get user inputs
    max_products = int(input("Enter max products per search term (default 10): ") or "10")
    output_file = input("Enter output filename (without extension): ") or "myntra_products"
    headless_mode = input("Run in headless mode? (y/n): ").lower() == 'y'
    
    # Define search terms
    search_terms = [
        "white shirt",
         "black dress", "denim jeans", "summer kurti", 
        "co-ord set", "oversized t-shirt", "sneakers", "blue linen pants",
        "pink blazer for women", "yellow maxi dress"
    ]
    
    # Initialize scraper
    scraper = MyntraProductScraper(headless=headless_mode)
    
    try:
        # Run scraping session
        scraper.run_scraping_session(search_terms, max_products)
        
        # Save results
        scraper.save_data(output_file)
        
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        scraper.close()

if __name__ == "__main__":
    main()