#!/usr/bin/env python3
"""
Hotel Data Parser - Parses hotel data from CSV and inserts into MySQL database
"""

import pandas as pd
import mysql.connector
from mysql.connector import Error
import json
import ast
from datetime import datetime
import logging
from typing import Dict, List, Optional, Any
import re

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class HotelDataParser:
    def __init__(self, db_config: Dict[str, str]):
        """Initialize the parser with database configuration."""
        self.db_config = db_config
        self.connection = None
        self.cursor = None
        
    def connect_to_database(self):
        """Establish connection to MySQL database."""
        try:
            self.connection = mysql.connector.connect(
                host=self.db_config['host'],
                port=int(self.db_config['port']),
                user=self.db_config['username'],
                password=self.db_config['password'],
                database=self.db_config['database'],
                charset='utf8mb4',
                use_unicode=True
            )
            self.cursor = self.connection.cursor(buffered=True)
            logger.info("Successfully connected to MySQL database")
            return True
        except Error as e:
            logger.error(f"Error connecting to MySQL database: {e}")
            return False
    
    def close_connection(self):
        """Close database connection."""
        if self.cursor:
            self.cursor.close()
        if self.connection:
            self.connection.close()
        logger.info("Database connection closed")
    
    def safe_json_loads(self, json_string: str) -> Any:
        """Safely parse JSON string, handling different formats."""
        if pd.isna(json_string) or json_string == '' or json_string is None or json_string == 'nan':
            return None
            
        # Convert to string if not already
        json_string = str(json_string).strip()
        
        # Handle empty or null-like strings
        if json_string in ['', '{}', '[]', 'null', 'None', 'nan']:
            return {} if json_string == '{}' else ([] if json_string == '[]' else None)
            
        try:
            # Try direct JSON parsing first
            return json.loads(json_string)
        except (json.JSONDecodeError, TypeError):
            try:
                # Try using ast.literal_eval for Python-like strings
                return ast.literal_eval(json_string)
            except (ValueError, SyntaxError):
                try:
                    # Handle cases where outer quotes might be missing
                    if not json_string.startswith(('{', '[', '"')):
                        return None
                    
                    # Try with eval as last resort (be careful with this in production)
                    # Only for trusted data sources
                    if json_string.startswith(('{', '[')):
                        return eval(json_string)
                except:
                    pass
                
                logger.warning(f"Could not parse JSON: {json_string[:100]}...")
                return None
    
    def get_or_create_property(self, property_type: str = 'hotel') -> int:
        """Get or create property ID for the given type."""
        # Check if property type exists
        self.cursor.execute("SELECT id FROM properties WHERE type = %s", (property_type,))
        result = self.cursor.fetchone()
        
        if result:
            return result[0]
        else:
            # Create new property type
            self.cursor.execute(
                "INSERT INTO properties (type) VALUES (%s)",
                (property_type,)
            )
            return self.cursor.lastrowid
    
    def get_or_create_facility(self, facility_name: str, icon_svg: str = None, category: str = None) -> int:
        """Get or create facility ID for the given facility."""
        # Check if facility exists
        self.cursor.execute("SELECT id FROM facilities WHERE name = %s", (facility_name,))
        result = self.cursor.fetchone()
        
        if result:
            return result[0]
        else:
            # Create new facility
            self.cursor.execute(
                "INSERT INTO facilities (name, category, icon_svg) VALUES (%s, %s, %s)",
                (facility_name, category, icon_svg)
            )
            return self.cursor.lastrowid
    
    def delete_existing_hotel(self, hotel_url: str):
        """Delete existing hotel and related data based on URL."""
        try:
            # Get hotel ID first
            self.cursor.execute("SELECT id FROM hotels WHERE url = %s", (hotel_url,))
            result = self.cursor.fetchone()
            
            if result:
                hotel_id = result[0]
                logger.info(f"Found existing hotel with ID {hotel_id}, deleting...")
                
                # Delete related data (foreign key constraints will handle this automatically)
                # But we'll do it explicitly for clarity
                self.cursor.execute("DELETE FROM hotel_facility WHERE hotel_id = %s", (hotel_id,))
                self.cursor.execute("DELETE FROM images WHERE hotel_id = %s", (hotel_id,))
                self.cursor.execute("DELETE FROM rooms WHERE hotel_id = %s", (hotel_id,))
                self.cursor.execute("DELETE FROM hotels WHERE id = %s", (hotel_id,))
                
                logger.info(f"Deleted existing hotel and related data for URL: {hotel_url}")
                
        except Error as e:
            logger.error(f"Error deleting existing hotel: {e}")
            raise
    
    def insert_hotel(self, hotel_data: Dict[str, Any]) -> int:
        """Insert hotel data and return hotel ID."""
        try:
            property_id = self.get_or_create_property('hotel')
            
            # Helper function to safely convert to numeric
            def safe_float(value):
                if value is None or value == '' or pd.isna(value):
                    return None
                try:
                    return float(value)
                except (ValueError, TypeError):
                    return None
            
            def safe_int(value):
                if value is None or value == '' or pd.isna(value):
                    return None
                try:
                    return int(float(value))  # Convert to float first to handle strings like "5.0"
                except (ValueError, TypeError):
                    return None
            
            # Prepare hotel data
            hotel_insert_data = (
                property_id,
                hotel_data.get('title'),
                hotel_data.get('address'),
                hotel_data.get('region'),
                hotel_data.get('postalCode'),
                hotel_data.get('addressCountry'),
                safe_float(hotel_data.get('latitude')),
                safe_float(hotel_data.get('longitude')),
                hotel_data.get('description'),
                safe_int(hotel_data.get('stars')),
                safe_float(hotel_data.get('rating_value')),
                hotel_data.get('rating_text'),
                hotel_data.get('url')
            )
            
            insert_query = """
                INSERT INTO hotels (property_id, title, address, region, postal_code, address_country, 
                                  latitude, longitude, description, stars, rating_value, rating_text, url)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            
            self.cursor.execute(insert_query, hotel_insert_data)
            hotel_id = self.cursor.lastrowid
            logger.info(f"Inserted hotel with ID: {hotel_id}")
            return hotel_id
            
        except Error as e:
            logger.error(f"Error inserting hotel: {e}")
            raise
    
    def insert_hotel_facilities(self, hotel_id: int, most_famous_facilities: Dict, all_facilities: Dict):
        """Insert hotel facilities."""
        try:
            # Process most famous facilities
            if most_famous_facilities:
                for facility_name, icon in most_famous_facilities.items():
                    facility_name = facility_name.strip()
                    if facility_name:
                        facility_id = self.get_or_create_facility(facility_name, icon)
                        
                        # Insert hotel-facility relationship
                        self.cursor.execute(
                            "INSERT INTO hotel_facility (hotel_id, facility_id, is_most_famous) VALUES (%s, %s, %s)",
                            (hotel_id, facility_id, 1)
                        )
            
            # Process all facilities
            if all_facilities:
                for category, facility_data in all_facilities.items():
                    if isinstance(facility_data, dict):
                        category_name = category.strip()
                        icon = facility_data.get('svg', '')
                        
                        # Insert main category facility
                        if category_name:
                            facility_id = self.get_or_create_facility(category_name, icon, 'main')
                            
                            # Check if not already inserted as most famous
                            self.cursor.execute(
                                "SELECT COUNT(*) FROM hotel_facility WHERE hotel_id = %s AND facility_id = %s",
                                (hotel_id, facility_id)
                            )
                            
                            if self.cursor.fetchone()[0] == 0:
                                self.cursor.execute(
                                    "INSERT INTO hotel_facility (hotel_id, facility_id, is_most_famous) VALUES (%s, %s, %s)",
                                    (hotel_id, facility_id, 0)
                                )
                        
                        # Process sub-facilities
                        sub_facilities = facility_data.get('sub_facilities', {})
                        if isinstance(sub_facilities, dict):
                            for sub_facility_name, sub_icon in sub_facilities.items():
                                sub_facility_name = sub_facility_name.strip()
                                if sub_facility_name:
                                    sub_facility_id = self.get_or_create_facility(sub_facility_name, sub_icon, 'sub')
                                    
                                    # Check if not already inserted
                                    self.cursor.execute(
                                        "SELECT COUNT(*) FROM hotel_facility WHERE hotel_id = %s AND facility_id = %s",
                                        (hotel_id, sub_facility_id)
                                    )
                                    
                                    if self.cursor.fetchone()[0] == 0:
                                        self.cursor.execute(
                                            "INSERT INTO hotel_facility (hotel_id, facility_id, is_most_famous) VALUES (%s, %s, %s)",
                                            (hotel_id, sub_facility_id, 0)
                                        )
            
            logger.info(f"Inserted facilities for hotel ID: {hotel_id}")
            
        except Error as e:
            logger.error(f"Error inserting hotel facilities: {e}")
            raise
    
    def insert_hotel_images(self, hotel_id: int, image_links: List[str]):
        """Insert hotel images."""
        try:
            if image_links:
                for image_url in image_links:
                    if image_url and image_url.strip():
                        self.cursor.execute(
                            "INSERT INTO images (hotel_id, image_url) VALUES (%s, %s)",
                            (hotel_id, image_url.strip())
                        )
                
                logger.info(f"Inserted {len(image_links)} images for hotel ID: {hotel_id}")
                
        except Error as e:
            logger.error(f"Error inserting hotel images: {e}")
            raise
    
    def insert_hotel_rooms(self, hotel_id: int, rooms_data: List[Dict]):
        """Insert hotel rooms."""
        try:
            if rooms_data:
                for room in rooms_data:
                    # Helper function for safe integer conversion
                    def safe_int_default(value, default=0):
                        if value is None or value == '' or pd.isna(value):
                            return default
                        try:
                            return int(float(value))
                        except (ValueError, TypeError):
                            return default
                    
                    room_insert_data = (
                        hotel_id,
                        room.get('room_name', ''),
                        room.get('bed_type', ''),
                        safe_int_default(room.get('adult_count'), 0),
                        safe_int_default(room.get('children_count'), 0),
                        json.dumps(room.get('content_text', {}), ensure_ascii=False) if room.get('content_text') else None
                    )
                    
                    insert_query = """
                        INSERT INTO rooms (hotel_id, room_name, bed_type, adult_count, children_count, content_text)
                        VALUES (%s, %s, %s, %s, %s, %s)
                    """
                    
                    self.cursor.execute(insert_query, room_insert_data)
                    room_id = self.cursor.lastrowid
                    
                    # Insert room images if available
                    room_images = room.get('content_text', {}).get('images_urls', [])
                    if room_images:
                        for image_url in room_images:
                            if image_url and image_url.strip():
                                self.cursor.execute(
                                    "INSERT INTO images (room_id, image_url) VALUES (%s, %s)",
                                    (room_id, image_url.strip())
                                )
                
                logger.info(f"Inserted {len(rooms_data)} rooms for hotel ID: {hotel_id}")
                
        except Error as e:
            logger.error(f"Error inserting hotel rooms: {e}")
            raise
    
    def parse_csv_row(self, row: pd.Series) -> Dict[str, Any]:
        """Parse a single CSV row into structured data."""
        try:
            # Helper function to safely get values and handle empty strings
            def safe_get(key, default=None):
                value = row.get(key, default)
                if pd.isna(value) or value == '' or value == 'nan':
                    return None
                return value
            
            # Parse JSON fields
            image_links = self.safe_json_loads(safe_get('image_links', '[]'))
            most_famous_facilities = self.safe_json_loads(safe_get('most_famous_facilities', '{}'))
            all_facilities = self.safe_json_loads(safe_get('all_facilities', '{}'))
            rooms_data = self.safe_json_loads(safe_get('rooms', '[]'))
            
            return {
                'title': safe_get('title'),
                'address': safe_get('address'),
                'region': safe_get('region'),
                'postalCode': safe_get('postalCode'),
                'addressCountry': safe_get('addressCountry'),
                'latitude': safe_get('latitude'),
                'longitude': safe_get('longitude'),
                'description': safe_get('description'),
                'stars': safe_get('stars'),
                'rating_value': safe_get('rating_value'),
                'rating_text': safe_get('rating_text'),
                'url': safe_get('url'),
                'image_links': image_links if isinstance(image_links, list) else [],
                'most_famous_facilities': most_famous_facilities if isinstance(most_famous_facilities, dict) else {},
                'all_facilities': all_facilities if isinstance(all_facilities, dict) else {},
                'rooms_data': rooms_data if isinstance(rooms_data, list) else []
            }
            
        except Exception as e:
            logger.error(f"Error parsing CSV row: {e}")
            return None
    
    def process_hotel_data(self, hotel_data: Dict[str, Any]) -> bool:
        """Process a single hotel's data."""
        try:
            # Start transaction
            self.connection.start_transaction()
            
            # Delete existing hotel if it exists
            if hotel_data.get('url'):
                self.delete_existing_hotel(hotel_data['url'])
            
            # Insert hotel
            hotel_id = self.insert_hotel(hotel_data)
            
            # Insert facilities
            self.insert_hotel_facilities(
                hotel_id, 
                hotel_data['most_famous_facilities'], 
                hotel_data['all_facilities']
            )
            
            # Insert images
            self.insert_hotel_images(hotel_id, hotel_data['image_links'])
            
            # Insert rooms
            self.insert_hotel_rooms(hotel_id, hotel_data['rooms_data'])
            
            # Commit transaction
            self.connection.commit()
            logger.info(f"Successfully processed hotel: {hotel_data.get('title', 'Unknown')}")
            return True
            
        except Exception as e:
            # Rollback transaction on error
            self.connection.rollback()
            logger.error(f"Error processing hotel data: {e}")
            return False
    
    def parse_csv_file(self, csv_file_path: str) -> bool:
        """Parse the entire CSV file and insert data into database."""
        try:
            # Read CSV file with proper handling of quoted fields
            logger.info(f"Reading CSV file: {csv_file_path}")
            df = pd.read_csv(
                csv_file_path, 
                encoding='utf-8',
                quotechar='"',
                escapechar='\\',
                index_col=0,  # Skip the first column (index)
                na_values=['', 'nan', 'null', 'None'],
                keep_default_na=True
            )
            logger.info(f"Found {len(df)} hotels in CSV file")
            
            success_count = 0
            error_count = 0
            
            # Process each row
            for index, row in df.iterrows():
                logger.info(f"Processing hotel {index + 1}/{len(df)}")
                
                # Parse row data
                hotel_data = self.parse_csv_row(row)
                
                if hotel_data:
                    # Process hotel data
                    if self.process_hotel_data(hotel_data):
                        success_count += 1
                    else:
                        error_count += 1
                else:
                    error_count += 1
                    logger.warning(f"Skipped row {index + 1} due to parsing errors")
            
            logger.info(f"Processing completed. Success: {success_count}, Errors: {error_count}")
            return error_count == 0
            
        except Exception as e:
            logger.error(f"Error reading CSV file: {e}")
            return False


def parse_hotels_from_csv(csv_file_path: str = 'sample_hotels.csv'):
    """
    Main function to parse hotels from CSV file and insert into database.
    
    Args:
        csv_file_path (str): Path to the CSV file containing hotel data
        
    Returns:
        bool: True if successful, False otherwise
    """
    
    # Database configuration
    db_config = {
        'host': '15.184.143.183',
        'port': '3306',
        'username': 'btd_secure',
        'password': 'UvAbryxBIyBHAmkWyviMgQPT0q5lLVLc',
        'database': 'btd_db'
    }
    
    # Initialize parser
    parser = HotelDataParser(db_config)
    
    try:
        # Connect to database
        if not parser.connect_to_database():
            logger.error("Failed to connect to database")
            return False
        
        # Parse CSV file
        result = parser.parse_csv_file(csv_file_path)
        
        return result
        
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return False
        
    finally:
        # Close database connection
        parser.close_connection()


if __name__ == "__main__":
    # Example usage
    success = parse_hotels_from_csv('sample_hotels.csv')
    
    if success:
        print("✅ Hotel data parsing completed successfully!")
    else:
        print("❌ Hotel data parsing completed with errors. Check logs for details.") 