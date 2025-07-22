#!/usr/bin/env python3
"""
Main scraper orchestrator that coordinates both link scraping and hotel data scraping.
This script provides options to either update hotel links or use existing CSV data.
"""

import os
import sys
import argparse
import logging
from datetime import datetime
from typing import Optional

# Add the parent directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.link_scraper_service import LinkScraperService
from services.BookingHotelsScraper import BookingScraperIntegration
from services.database_service import DatabaseService
from models import ScrapingJob
from database import SessionLocal

# Setup logging with custom format (no timestamps)
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('main_scraper.log', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)

class MainScraperOrchestrator:
    """Main orchestrator for coordinating both scrapers"""
    
    def __init__(self):
        self.link_scraper = LinkScraperService()
        self.booking_scraper = BookingScraperIntegration()
        self.database_service = DatabaseService()
        
    def _log_message(self, message: str, level: str = "INFO"):
        """Log message to console and file"""
        try:
            clean_message = message.replace('\n', ' ').strip()
            print(f"[{level}] {clean_message}")
            logger.log(getattr(logging, level), clean_message)
        except Exception as e:
            print(f"[ERROR] Failed to log message: {str(e)}")
    
    def _create_scraping_job(self, job_type: str, description: str) -> int:
        """Create a new scraping job in the database"""
        try:
            session = SessionLocal()
            job = ScrapingJob(
                status="PENDING",
                progress=0.0,
                message=description,
                urls_count=0,
                scraped_count=0,
                failed_count=0
            )
            session.add(job)
            session.commit()
            job_id = job.id
            session.close()
            self._log_message(f"Created scraping job {job_id} for: {description}")
            return job_id
        except Exception as e:
            self._log_message(f"Error creating scraping job: {str(e)}", "ERROR")
            return None
    
    def check_existing_links(self) -> bool:
        """Check if booking links CSV exists and has data"""
        csv_file = "data/csv/booking_links.csv"
        try:
            if not os.path.exists(csv_file):
                return False
                
            with open(csv_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                # Check if file has more than just header
                return len(lines) > 1
                
        except Exception as e:
            self._log_message(f"Error checking existing links: {str(e)}", "ERROR")
            return False
    
    def run_link_scraping(self, force_update: bool = False) -> bool:
        """Run link scraping job"""
        try:
            # Check if we need to update links
            if not force_update and self.check_existing_links():
                self._log_message("Existing links found in CSV. Skipping link scraping.")
                return True
                
            self._log_message("Starting link scraping process...")
            
            # Create job in database
            job_id = self._create_scraping_job("LINK_SCRAPING", "Hotel links scraping job")
            if not job_id:
                self._log_message("Failed to create link scraping job", "ERROR")
                return False
            
            # Run link scraping
            result = self.link_scraper.run_link_scraping_job(job_id)
            
            if result.get("status") == "COMPLETED":
                self._log_message(f"Link scraping completed successfully. Found {result.get('total_links', 0)} links")
                return True
            else:
                self._log_message(f"Link scraping failed: {result.get('error', 'Unknown error')}", "ERROR")
                return False
                
        except Exception as e:
            self._log_message(f"Error in link scraping: {str(e)}", "ERROR")
            return False
    
    def run_hotel_scraping(self, csv_file: Optional[str] = None) -> bool:
        """Run hotel data scraping"""
        try:
            self._log_message("Starting hotel data scraping process...")
            
            # Use default CSV if none specified
            if csv_file is None:
                csv_file = "data/csv/booking_links.csv"
            
            # Check if CSV exists
            if not os.path.exists(csv_file):
                self._log_message(f"CSV file not found: {csv_file}", "ERROR")
                return False
            
            # Create job in database for tracking
            job_id = self._create_scraping_job("HOTEL_SCRAPING", "Hotel data scraping from CSV")
            if not job_id:
                self._log_message("Failed to create hotel scraping job", "ERROR")
                return False
            
            # Run hotel scraping with job_id for cancellation support
            result = self.booking_scraper.run_scraping(csv_file=csv_file, job_id=job_id)
            
            if result.get("success"):
                self._log_message("Hotel data scraping completed successfully")
                return True
            else:
                self._log_message(f"Hotel data scraping failed: {result.get('message', 'Unknown error')}", "ERROR")
                return False
            
        except Exception as e:
            self._log_message(f"Error in hotel scraping: {str(e)}", "ERROR")
            return False
    
    def run_complete_scraping(self, update_links: bool = False):
        """Run complete scraping process"""
        try:
            self._log_message("=" * 60)
            self._log_message("STARTING COMPLETE SCRAPING PROCESS")
            self._log_message("=" * 60)
            
            # Step 1: Link scraping
            if update_links:
                self._log_message("STEP 1: Updating hotel links...")
                if not self.run_link_scraping(force_update=True):
                    self._log_message("Link scraping failed, aborting process", "ERROR")
                    return False
            else:
                self._log_message("STEP 1: Checking existing hotel links...")
                if not self.run_link_scraping(force_update=False):
                    self._log_message("No existing links found and link scraping failed", "ERROR")
                    return False
            
            # Step 2: Hotel data scraping
            self._log_message("STEP 2: Scraping hotel data...")
            if not self.run_hotel_scraping():
                self._log_message("Hotel data scraping failed", "ERROR")
                return False
            
            self._log_message("=" * 60)
            self._log_message("COMPLETE SCRAPING PROCESS FINISHED SUCCESSFULLY")
            self._log_message("=" * 60)
            
            return True
            
        except Exception as e:
            self._log_message(f"Error in complete scraping process: {str(e)}", "ERROR")
            return False

def main():
    """Main function with command line arguments"""
    parser = argparse.ArgumentParser(description='Booking.com Scraper Orchestrator')
    parser.add_argument('--update-links', action='store_true', 
                       help='Force update hotel links (default: use existing links if available)')
    parser.add_argument('--links-only', action='store_true',
                       help='Only scrape hotel links, do not scrape hotel data')
    parser.add_argument('--hotels-only', action='store_true',
                       help='Only scrape hotel data from existing CSV')
    parser.add_argument('--csv-file', type=str, default=None,
                       help='Specify custom CSV file for hotel URLs (default: data/csv/booking_links.csv)')
    
    args = parser.parse_args()
    
    # Create orchestrator
    orchestrator = MainScraperOrchestrator()
    
    try:
        if args.links_only:
            # Only run link scraping
            orchestrator._log_message("Running link scraping only...")
            success = orchestrator.run_link_scraping(force_update=True)
            
        elif args.hotels_only:
            # Only run hotel scraping
            orchestrator._log_message("Running hotel scraping only...")
            success = orchestrator.run_hotel_scraping(csv_file=args.csv_file)
            
        else:
            # Run complete process
            success = orchestrator.run_complete_scraping(update_links=args.update_links)
        
        if success:
            orchestrator._log_message("Process completed successfully!", "INFO")
            exit(0)
        else:
            orchestrator._log_message("Process failed!", "ERROR")
            exit(1)
            
    except KeyboardInterrupt:
        orchestrator._log_message("Process interrupted by user", "WARN")
        exit(1)
    except Exception as e:
        orchestrator._log_message(f"Unexpected error: {str(e)}", "ERROR")
        exit(1)

if __name__ == "__main__":
    main() 