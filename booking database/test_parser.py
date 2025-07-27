#!/usr/bin/env python3
"""
Test script to validate hotel data parser functionality
"""

import pandas as pd
from hotel_data_parser import HotelDataParser
import logging

# Configure logging for test
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_csv_reading():
    """Test CSV file reading and basic data validation."""
    print("🧪 Testing CSV file reading...")
    
    try:
        # Try to read the CSV file
        df = pd.read_csv(
            'sample_hotels.csv', 
            encoding='utf-8',
            quotechar='"',
            escapechar='\\',
            index_col=0,
            na_values=['', 'nan', 'null', 'None'],
            keep_default_na=True,
            nrows=5  # Only read first 5 rows for testing
        )
        
        print(f"✅ Successfully read CSV file with {len(df)} rows")
        print(f"📊 Columns: {list(df.columns)}")
        
        # Check for required columns
        required_columns = ['title', 'url', 'latitude', 'longitude', 'image_links', 'most_famous_facilities', 'all_facilities', 'rooms']
        missing_columns = [col for col in required_columns if col not in df.columns]
        
        if missing_columns:
            print(f"⚠️  Missing columns: {missing_columns}")
        else:
            print("✅ All required columns present")
        
        return df
        
    except Exception as e:
        print(f"❌ Error reading CSV file: {e}")
        return None

def test_data_parsing(df):
    """Test data parsing functionality."""
    print("\n🧪 Testing data parsing...")
    
    # Initialize parser (without connecting to database)
    db_config = {
        'host': '15.184.143.183',
        'port': '3306',
        'username': 'btd_secure',  
        'password': 'UvAbryxBIyBHAmkWyviMgQPT0q5lLVLc',
        'database': 'btd_db'
    }
    
    parser = HotelDataParser(db_config)
    
    success_count = 0
    error_count = 0
    
    for index, row in df.iterrows():
        print(f"\n📋 Testing row {index + 1}: {row.get('title', 'Unknown')[:50]}...")
        
        # Test parsing
        hotel_data = parser.parse_csv_row(row)
        
        if hotel_data:
            print("✅ Row parsed successfully")
            
            # Validate key fields
            if hotel_data.get('title'):
                print(f"  📝 Title: {hotel_data['title'][:50]}...")
            else:
                print("  ⚠️  Missing title")
            
            if hotel_data.get('url'):
                print(f"  🔗 URL: {hotel_data['url'][:50]}...")
            else:
                print("  ⚠️  Missing URL")
            
            # Test image links parsing
            if hotel_data['image_links']:
                print(f"  🖼️  Images: {len(hotel_data['image_links'])} found")
            else:
                print("  ⚠️  No images found")
            
            # Test facilities parsing
            if hotel_data['most_famous_facilities']:
                print(f"  ⭐ Famous facilities: {len(hotel_data['most_famous_facilities'])} found")
            
            if hotel_data['all_facilities']:
                print(f"  🏨 All facilities: {len(hotel_data['all_facilities'])} categories found")
            
            # Test rooms parsing
            if hotel_data['rooms_data']:
                print(f"  🛏️  Rooms: {len(hotel_data['rooms_data'])} found")
            else:
                print("  ⚠️  No rooms found")
            
            success_count += 1
        else:
            print("❌ Failed to parse row")
            error_count += 1
    
    print(f"\n📊 Parsing Results: {success_count} successful, {error_count} errors")
    return success_count > 0

def test_database_connection():
    """Test database connection."""
    print("\n🧪 Testing database connection...")
    
    db_config = {
        'host': '15.184.143.183',
        'port': '3306',
        'username': 'btd_secure',
        'password': 'UvAbryxBIyBHAmkWyviMgQPT0q5lLVLc',
        'database': 'btd_db'
    }
    
    parser = HotelDataParser(db_config)
    
    try:
        if parser.connect_to_database():
            print("✅ Database connection successful")
            
            # Test if tables exist
            parser.cursor.execute("SHOW TABLES")
            tables = [table[0] for table in parser.cursor.fetchall()]
            
            required_tables = ['hotels', 'properties', 'facilities', 'hotel_facility', 'images', 'rooms']
            missing_tables = [table for table in required_tables if table not in tables]
            
            if missing_tables:
                print(f"⚠️  Missing tables: {missing_tables}")
            else:
                print("✅ All required tables exist")
            
            parser.close_connection()
            return True
        else:
            print("❌ Database connection failed")
            return False
            
    except Exception as e:
        print(f"❌ Database connection error: {e}")
        return False

def main():
    """Run all tests."""
    print("🚀 Hotel Data Parser - Test Suite")
    print("=" * 50)
    
    # Test 1: CSV Reading
    df = test_csv_reading()
    if df is None:
        print("\n❌ Cannot proceed with tests - CSV reading failed")
        return False
    
    # Test 2: Data Parsing
    parsing_success = test_data_parsing(df)
    if not parsing_success:
        print("\n❌ Data parsing tests failed")
        return False
    
    # Test 3: Database Connection
    db_success = test_database_connection()
    if not db_success:
        print("\n❌ Database connection tests failed")
        return False
    
    print("\n🎉 All tests passed! The parser should work correctly with your data.")
    print("\n💡 To run the full parser, execute:")
    print("   python hotel_data_parser.py")
    
    return True

if __name__ == "__main__":
    main() 