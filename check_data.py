#!/usr/bin/env python3
"""
Script to check what hotel data has been saved
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from models import Hotel, Room
from database import SessionLocal, init_db

def check_saved_data():
    """Check what data has been saved to the database"""
    try:
        # Initialize database
        init_db()
        
        # Create session
        session = SessionLocal()
        
        # Count hotels
        hotel_count = session.query(Hotel).count()
        print(f"🏨 Total Hotels Saved: {hotel_count}")
        
        if hotel_count > 0:
            # Get some sample hotels
            hotels = session.query(Hotel).limit(5).all()
            
            print("\n📋 Sample Hotels:")
            print("-" * 60)
            
            for i, hotel in enumerate(hotels, 1):
                print(f"{i}. {hotel.title}")
                print(f"   📍 Address: {hotel.address}")
                print(f"   ⭐ Rating: {hotel.rating_value} ({hotel.rating_text})")
                print(f"   🌟 Stars: {hotel.stars}")
                print(f"   🔗 URL: {hotel.url}")
                
                # Count rooms for this hotel
                room_count = session.query(Room).filter(Room.hotel_id == hotel.id).count()
                print(f"   🛏️  Rooms: {room_count}")
                print()
            
            # Show total rooms
            total_rooms = session.query(Room).count()
            print(f"🛏️  Total Rooms Saved: {total_rooms}")
            
            # Show data file locations
            print("\n📁 Data Locations:")
            print(f"   Database: booking_hotels.db")
            if os.path.exists("data/csv/booking_hotels_data.csv"):
                print(f"   CSV Backup: data/csv/booking_hotels_data.csv ✅")
            else:
                print(f"   CSV Backup: data/csv/booking_hotels_data.csv ❌ (not found)")
                
        else:
            print("\n⚠️  No hotels found in database.")
            print("Make sure you've run the hotel scraper successfully.")
        
        session.close()
        
    except Exception as e:
        print(f"❌ Error checking data: {str(e)}")

def show_csv_info():
    """Show CSV file information"""
    csv_file = "data/csv/booking_hotels_data.csv"
    
    if os.path.exists(csv_file):
        try:
            import pandas as pd
            df = pd.read_csv(csv_file)
            
            print(f"\n📊 CSV File Info:")
            print(f"   File: {csv_file}")
            print(f"   Size: {os.path.getsize(csv_file):,} bytes")
            print(f"   Hotels: {len(df)} rows")
            print(f"   Columns: {len(df.columns)}")
            
            if len(df) > 0:
                print(f"\n🏨 Sample Hotels from CSV:")
                print("-" * 40)
                for i, row in df.head(3).iterrows():
                    print(f"{i+1}. {row.get('title', 'N/A')}")
                    print(f"   📍 {row.get('address', 'N/A')}")
                    
        except Exception as e:
            print(f"❌ Error reading CSV: {str(e)}")
    else:
        print(f"\n❌ CSV file not found: {csv_file}")

if __name__ == "__main__":
    print("🔍 Checking Saved Hotel Data")
    print("=" * 50)
    
    # Check database
    check_saved_data()
    
    # Check CSV
    show_csv_info()
    
    print("\n" + "=" * 50)
    print("💡 Tips:")
    print("• Use Excel/LibreOffice to open the CSV file")
    print("• Run 'python main.py' to start the web dashboard") 
    print("• Check booking_scraper.log for scraping details") 