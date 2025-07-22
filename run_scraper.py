 #!/usr/bin/env python3
"""
Simple script to run the booking scraper orchestrator
This script demonstrates how to use the main scraper orchestrator
"""

import os
import sys
from services.main_scraper_orchestrator import MainScraperOrchestrator

def main():
    """Main function with simple options"""
    print("Booking.com Scraper Orchestrator")
    print("=" * 40)
    print("1. Run complete scraping (use existing links if available)")
    print("2. Run complete scraping (force update links)")
    print("3. Only scrape hotel links")
    print("4. Only scrape hotel data from existing CSV")
    print("5. Exit")
    
    choice = input("\nEnter your choice (1-5): ").strip()
    
    orchestrator = MainScraperOrchestrator()
    
    try:
        if choice == "1":
            print("\n[INFO] Running complete scraping with existing links...")
            success = orchestrator.run_complete_scraping(update_links=False)
            
        elif choice == "2":
            print("\n[INFO] Running complete scraping with link updates...")
            success = orchestrator.run_complete_scraping(update_links=True)
            
        elif choice == "3":
            print("\n[INFO] Running link scraping only...")
            success = orchestrator.run_link_scraping(force_update=True)
            
        elif choice == "4":
            print("\n[INFO] Running hotel scraping only...")
            success = orchestrator.run_hotel_scraping()
            
        elif choice == "5":
            print("\n[INFO] Exiting...")
            return
            
        else:
            print("\n[ERROR] Invalid choice. Please select 1-5.")
            return
            
        if success:
            print("\n[SUCCESS] Process completed successfully!")
        else:
            print("\n[ERROR] Process failed!")
            
    except KeyboardInterrupt:
        print("\n[WARN] Process interrupted by user")
    except Exception as e:
        print(f"\n[ERROR] Unexpected error: {str(e)}")

if __name__ == "__main__":
    main() 