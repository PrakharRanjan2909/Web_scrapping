# Web Scraping Assignment - E-commerce Product Data Extraction

## Description
This project is a comprehensive web scraping solution designed to extract product information from major e-commerce platforms including Nykaa Fashion and Myntra. The scraper utilizes advanced Selenium-based automation with robust anti-bot protection mechanisms to gather detailed product data including prices, ratings, reviews, images, and availability information. The solution is built with enterprise-grade error handling, dynamic content management, and exports data in both CSV and JSON formats for maximum compatibility.

## Objectives
1. Data Extraction: Automatically collect comprehensive product information from e-commerce websites
2. Anti-Bot Evasion: Implement sophisticated techniques to bypass detection mechanisms
3. Dynamic Content Handling: Manage JavaScript-rendered content and lazy-loaded elements
4. Data Quality: Ensure accurate and complete data extraction with proper validation
5. Scalability: Design a modular, object-oriented architecture for easy maintenance and extension
6. Export Flexibility: Provide structured data output in multiple formats (CSV, JSON)
7. Production Readiness: Build a robust solution suitable for real-world applications

## Features
🔧 Core Functionality
Multi-Platform Support: Scrape from Nykaa Fashion and Myntra
Advanced Search: Automated product search with configurable parameters
Comprehensive Data Extraction: Brand, name, prices, ratings, reviews, images, sizes, availability
Dual Export Formats: CSV and JSON output with proper encoding

🛡️ Anti-Bot Protection
User-Agent Rotation: Random browser identification to avoid detection
WebDriver Stealth: Hidden automation indicators and fingerprint prevention
Human-Like Behavior: Random delays, mouse movements, and typing patterns
Rate Limiting: Configurable delays between requests to mimic human browsing

🎯 Dynamic Content Handling
Explicit Waits: WebDriverWait for dynamically loaded elements
Lazy Loading Support: Scroll-based content loading for infinite scroll pages
Popup Management: Automatic handling of promotional popups and overlays
Fallback Strategies: Multiple extraction methods for robust data collection


📊 Data Quality & Structure
Safe Extraction: Graceful error handling with fallback values
Data Validation: Price normalization and format consistency
Size Tracking: Stock availability status for each product variant
Review Aggregation: Multiple customer reviews collection and formatting
## Approach

The solution employs a class-based object-oriented architecture using Python's Selenium WebDriver for browser automation. The scraper implements a multi-layered anti-bot strategy combining user-agent spoofing, WebGL disabling, and human behavior simulation to bypass detection systems. Dynamic content handling is achieved through explicit waits, scroll-based loading, and multiple extraction strategies with fallback mechanisms. The data extraction pipeline uses XPath and CSS selectors with safe extraction methods to ensure robustness against website structure changes. Finally, the system provides flexible data export in both CSV and JSON formats with proper UTF-8 encoding for international character support

Requirements
``` bash
selenium==4.15.0
webdriver-manager==4.0.1
pandas==2.0.3
beautifulsoup4==4.12.2
requests==2.31.0
```

## Installation & Setup
``` bash
git clone <repository-url>
cd ...
pip install -r requirements.txt
```

## Install Chrome WebDriver:

Download ChromeDriver from https://chromedriver.chromium.org/
Ensure ChromeDriver is in your system PATH
Or use webdriver-manager for automatic management

## 🚀 Quick Start - Nykaa Fashion Scraper
``` bash
python nyakaa_new.py
python myntra_new.py
```



