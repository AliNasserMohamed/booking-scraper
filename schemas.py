from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional, Generic, TypeVar
from datetime import datetime

T = TypeVar('T')

class BaseResponse(BaseModel):
    class Config:
        from_attributes = True

class PaginatedResponse(BaseResponse, Generic[T]):
    items: List[T]
    total: int
    page: int
    size: int
    pages: int

class HotelResponse(BaseResponse):
    title: Optional[str] = None
    address: Optional[str] = None
    region: Optional[str] = None
    postalCode: Optional[str] = None
    addressCountry: Optional[str] = None
    latitude: Optional[str] = None
    longitude: Optional[str] = None
    description: Optional[str] = None
    stars: Optional[int] = None
    image_links: Optional[List[str]] = None
    most_famous_facilities: Optional[Dict[str, Any]] = None
    all_facilities: Optional[Dict[str, Any]] = None
    rooms: Optional[List[Dict[str, Any]]] = None
    rating_value: Optional[str] = None
    rating_text: Optional[str] = None
    url: Optional[str] = None

class ScrapingJobResponse(BaseResponse):
    id: int
    status: str
    progress: float
    message: Optional[str] = None
    urls_count: int
    scraped_count: int
    failed_count: int
    created_at: datetime
    updated_at: datetime

class ScrapingLogResponse(BaseResponse):
    id: int
    job_id: Optional[int] = None
    message: str
    log_level: str
    created_at: datetime

class ScrapingJobCreate(BaseModel):
    urls: List[str]
    description: Optional[str] = None

class StatsResponse(BaseResponse):
    total_hotels: int
    running_jobs: int
    failed_jobs: int 