# Hotel Data Parser

A comprehensive Python script to parse hotel data from CSV files and insert it into a MySQL database.

## Features

- ✅ Parses complex CSV data with nested JSON structures
- ✅ Handles hotel information, facilities, images, and room data
- ✅ Automatically manages database relationships
- ✅ Checks for existing hotels by URL and replaces them
- ✅ Comprehensive error handling and logging
- ✅ Transaction-based operations for data integrity
- ✅ Supports UTF-8 encoding for Arabic text

## Database Schema

The parser works with the following tables:
- `properties`: Property types (hotel, apartment, etc.)
- `hotels`: Main hotel information
- `facilities`: Available facilities with icons
- `hotel_facility`: Junction table linking hotels to facilities
- `images`: Hotel and room images
- `rooms`: Room details with JSON content

## Installation

1. Install required dependencies:
```bash
pip install -r requirements.txt
```

2. Ensure your MySQL database is accessible and the schema is created.

3. (Optional) Test the parser before running on full data:
```bash
python test_parser.py
```

## Usage

### Method 1: Direct execution (Recommended)
```bash
# Run the parser directly
python hotel_data_parser.py
```

### Method 2: Using the main function
```python
from hotel_data_parser import parse_hotels_from_csv

# Parse hotels from CSV file
success = parse_hotels_from_csv('sample_hotels.csv')

if success:
    print("All hotels parsed successfully!")
else:
    print("Some errors occurred. Check logs for details.")
```

### Method 3: Using the parser class directly
```python
from hotel_data_parser import HotelDataParser

# Database configuration
db_config = {
    'host': '15.184.143.183',
    'port': '3306',
    'username': 'btd_secure',
    'password': 'UvAbryxBIyBHAmkWyviMgQPT0q5lLVLc',
    'database': 'btd_db'
}

# Initialize and use parser
parser = HotelDataParser(db_config)
parser.connect_to_database()
parser.parse_csv_file('sample_hotels.csv')
parser.close_connection()
```

## CSV Data Format

The CSV file should contain the following columns:
- `title`: Hotel name
- `address`: Hotel address
- `region`: Geographic region
- `postalCode`: Postal code
- `addressCountry`: Country
- `latitude`, `longitude`: GPS coordinates
- `description`: Hotel description
- `stars`: Star rating (1-5)
- `rating_value`: Numeric rating (0-10)
- `rating_text`: Rating text (e.g., "Excellent")
- `url`: Hotel booking URL
- `image_links`: JSON array of image URLs
- `most_famous_facilities`: JSON object with facility names and icons
- `all_facilities`: JSON object with nested facility structure
- `rooms`: JSON array with room details
- `scraped_at`: Timestamp when data was scraped

## Key Features

### Duplicate Handling
- The script checks for existing hotels using the `url` field
- If a hotel exists, it deletes all related data (facilities, images, rooms) and re-inserts the new data
- This ensures data consistency and prevents duplicates

### Facility Management
- Automatically creates new facilities if they don't exist
- Handles both "most famous" facilities and regular facilities
- Maintains facility categories and icons

### Room and Image Handling
- Stores room details as JSON in the `content_text` field
- Links room images to specific rooms
- Links hotel images to hotels

### Error Handling
- Uses database transactions to ensure data integrity
- Comprehensive logging for debugging
- Graceful handling of malformed JSON data

## Database Configuration

The script is pre-configured with your database settings:
- Host: `15.184.143.183`
- Port: `3306`
- Username: `btd_secure`
- Password: `UvAbryxBIyBHAmkWyviMgQPT0q5lLVLc`
- Database: `btd_db`

## Logging

The script provides detailed logging information:
- INFO: General progress updates
- WARNING: Non-critical issues (e.g., malformed JSON)
- ERROR: Critical errors that prevent data insertion

## Example Output

```
2025-01-23 10:30:00 - INFO - Successfully connected to MySQL database
2025-01-23 10:30:01 - INFO - Reading CSV file: sample_hotels.csv
2025-01-23 10:30:01 - INFO - Found 24 hotels in CSV file
2025-01-23 10:30:01 - INFO - Processing hotel 1/24
2025-01-23 10:30:01 - INFO - Found existing hotel with ID 1, deleting...
2025-01-23 10:30:02 - INFO - Inserted hotel with ID: 25
2025-01-23 10:30:02 - INFO - Inserted facilities for hotel ID: 25
2025-01-23 10:30:02 - INFO - Inserted 5 images for hotel ID: 25
2025-01-23 10:30:02 - INFO - Inserted 1 rooms for hotel ID: 25
2025-01-23 10:30:02 - INFO - Successfully processed hotel: شقق فندقية عصرية مودرن
...
2025-01-23 10:35:00 - INFO - Processing completed. Success: 24, Errors: 0
```

## Troubleshooting

### Common Issues

1. **Connection Error**: Check database credentials and network connectivity
2. **Encoding Issues**: Ensure CSV file is saved with UTF-8 encoding
3. **JSON Parse Errors**: Check CSV data format, especially JSON fields
4. **Memory Issues**: For large CSV files, consider processing in batches

### Debug Mode
To enable more detailed logging, modify the logging level:
```python
logging.basicConfig(level=logging.DEBUG)
```

## License

This script is provided as-is for parsing hotel booking data into MySQL databases. 