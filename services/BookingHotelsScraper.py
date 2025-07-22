#!/usr/bin/env python3
"""
Enhanced Booking.com Hotel Scraper with CSV-first approach
"""

import undetected_chromedriver as uc
import time
import json
import csv
import re
import os
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional
from bs4 import BeautifulSoup
import pandas as pd
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from services.database_service import DatabaseService
from models import ScrapingJob
from database import SessionLocal

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BookingScraperIntegration:
    """
    Enhanced Booking.com scraper that saves to CSV first, then imports to database
    """
    
    def __init__(self, csv_directory: str = "data/csv"):
        self.driver = None
        self.csv_directory = csv_directory
        self.database_service = DatabaseService()
        self.current_csv_file = None
        self.scraped_hotels = []
        self.current_job_id = None
        
        # Ensure CSV directory exists
        os.makedirs(self.csv_directory, exist_ok=True)
        
    def _setup_driver(self):
        """Setup Chrome driver with anti-detection"""
        try:
            log_path = "/tmp/chromedriver.log"
            
            self._log_message("Starting Chrome driver...")
            
            # Configure Chrome options for Ubuntu server environment
            options = uc.ChromeOptions()
            
            # Essential arguments for server environments
            options.add_argument("--headless")  # Required for server environments
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--disable-gpu")
            options.add_argument("--window-size=1920,1080")
            options.add_argument("--disable-blink-features=AutomationControlled")
            
            # Additional stability arguments for Ubuntu server
            options.add_argument("--disable-extensions")
            options.add_argument("--disable-plugins")
            options.add_argument("--disable-images")
            options.add_argument("--no-first-run")
            options.add_argument("--no-default-browser-check")
            options.add_argument("--disable-default-apps")
            options.add_argument("--disable-web-security")
            options.add_argument("--allow-running-insecure-content")
            options.add_argument("--disable-background-timer-throttling")
            options.add_argument("--disable-renderer-backgrounding")
            options.add_argument("--disable-backgrounding-occluded-windows")
            
            # Try to detect Chrome binary location
            chrome_paths = [
                "/usr/bin/google-chrome-stable",
                "/usr/bin/google-chrome",
                "/usr/bin/chromium-browser",
                "/usr/bin/chromium",
                "/opt/google/chrome/chrome"
            ]
            
            chrome_binary = None
            for path in chrome_paths:
                if os.path.exists(path):
                    chrome_binary = path
                    break
            
            if chrome_binary:
                options.binary_location = chrome_binary
                self._log_message(f"Using Chrome binary: {chrome_binary}")
            else:
                self._log_message("Chrome binary not found in standard locations, using system default")
            
            # Initialize Chrome driver with improved configuration
            self.driver = uc.Chrome(
                options=options,
                service_log_path=log_path,
                version_main=None,  # Auto-detect Chrome version
                driver_executable_path=None  # Let undetected-chromedriver handle this
            )
            
            # Configure driver settings
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            self.driver.set_page_load_timeout(60)  # Increased timeout for server environments
            self.driver.implicitly_wait(15)  # Increased wait time
            
            self._log_message("Chrome driver setup completed successfully")
            
        except Exception as e:
            self._log_message(f"Error setting up Chrome driver: {str(e)}", "ERROR")
            
            # Print any Chrome driver logs for debugging
            log_path = "/tmp/chromedriver.log"
            if os.path.exists(log_path):
                try:
                    with open(log_path, 'r') as f:
                        log_content = f.read()
                        self._log_message("Chrome driver logs:", "ERROR")
                        self._log_message(log_content, "ERROR")
                except:
                    pass
            
            # Additional debugging information
            self._log_message("Chrome binary detection results:", "ERROR")
            chrome_paths = [
                "/usr/bin/google-chrome-stable",
                "/usr/bin/google-chrome",
                "/usr/bin/chromium-browser",
                "/usr/bin/chromium",
                "/opt/google/chrome/chrome"
            ]
            for path in chrome_paths:
                exists = os.path.exists(path)
                self._log_message(f"  {path}: {'EXISTS' if exists else 'NOT FOUND'}", "ERROR")
            
            raise Exception(f"Could not initialize Chrome driver: {str(e)}")

    def _log_message(self, message: str, level: str = "INFO"):
        """Log message with timestamp"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] {level}: {message}"
        print(log_entry)
        logger.log(getattr(logging, level), message)
    
    def _should_stop_job(self, job_id: int) -> bool:
        """Check if job should be stopped"""
        try:
            session = SessionLocal()
            job = session.query(ScrapingJob).filter(ScrapingJob.id == job_id).first()
            should_stop = job and job.status in ["STOPPED", "CANCELLED", "FAILED"]
            session.close()
            return should_stop
        except Exception as e:
            logger.error(f"Error checking job status: {str(e)}")
            return False
    
    def read_urls_from_csv(self, csv_file: str = "data/csv/booking_links.csv") -> List[str]:
        """Read URLs from CSV file"""
        try:
            if not os.path.exists(csv_file):
                self._log_message(f"CSV file not found: {csv_file}", "ERROR")
                return []
            
            urls = []
            with open(csv_file, 'r', encoding='utf-8') as file:
                reader = csv.reader(file)
                next(reader, None)  # Skip header
                for row in reader:
                    if row and len(row) > 1:  # Make sure we have at least 2 columns
                        urls.append(row[1].strip())  # Take URL from page_link column (index 1)
            
            self._log_message(f"Loaded {len(urls)} URLs from {csv_file}")
            return urls
            
        except Exception as e:
            self._log_message(f"Error reading URLs from CSV: {str(e)}", "ERROR")
            return []

    def has_furnature_header(self, tag):
        return tag.name == "section" and tag.find('h2') and "مرافق" in tag.find('h2').get_text()

    def has_bathroom_header(self, tag):
        return tag.name == "section" and tag.find('h2') and "حمام" in tag.find('h2').get_text()

    def has_view_header(self, tag):
        return tag.name == "section" and tag.find('h2') and "الإطلالة:" in tag.find('h2').get_text()

    def has_cooking_header(self, tag):
        return tag.name == "section" and tag.find('h2') and "مطبخ" in tag.find('h2').get_text()

    def extract_apartment_info(self, url: str) -> Dict[str, Any]:
        """
        Extract apartment information from booking.com URL using the exact original scraper code
        """
        self._log_message(f"Starting to scrape: {url}")

        self.driver.get(url)
        self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(3)  # Wait only 1 second as requested

        # Check if job should be stopped after page load
        if self.current_job_id and self._should_stop_job(self.current_job_id):
            self._log_message(f"Job {self.current_job_id} was stopped by user, returning empty hotel data", "INFO")
            return {}

        soup = BeautifulSoup(self.driver.page_source, 'html.parser')

        address_info = \
            soup.find("div", {"data-testid": "PropertyHeaderAddressDesktop-wrapper"}).find("button").find(
                "div").contents[
                0].strip()
        try:
            region = self.driver.page_source.split("region_name: ")[1].split(",")[0].replace("'", "")
        except:
            region = None
        postalCode = ""
        address = address_info
        addressCountry = "المملكة العربية السعودية"

        # Hotel title
        try:
            title = soup.find("div", id="hp_hotel_name").find("h2").text.strip()
        except:
            title = None

        # Latitude and Longitude
        try:
            lat, lon = soup.find("a", id="map_trigger_header")["data-atlas-latlng"].split(",")
        except:
            lat = lon = None

        # Image links
        try:
            images = soup.find("div", id="photo_wrapper").find_all("img")
            image_links = [img["src"].replace("max500", "max1000").replace("max300", "max1000") for img in images]
        except:
            image_links = []

        # Description
        try:
            description = soup.find("p", {"data-testid": "property-description"}).text.strip()
        except:
            description = None

        # Most famous facilities
        try:
            most_famous_facilities = soup.find("div",
                                               {"data-testid": "property-most-popular-facilities-wrapper"}).find_all(
                "li")
            most_famous_facilities_text = {facility.text: str(facility.find("svg")) for facility in
                                           most_famous_facilities}
        except:
            most_famous_facilities_text = {}

        # All facilities
        try:
            all_facilities = soup.find("div", id="hp_facilities_box").find("div", {
                "data-testid": "property-section--content"}).find_all("div",
                                                                      {"data-testid": "facility-group-container"})
            all_facilities_text = {
                str(facility.find("h3").text.strip()): {
                    "svg": str(facility.find("h3").find("svg")),
                    "sub_facilities": {str(li.text.strip()): str(li.find("svg")) for li in facility.find_all("li")}
                }
                for facility in all_facilities
            }
            print("all_facilities_text", all_facilities_text)
        except:
            all_facilities_text = {}

        # Rooms data
        rooms_data = []

        rows = soup.find("div", id="maxotelRoomArea").find("table").find_all("tr")
        wait = WebDriverWait(self.driver, 10)
        div = wait.until(EC.presence_of_element_located((By.ID, "maxotelRoomArea")))

        # Now find all the <tr> elements within the <table> inside the div
        selenium_rows = div.find_element(By.TAG_NAME, "table").find_elements(By.TAG_NAME, "tr")
        print("Number of selenium rows ", len(selenium_rows))

        for row, selenium_row in zip(rows[1:], selenium_rows[1:]):
            try:
                selenium_row.find_element(By.TAG_NAME, "a").click()
                time.sleep(1)
                rp_content_div = wait.until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, 'div[data-testid="rp-content"]')))

                # Get the outer HTML of the element as a string
                content_html = rp_content_div.get_attribute("outerHTML")

                # Parse it with BeautifulSoup
                content_soup = BeautifulSoup(content_html, "html.parser")
                room_info = {}

                try:
                    room_name_tag = row.find("th").find("span").text.strip()
                    room_info["room_name"] = room_name_tag
                except:
                    pass

                try:
                    bed_type_tag = row.find("th").find_all('div', recursive=False)[-1]
                    if bed_type_tag:
                        room_info["bed_type"] = bed_type_tag.get_text(strip=True)
                except:
                    pass
                try:
                    adult_count = len(row.find_all("span", {"data-testid": "adults-icon"}))
                except:
                    adult_count = 2
                try:
                    children_count = len(row.find_all("span", {"data-testid": "kids-icon"}))
                except:
                    children_count = 0
                try:
                    td_number = int(row.find("td").text.split("×")[1].replace("+", ""))
                    adult_count = td_number
                except:
                    pass

                room_info["adult_count"] = adult_count
                room_info["children_count"] = children_count
                room_info["content_text"] = {}
                try:
                    room_info["content_text"]["مساحة الغرفة"] = content_soup.find('div',
                                                                                  {'data-testid': 'rp-room-size'}).text
                except:
                    room_info["content_text"]["مساحة الغرفة"] = None
                    print("Room with no area ")
                try:
                    room_info["content_text"]["وصف الغرفة"] = content_soup.find('div',
                                                                                {'data-testid': 'rp-description'}).text
                except:
                    room_info["content_text"]["وصف الغرفة"] = None
                    print("Room with no Desc ")

                    # Extract facilities list
                try:
                    facilities_ul = content_soup.find(self.has_bathroom_header).find('ul', {'data-testid': 'rp-facilities'})
                    if facilities_ul:
                        facilities = [li.find('span', class_='beb5ef4fb4').text.strip() for li in
                                      facilities_ul.find_all('li')]
                        room_info["content_text"]["الحمام"] = facilities
                    else:
                        room_info["content_text"]["الحمام"] = []
                except:
                    room_info["content_text"]["الحمام"] = []

                try:
                    facilities_ul = content_soup.find(self.has_furnature_header).find('ul',
                                                                                      {'data-testid': 'rp-facilities'})
                    if facilities_ul:
                        facilities = [li.find('span', class_='beb5ef4fb4').text.strip() for li in
                                      facilities_ul.find_all('li')]
                        room_info["content_text"]["المرافق المتوفرة"] = facilities
                    else:
                        room_info["content_text"]["المرافق المتوفرة"] = []
                except Exception as e:
                    print("مرافق الشقة", e)
                    room_info["content_text"]["المرافق المتوفرة"] = []

                try:
                    facilities_ul = content_soup.find(self.has_cooking_header).find('ul', {'data-testid': 'rp-facilities'})
                    if facilities_ul:
                        facilities = [li.find('span', class_='beb5ef4fb4').text.strip() for li in
                                      facilities_ul.find_all('li')]
                        room_info["content_text"]["المطبخ"] = facilities
                    else:
                        room_info["content_text"]["المطبخ"] = []
                except:
                    room_info["content_text"]["المطبخ"] = []

                try:
                    facilities_ul = content_soup.find(self.has_view_header).find('ul', {'data-testid': 'rp-facilities'})
                    if facilities_ul:
                        facilities = [li.find('span', class_='beb5ef4fb4').text.strip() for li in
                                      facilities_ul.find_all('li')]
                        room_info["content_text"]["الإطلالة"] = facilities
                    else:
                        room_info["content_text"]["الإطلالة"] = []
                except:
                    room_info["content_text"]["الإطلالة"] = []

                room_info["content_text"]["سياسة التدخين"] = \
                    content_soup.find('section', {'class': 'b7f1f9eb58'}).find_all('span')[1].text.strip()

                highlights_container = content_soup.find('div', {'data-testid': 'rp-highlights-test'})
                if not highlights_container:
                    room_info["content_text"]["المعلومات المهمه"] = {}
                else:
                    # Extract all elements that contain text and SVG icons
                    highlight_elements = highlights_container.find_all(['div', 'span'], recursive=True)
                    room_info["content_text"]["المعلومات المهمه"] = {}
                    for element in highlight_elements:
                        # Look for elements that have both text and SVG
                        text_span = element.find('span', class_='beb5ef4fb4')
                        svg_element = element.find('svg')

                        if text_span and svg_element:
                            # Get the Arabic text
                            arabic_text = text_span.get_text(strip=True)
                            # Get the SVG as string
                            svg_string = str(svg_element)
                            # Add to the highlights dictionary
                            if arabic_text and svg_string:
                                room_info["content_text"]["المعلومات المهمه"][arabic_text] = svg_string

                li_elements = content_soup.find_all('li', {'aria-roledescription': 'slide', 'role': 'group'})
                image_urls = []
                for li in li_elements:
                    # Find div with style attribute containing background-image
                    div = li.find('div', style=True)
                    if div and 'background-image' in div['style']:
                        # Extract URL from background-image: url("...") using regex
                        style_content = div['style']
                        #print("style_content", style_content)
                        url_match = re.search(r'url\("([^"]+)"\)', style_content)
                        if url_match:
                            # Decode HTML entities
                            url_img = url_match.group(1).replace('&amp;', '&')
                            image_urls.append(url_img)
                room_info["content_text"]["images_urls"] = image_urls[0:5]

                dialog_div = wait.until(
                    EC.presence_of_element_located(
                        (By.CSS_SELECTOR, 'div[role="dialog"].a9f1d9ba2c.f67e3e9cde.e76a03136a.c99c8fdd99.a3a4d85eff'))
                )
                button = dialog_div.find_element(By.CSS_SELECTOR,
                                                 "button.de576f5064.b46cd7aad7.e26a59bb37.c295306d66.c7a901b0e7.daf5d4cb1c")
                button.click()
                time.sleep(0.5)

                rooms_data.append(room_info)
            except Exception as e:
                print("pass scraping room ",e)

        # Rating stars
        try:
            stars = len(soup.find("span", {"data-testid": "rating-squares"}).find_all("svg"))
        except:
            stars = None

        # Step 1: Find the review score component div
        try:
            review_div = soup.find('div', attrs={'data-testid': 'review-score-component'})
            # Step 2: Extract the rating value
            rating_value = review_div.find('div', class_='f63b14ab7a dff2e52086').text.strip()
            # Step 3: Extract the rating text
            rating_text = review_div.find('span', class_='f63b14ab7a f546354b44 becbee2f63').text.strip()
        except:
            rating_value = rating_text = None

        # Final dictionary
        hotel_data = {
            "title": title,
            "address": address,
            "region": region,
            "postalCode": postalCode,
            "addressCountry": addressCountry,
            "latitude": lat,
            "longitude": lon,
            "description": description,
            "stars": stars,
            "image_links": image_links[0:5] if image_links else [],
            "most_famous_facilities": most_famous_facilities_text,
            "all_facilities": all_facilities_text,
            "rooms": rooms_data,
            "rating_value": rating_value,
            "rating_text": rating_text,
            "url": url
        }

        self._log_message(f"Successfully scraped: {title}")
        return hotel_data
    

    def save_hotel_to_csv(self, hotel_data: Dict[str, Any]) -> None:
        """Save a single hotel to CSV file"""
        try:
            # Create CSV file path without timestamp
            if not self.current_csv_file:
                self.current_csv_file = os.path.join(self.csv_directory, "booking_hotels.csv")
            
            # Prepare hotel data for CSV
            csv_row = {
                'title': hotel_data.get('title'),
                'address': hotel_data.get('address'),
                'region': hotel_data.get('region'),
                'postalCode': hotel_data.get('postalCode'),
                'addressCountry': hotel_data.get('addressCountry'),
                'latitude': hotel_data.get('latitude'),
                'longitude': hotel_data.get('longitude'),
                'description': hotel_data.get('description'),
                'stars': hotel_data.get('stars'),
                'rating_value': hotel_data.get('rating_value'),
                'rating_text': hotel_data.get('rating_text'),
                'url': hotel_data.get('url'),
                'image_links': json.dumps(hotel_data.get('image_links', []), ensure_ascii=False),
                'most_famous_facilities': json.dumps(hotel_data.get('most_famous_facilities', {}), ensure_ascii=False),
                'all_facilities': json.dumps(hotel_data.get('all_facilities', {}), ensure_ascii=False),
                'rooms': json.dumps(hotel_data.get('rooms', []), ensure_ascii=False),
                'scraped_at': datetime.now().isoformat()
            }
            
            # Determine file mode - write header if this is the first hotel in the session
            if len(self.scraped_hotels) == 0:
                file_mode = 'w'  # Write mode for first hotel
                write_header = True
            else:
                file_mode = 'a'  # Append mode for subsequent hotels
                write_header = False
            
            # Write to CSV
            with open(self.current_csv_file, file_mode, newline='', encoding='utf-8') as csvfile:
                fieldnames = csv_row.keys()
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                
                if write_header:
                    writer.writeheader()
                
                writer.writerow(csv_row)
            
            self._log_message(f"Hotel saved to CSV: {hotel_data.get('title')}")
            
        except Exception as e:
            self._log_message(f"Error saving hotel to CSV: {str(e)}", "ERROR")
            raise

    def import_csv_to_database(self, csv_file: str = None) -> int:
        """Import CSV data to database"""
        try:
            if not csv_file:
                csv_file = self.current_csv_file
            
            if not csv_file or not os.path.exists(csv_file):
                self._log_message(f"CSV file not found: {csv_file}", "ERROR")
                return 0
            
            self._log_message(f"Importing CSV data to database: {csv_file}")
            imported_count = self.database_service.import_hotels_from_csv(csv_file)
            self._log_message(f"Successfully imported {imported_count} hotels to database")
            return imported_count
            
        except Exception as e:
            self._log_message(f"Error importing CSV to database: {str(e)}", "ERROR")
            raise

    def run_scraping(self, urls: List[str] = None, csv_file: str = None, job_id: int = None) -> Dict[str, Any]:
        """Run the scraping process: CSV first, then database import"""
        try:
            # Reset for new scraping session
            self.current_csv_file = None
            self.scraped_hotels = []
            self.current_job_id = job_id
            
            # Determine URL source
            if urls is None:
                if csv_file:
                    urls = self.read_urls_from_csv(csv_file)
                else:
                    urls = self.read_urls_from_csv()  # Use default CSV
            
            if not urls:
                self._log_message("No URLs to process", "ERROR")
                return {"success": False, "message": "No URLs to process"}
                
            # Setup driver
            self._setup_driver()
            
            # Initialize counters
            scraped_count = 0
            failed_count = 0
            
            self._log_message(f"Starting scraping process for {len(urls)} URLs")
            
            # Process each URL
            for i, url in enumerate(urls):
                # Check if job should be stopped before each URL
                if self.current_job_id and self._should_stop_job(self.current_job_id):
                    self._log_message(f"Job {self.current_job_id} was stopped by user, exiting scraping", "INFO")
                    return {"success": False, "status": "STOPPED", "message": "Job stopped by user"}
                
                try:
                    self._log_message(f"Processing URL {i+1}/{len(urls)}: {url}")
                    
                    # Extract hotel data
                    hotel_data = self.extract_apartment_info(url)
                    
                    # Check if job should be stopped after scraping
                    if self.current_job_id and self._should_stop_job(self.current_job_id):
                        self._log_message(f"Job {self.current_job_id} was stopped by user, exiting scraping", "INFO")
                        return {"success": False, "status": "STOPPED", "message": "Job stopped by user"}
                    
                    # Save to CSV immediately
                    self.save_hotel_to_csv(hotel_data)
                    self.scraped_hotels.append(hotel_data)
                    
                    scraped_count += 1
                    self._log_message(f"Successfully scraped: {hotel_data.get('title')}")
                    
                    # Small delay between requests
                    time.sleep(3)
                    
                except Exception as e:
                    failed_count += 1
                    self._log_message(f"Error processing URL {url}: {str(e)}", "ERROR")
                    continue
            
            # After scraping all URLs, import CSV to database
            if scraped_count > 0:
                self._log_message("Scraping completed. Importing CSV data to database...")
                imported_count = self.import_csv_to_database()
                
                result = {
                    "success": True,
                    "message": f"Scraping completed successfully",
                    "total_urls": len(urls),
                    "scraped_count": scraped_count,
                    "failed_count": failed_count,
                    "imported_count": imported_count,
                    "csv_file": self.current_csv_file
                }
                
                self._log_message(f"Process completed: {scraped_count} scraped, {imported_count} imported to database")
                return result
            else:
                return {"success": False, "message": "No hotels were scraped successfully"}
            
        except Exception as e:
            self._log_message(f"Scraping process failed: {str(e)}", "ERROR")
            return {"success": False, "message": f"Scraping failed: {str(e)}"}
            
        finally:
            # Clean up driver
            if self.driver:
                self.driver.quit()
                self._log_message("Chrome driver closed")

    def get_csv_files(self) -> List[str]:
        """Get list of available CSV files"""
        try:
            csv_files = []
            for filename in os.listdir(self.csv_directory):
                if filename.endswith('.csv') and 'booking_hotels' in filename:
                    csv_files.append(os.path.join(self.csv_directory, filename))
            return sorted(csv_files, reverse=True)  # Most recent first
        except Exception as e:
            self._log_message(f"Error getting CSV files: {str(e)}", "ERROR")
            return []

    def get_stats(self) -> Dict[str, Any]:
        """Get scraping statistics"""
        try:
            csv_files = self.get_csv_files()
            db_count = self.database_service.get_hotel_count()
            
            return {
                "database_hotels": db_count,
                "csv_files_count": len(csv_files),
                "latest_csv": csv_files[0] if csv_files else None,
                "current_session_scraped": len(self.scraped_hotels)
            }
        except Exception as e:
            self._log_message(f"Error getting stats: {str(e)}", "ERROR")
            return {}

    def close(self):
        """Close database connection"""
        if self.database_service:
            self.database_service.close() 