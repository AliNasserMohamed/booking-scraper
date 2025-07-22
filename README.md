# Booking Scraper - Enhanced FastAPI Application

A comprehensive web scraping solution for booking.com hotels with FastAPI backend, single table structure, CSV-first approach, and real-time dashboard.

## 🚀 New Features

- **Single Table Structure**: Unified database schema with all hotel data in one table
- **CSV-First Approach**: Data is scraped to CSV first, then imported to database
- **Exact JSON Format**: API returns data in the exact format requested
- **Enhanced Pagination**: Efficient data retrieval with pagination support
- **Real-time Processing**: Background job processing for scraping tasks

## 📋 System Architecture

### Database Structure
The system now uses a single `hotels` table that stores all data including:
- Hotel information (title, address, region, coordinates, etc.)
- Room details (stored as JSON array)
- Facilities (stored as JSON objects)
- Images (stored as JSON array)
- Ratings and reviews

### Workflow
1. **Scraping**: BookingHotelsScraper extracts data and saves to CSV (one hotel per row)
2. **Storage**: CSV data is then imported to the database
3. **API**: FastAPI endpoints serve data in the exact JSON format requested
4. **Pagination**: Efficient pagination for large datasets

## 🛠️ Installation

### Prerequisites
- Python 3.9+
- Chrome browser (for web scraping)
- SQLite (default) or PostgreSQL

### Quick Setup

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd booking_scraper
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Initialize the system**
   ```bash
   python test_system.py
   ```

4. **Start the API server**
   ```bash
   python main.py
   ```

## 📊 API Endpoints

### Hotels Data
- `GET /api/hotels` - Get paginated list of hotels in exact JSON format
- `GET /api/hotels/{hotel_id}` - Get specific hotel details
- `GET /api/export/hotels` - Export all hotels to CSV

### Scraping Jobs
- `POST /api/scraping-jobs/start` - Start new scraping job (CSV-first approach)
- `GET /api/scraping-jobs` - Get paginated list of scraping jobs
- `GET /api/scraping-jobs/{job_id}` - Get specific job details
- `POST /api/scraping-jobs/{job_id}/stop` - Stop running job

### CSV Management
- `POST /api/csv/import` - Import CSV file to database
- `POST /api/csv/upload` - Upload CSV file for later import
- `GET /api/csv/files` - Get list of available CSV files

### System Management
- `GET /api/stats` - Get system statistics
- `GET /api/scraping/stats` - Get detailed scraping statistics
- `POST /api/database/backup` - Backup database to CSV
- `POST /api/database/reset` - Reset database (⚠️ WARNING: Deletes all data)

## 🔧 Usage Examples

### 1. Start a Scraping Job

```bash
curl -X POST "http://localhost:8000/api/scraping-jobs/start" \
  -H "Content-Type: application/json" \
  -d '{
    "urls": [
      "https://www.booking.com/hotel/example1.html",
      "https://www.booking.com/hotel/example2.html"
    ]
  }'
```

### 2. Get Hotels with Pagination

```bash
curl "http://localhost:8000/api/hotels?page=1&size=10"
```

### 3. Import CSV to Database

```bash
curl -X POST "http://localhost:8000/api/csv/import?csv_file=data/csv/booking_hotels_20240101_120000.csv"
```

## 📊 JSON Response Format

The API returns hotel data in the exact format requested:

```json
[
  {
    "title": "استديو أنيق بدخول ذاتي",
    "address": "الخرج شارع ثقيف 8658 الطابق الاول, 11942 الخرج, المملكة العربية السعودية",
    "region": "منطقة الرياض",
    "postalCode": "11942",
    "addressCountry": "السعودية",
    "latitude": "24.1654412620605",
    "longitude": "47.3223412644691",
    "description": "يتميز مكان إقامة...",
    "stars": 3,
    "image_links": [
      "https://cf.bstatic.com/xdata/images/hotel/max1024x768/507796823.jpg",
      "https://cf.bstatic.com/xdata/images/hotel/max1000/507796856.jpg"
    ],
    "most_famous_facilities": {
      "مواقف سيارات مجانية": "<svg viewbox=\"0 0 24 24\"...>",
      "واي فاي مجاني": "<svg viewbox=\"0 0 24 24\"...>"
    },
    "all_facilities": {
      "موقف سيارات": {
        "svg": "<svg viewbox=\"0 0 24 24\"...>",
        "sub_facilities": {
          "يتوفر موقف مجاني": "<svg viewbox=\"0 0 24 24\"...>"
        }
      }
    },
    "rooms": [
      {
        "room_name": "شقة استوديو",
        "bed_type": "1 سرير مزدوج كبير",
        "adult_count": 2,
        "children_count": 1,
        "content_text": {
          "مساحة الغرفة": "مساحة الشقة: 60 م²",
          "وصف الغرفة": "This apartment is comprised of...",
          "الحمام": ["لوازم استحمام مجانية", "شطافة"],
          "المرافق المتوفرة": ["تكييف", "مقبس بجانب السرير"]
        }
      }
    ],
    "rating_value": "9.6",
    "rating_text": "استثنائي",
    "url": "https://www.booking.com/hotel/example.html"
  }
]
```

## 🔄 CSV-First Workflow

### 1. Scraping Process
```python
from services.BookingHotelsScraper import BookingScraperIntegration

# Initialize scraper
scraper = BookingScraperIntegration()

# URLs to scrape
urls = ["https://www.booking.com/hotel/example.html"]

# Run scraping (CSV first, then database)
result = scraper.run_scraping(urls)
```

### 2. CSV Structure
The CSV files contain one hotel per row with all data:
- Basic information (title, address, region, etc.)
- JSON fields (image_links, facilities, rooms)
- Metadata (scraped_at timestamp)

### 3. Database Import
```python
from services.database_service import DatabaseService

# Import CSV to database
db_service = DatabaseService()
imported_count = db_service.import_hotels_from_csv("path/to/hotels.csv")
```

## 🗂️ File Structure

```
booking_scraper/
├── main.py                     # FastAPI application
├── models.py                   # Single table SQLAlchemy models
├── schemas.py                  # Pydantic response schemas
├── database.py                 # Database configuration
├── test_system.py              # System testing script
├── services/
│   ├── BookingHotelsScraper.py # Enhanced scraper with CSV-first approach
│   ├── database_service.py     # Database operations
│   ├── scraper_service.py      # Scraping job management
│   └── link_scraper_service.py # Link collection service
├── data/
│   └── csv/                    # CSV files directory
│       ├── booking_links.csv   # Input URLs
│       └── booking_hotels_*.csv # Scraped data
├── templates/
│   └── dashboard.html          # Dashboard interface
└── static/                     # Static files
```

## 🔧 Configuration

### Database Settings
```python
# In database.py
DATABASE_URL = "sqlite:///booking_hotels.db"  # Default SQLite
# DATABASE_URL = "postgresql://user:pass@localhost/booking_hotels"  # PostgreSQL
```

### Scraper Settings
```python
# In BookingHotelsScraper.py
csv_directory = "data/csv"  # CSV output directory
```

## 📊 Monitoring and Logs

### System Statistics
```bash
curl "http://localhost:8000/api/stats"
```

### Scraping Progress
```bash
curl "http://localhost:8000/api/scraping/stats"
```

### CSV Files Management
```bash
curl "http://localhost:8000/api/csv/files"
```

## 🚨 Important Notes

1. **Data Migration**: The system automatically migrates from old multi-table structure to single table
2. **CSV Backup**: All scraped data is backed up to CSV files
3. **Memory Usage**: Large datasets are handled efficiently with pagination
4. **Error Handling**: Comprehensive error handling and logging
5. **Anti-Detection**: Scraper includes anti-detection measures

## 📈 Performance

- **Pagination**: Efficient handling of large datasets
- **Background Jobs**: Non-blocking scraping operations
- **CSV Processing**: Fast CSV import/export operations
- **Memory Management**: Optimized memory usage for large datasets

## 🔒 Security

- **Input Validation**: All inputs are validated
- **SQL Injection Protection**: SQLAlchemy ORM protection
- **File Upload Security**: Secure file upload handling
- **Rate Limiting**: Built-in request rate limiting

## 🆘 Troubleshooting

### Common Issues

1. **Database Connection Issues**
   ```bash
   python test_system.py  # Test database connectivity
   ```

2. **CSV Import Errors**
   ```bash
   # Check CSV format and encoding
   python -c "import pandas as pd; print(pd.read_csv('your_file.csv').head())"
   ```

3. **Scraping Issues**
   ```bash
   # Check Chrome driver installation
   python -c "import undetected_chrome as uc; uc.Chrome()"
   ```

### Debug Mode
```bash
# Enable debug logging
export LOG_LEVEL=DEBUG
python main.py
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests: `python test_system.py`
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🎉 Getting Started

1. **Test the system**: `python test_system.py`
2. **Start the API**: `python main.py`
3. **Access dashboard**: http://localhost:8000
4. **View API docs**: http://localhost:8000/docs
5. **Start scraping**: Use the dashboard or API endpoints

The system is now ready to scrape booking.com hotels with the CSV-first approach and return data in the exact JSON format you requested! 