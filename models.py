from sqlalchemy import Column, Integer, String, Float, Text, DateTime, JSON, Boolean
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class Hotel(Base):
    __tablename__ = 'hotels'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(255))
    address = Column(String(500))
    region = Column(String(100))
    postalCode = Column(String(20))
    addressCountry = Column(String(100))
    latitude = Column(String(50))  # Store as string to preserve exact format
    longitude = Column(String(50))  # Store as string to preserve exact format
    description = Column(Text)
    stars = Column(Integer)
    image_links = Column(JSON)  # List of image URLs
    most_famous_facilities = Column(JSON)  # Dict of facilities with SVG
    all_facilities = Column(JSON)  # Dict of facility categories
    rooms = Column(JSON)  # List of room objects
    rating_value = Column(String(10))  # Store as string to preserve format like "9.6"
    rating_text = Column(String(100))
    url = Column(String(500), unique=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class ScrapingJob(Base):
    __tablename__ = 'scraping_jobs'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    status = Column(String(50), default='PENDING')  # PENDING, RUNNING, COMPLETED, FAILED
    progress = Column(Float, default=0.0)
    message = Column(String(500))
    urls_count = Column(Integer, default=0)
    scraped_count = Column(Integer, default=0)
    failed_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class ScrapingLog(Base):
    __tablename__ = 'scraping_logs'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    job_id = Column(Integer, nullable=True)
    message = Column(Text)
    log_level = Column(String(20), default='INFO')  # INFO, WARNING, ERROR
    created_at = Column(DateTime, default=datetime.utcnow) 