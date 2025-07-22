import pandas as pd
import json
from sqlalchemy.orm import Session
from sqlalchemy import create_engine
from typing import List, Dict, Any
from datetime import datetime
import os
import logging

from models import Hotel, ScrapingLog, ScrapingJob
from database import SessionLocal, engine

logger = logging.getLogger(__name__)

class DatabaseService:
    """Service for database operations and CSV import/export"""
    
    def __init__(self):
        self.session = SessionLocal()
        self.csv_directory = "data/csv"
        os.makedirs(self.csv_directory, exist_ok=True)
    
    def save_hotel_data(self, hotel_data: Dict[str, Any]) -> Hotel:
        """Save hotel data to database"""
        try:
            # Check if hotel exists by URL
            existing_hotel = self.session.query(Hotel).filter(Hotel.url == hotel_data['url']).first()
            
            if existing_hotel:
                # Update existing hotel
                hotel = existing_hotel
                hotel.updated_at = datetime.utcnow()
            else:
                # Create new hotel
                hotel = Hotel()
                hotel.created_at = datetime.utcnow()
                hotel.updated_at = datetime.utcnow()
            
            # Update hotel fields
            hotel.title = hotel_data.get('title')
            hotel.address = hotel_data.get('address')
            hotel.region = hotel_data.get('region')
            hotel.postalCode = hotel_data.get('postalCode')
            hotel.addressCountry = hotel_data.get('addressCountry')
            hotel.latitude = hotel_data.get('latitude')
            hotel.longitude = hotel_data.get('longitude')
            hotel.description = hotel_data.get('description')
            hotel.stars = hotel_data.get('stars')
            hotel.rating_value = hotel_data.get('rating_value')
            hotel.rating_text = hotel_data.get('rating_text')
            hotel.url = hotel_data.get('url')
            hotel.image_links = hotel_data.get('image_links', [])
            hotel.most_famous_facilities = hotel_data.get('most_famous_facilities', {})
            hotel.all_facilities = hotel_data.get('all_facilities', {})
            hotel.rooms = hotel_data.get('rooms', [])
            
            if not existing_hotel:
                self.session.add(hotel)
            
            self.session.commit()
            self.session.refresh(hotel)
            
            return hotel
            
        except Exception as e:
            logger.error(f"Error saving hotel data: {str(e)}")
            self.session.rollback()
            raise
    
    def save_scraping_log(self, message: str, log_level: str = "INFO", job_id: int = None):
        """Save scraping log entry"""
        try:
            log = ScrapingLog(
                job_id=job_id,
                message=message,
                log_level=log_level,
                created_at=datetime.utcnow()
            )
            self.session.add(log)
            self.session.commit()
            
        except Exception as e:
            logger.error(f"Error saving scraping log: {str(e)}")
            self.session.rollback()
    
    def export_hotels_to_csv(self, hotels: List[Hotel]) -> str:
        """Export hotels to CSV file"""
        try:
            # Prepare data for CSV
            hotels_data = []
            for hotel in hotels:
                hotel_dict = {
                    'id': hotel.id,
                    'title': hotel.title,
                    'address': hotel.address,
                    'region': hotel.region,
                    'postalCode': hotel.postalCode,
                    'addressCountry': hotel.addressCountry,
                    'latitude': hotel.latitude,
                    'longitude': hotel.longitude,
                    'description': hotel.description,
                    'stars': hotel.stars,
                    'rating_value': hotel.rating_value,
                    'rating_text': hotel.rating_text,
                    'url': hotel.url,
                    'image_links': json.dumps(hotel.image_links, ensure_ascii=False) if hotel.image_links else '',
                    'most_famous_facilities': json.dumps(hotel.most_famous_facilities, ensure_ascii=False) if hotel.most_famous_facilities else '',
                    'all_facilities': json.dumps(hotel.all_facilities, ensure_ascii=False) if hotel.all_facilities else '',
                    'rooms': json.dumps(hotel.rooms, ensure_ascii=False) if hotel.rooms else '',
                    'created_at': hotel.created_at,
                    'updated_at': hotel.updated_at
                }
                hotels_data.append(hotel_dict)
            
            # Create DataFrame and save to CSV
            df = pd.DataFrame(hotels_data)
            csv_path = os.path.join(self.csv_directory, f"hotels_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv")
            df.to_csv(csv_path, index=False, encoding='utf-8')
            
            return csv_path
            
        except Exception as e:
            logger.error(f"Error exporting hotels to CSV: {str(e)}")
            raise
    
    def save_hotels_to_csv(self, hotels_data: List[Dict[str, Any]], filename: str = None) -> str:
        """Save scraped hotels data to CSV file (one hotel per row)"""
        try:
            if not filename:
                filename = f"booking_hotels_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            
            csv_path = os.path.join(self.csv_directory, filename)
            
            # Ensure directory exists
            os.makedirs(os.path.dirname(csv_path), exist_ok=True)
            
            # Prepare data for CSV
            flattened_data = []
            for hotel in hotels_data:
                hotel_row = {
                    'title': hotel.get('title'),
                    'address': hotel.get('address'),
                    'region': hotel.get('region'),
                    'postalCode': hotel.get('postalCode'),
                    'addressCountry': hotel.get('addressCountry'),
                    'latitude': hotel.get('latitude'),
                    'longitude': hotel.get('longitude'),
                    'description': hotel.get('description'),
                    'stars': hotel.get('stars'),
                    'rating_value': hotel.get('rating_value'),
                    'rating_text': hotel.get('rating_text'),
                    'url': hotel.get('url'),
                    'image_links': json.dumps(hotel.get('image_links', []), ensure_ascii=False),
                    'most_famous_facilities': json.dumps(hotel.get('most_famous_facilities', {}), ensure_ascii=False),
                    'all_facilities': json.dumps(hotel.get('all_facilities', {}), ensure_ascii=False),
                    'rooms': json.dumps(hotel.get('rooms', []), ensure_ascii=False),
                    'scraped_at': datetime.now().isoformat()
                }
                flattened_data.append(hotel_row)
            
            df = pd.DataFrame(flattened_data)
            df.to_csv(csv_path, index=False, encoding='utf-8')
            
            logger.info(f"Saved {len(hotels_data)} hotels to CSV: {csv_path}")
            return csv_path
            
        except Exception as e:
            logger.error(f"Error saving hotels to CSV: {str(e)}")
            raise
    
    def import_hotels_from_csv(self, csv_path: str):
        """Import hotels from CSV file to database"""
        try:
            df = pd.read_csv(csv_path, encoding='utf-8')
            
            logger.info(f"Importing {len(df)} hotels from CSV: {csv_path}")
            
            imported_count = 0
            for _, row in df.iterrows():
                try:
                    hotel_data = {
                        'title': row.get('title'),
                        'address': row.get('address'),
                        'region': row.get('region'),
                        'postalCode': row.get('postalCode'),
                        'addressCountry': row.get('addressCountry'),
                        'latitude': row.get('latitude'),
                        'longitude': row.get('longitude'),
                        'description': row.get('description'),
                        'stars': int(row.get('stars')) if pd.notna(row.get('stars')) else None,
                        'rating_value': row.get('rating_value'),
                        'rating_text': row.get('rating_text'),
                        'url': row.get('url'),
                        'image_links': json.loads(row.get('image_links', '[]')) if row.get('image_links') else [],
                        'most_famous_facilities': json.loads(row.get('most_famous_facilities', '{}')) if row.get('most_famous_facilities') else {},
                        'all_facilities': json.loads(row.get('all_facilities', '{}')) if row.get('all_facilities') else {},
                        'rooms': json.loads(row.get('rooms', '[]')) if row.get('rooms') else []
                    }
                    
                    # Save to database
                    self.save_hotel_data(hotel_data)
                    imported_count += 1
                    
                except Exception as e:
                    logger.error(f"Error importing hotel row: {str(e)}")
                    continue
            
            logger.info(f"Successfully imported {imported_count} hotels from CSV")
            return imported_count
            
        except Exception as e:
            logger.error(f"Error importing hotels from CSV: {str(e)}")
            raise
    
    def backup_database_to_csv(self) -> str:
        """Backup entire database to CSV file"""
        try:
            backup_dir = os.path.join(self.csv_directory, f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
            os.makedirs(backup_dir, exist_ok=True)
            
            # Export hotels
            hotels = self.session.query(Hotel).all()
            hotels_path = os.path.join(backup_dir, "hotels_backup.csv")
            df_hotels = pd.DataFrame([{
                'id': h.id, 'title': h.title, 'address': h.address, 'region': h.region,
                'postalCode': h.postalCode, 'addressCountry': h.addressCountry,
                'latitude': h.latitude, 'longitude': h.longitude, 'description': h.description,
                'stars': h.stars, 'rating_value': h.rating_value, 'rating_text': h.rating_text,
                'url': h.url, 'image_links': json.dumps(h.image_links, ensure_ascii=False),
                'most_famous_facilities': json.dumps(h.most_famous_facilities, ensure_ascii=False),
                'all_facilities': json.dumps(h.all_facilities, ensure_ascii=False),
                'rooms': json.dumps(h.rooms, ensure_ascii=False),
                'created_at': h.created_at, 'updated_at': h.updated_at
            } for h in hotels])
            df_hotels.to_csv(hotels_path, index=False, encoding='utf-8')
            
            logger.info(f"Database backup completed: {backup_dir}")
            return backup_dir
            
        except Exception as e:
            logger.error(f"Error backing up database: {str(e)}")
            raise
    
    def get_hotel_count(self) -> int:
        """Get total number of hotels in database"""
        try:
            return self.session.query(Hotel).count()
        except Exception as e:
            logger.error(f"Error getting hotel count: {str(e)}")
            return 0
    
    def close(self):
        """Close database session"""
        if self.session:
            self.session.close() 