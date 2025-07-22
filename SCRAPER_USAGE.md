# Booking Scraper Usage Guide

This guide explains how to use the improved booking scraper system with better logging and orchestration.

## Files Overview

### Core Scraper Files
- **`services/link_scraper_service.py`** - Scrapes hotel links from cities and saves to CSV
- **`services/BookingHotelsScraper.py`** - Scrapes detailed hotel information from URLs
- **`services/main_scraper_orchestrator.py`** - Orchestrates both scrapers with various options

### Usage Files
- **`run_scraper.py`** - Simple interactive script to run the scrapers
- **`services/cities.txt`** - List of cities to scrape hotel links from

### Data Files
- **`data/csv/booking_links.csv`** - Hotel links scraped from cities (constant filename)
- **`data/csv/booking_hotels_data.csv`** - Detailed hotel data (constant filename)

### Log Files
- **`link_scraper.log`** - Logs from link scraping operations
- **`booking_scraper.log`** - Logs from hotel data scraping operations
- **`main_scraper.log`** - Logs from the main orchestrator

## How to Use

### Option 1: Interactive Script (Recommended)
```bash
python run_scraper.py
```

This will show you a menu with options:
1. Run complete scraping (use existing links if available)
2. Run complete scraping (force update links)
3. Only scrape hotel links
4. Only scrape hotel data from existing CSV
5. Exit

### Option 2: Command Line Interface
```bash
# Run complete scraping with existing links
python -m services.main_scraper_orchestrator

# Force update links then scrape hotels
python -m services.main_scraper_orchestrator --update-links

# Only scrape hotel links
python -m services.main_scraper_orchestrator --links-only

# Only scrape hotel data from existing CSV
python -m services.main_scraper_orchestrator --hotels-only

# Use custom CSV file for hotel URLs
python -m services.main_scraper_orchestrator --hotels-only --csv-file "custom_links.csv"
```

### Option 3: Direct Python Usage
```python
from services.main_scraper_orchestrator import MainScraperOrchestrator

# Create orchestrator
orchestrator = MainScraperOrchestrator()

# Run complete scraping (with existing links)
success = orchestrator.run_complete_scraping(update_links=False)

# Or force update links
success = orchestrator.run_complete_scraping(update_links=True)

# Or run individual components
success = orchestrator.run_link_scraping(force_update=True)
success = orchestrator.run_hotel_scraping()
```

## Key Features

### 1. Improved Logging
- **No timestamps in console output** - cleaner display
- **Consistent log format** across all components
- **Separate log files** for each component
- **Both console and file logging** simultaneously

### 2. Constant File Names
- **`data/csv/booking_links.csv`** - always the same name for links
- **`data/csv/booking_hotels_data.csv`** - always the same name for hotel data
- **No timestamp-based filenames** - easier to find and use

### 3. Smart Link Management
- **Automatic detection** of existing links
- **Option to update or reuse** existing links
- **Efficient workflow** - skip link scraping if not needed

### 4. Flexible Options
- **Run complete workflow** or individual components
- **Custom CSV files** supported
- **Command line arguments** for automation
- **Interactive mode** for easy use

## Workflow Description

### Complete Scraping Process

1. **Link Scraping Phase**
   - Reads cities from `services/cities.txt`
   - Scrapes hotel links from booking.com for each city
   - Saves links to `data/csv/booking_links.csv`
   - Handles pagination automatically
   - Avoids duplicate links

2. **Hotel Data Scraping Phase**
   - Reads URLs from `data/csv/booking_links.csv`
   - Scrapes detailed hotel information for each URL
   - Saves data to database
   - Creates backup CSV at `data/csv/booking_hotels_data.csv`
   - Handles errors gracefully

### Smart Link Management

- **First run**: Always scrapes links from cities
- **Subsequent runs**: Uses existing links unless `--update-links` is specified
- **Manual control**: Use `--links-only` or `--hotels-only` for specific tasks

## Configuration

### Cities List
Edit `services/cities.txt` to add or remove cities:
```
الرياض
جدة
الدمام
مكة المكرمة
المدينة المنورة
```

### Database Configuration
The scrapers use the existing database configuration from your project.

### Chrome Driver
The hotel scraper uses undetected Chrome driver for web scraping.

## Log Analysis

### Console Logs
```
[INFO] Starting link scraping process...
[INFO] Processing city: الرياض
[INFO] Found 50 links on page 1 for city الرياض
[INFO] Link scraping completed successfully. Found 1250 links
```

### File Logs
- Check `link_scraper.log` for link scraping details
- Check `booking_scraper.log` for hotel data scraping details
- Check `main_scraper.log` for orchestrator operations

## Error Handling

The system includes robust error handling:
- **Network errors** - retries and continues with next items
- **Missing files** - clear error messages
- **Database errors** - graceful degradation
- **User interruption** - clean shutdown with Ctrl+C

## Performance Tips

1. **Use existing links** when possible to save time
2. **Run link scraping during off-peak hours** for better success rates
3. **Monitor log files** for errors and blocked requests
4. **Use smaller city lists** for testing

## Troubleshooting

### Common Issues

1. **"cities.txt not found"**
   - Ensure `services/cities.txt` exists with city names

2. **"CSV file not found"**
   - Run link scraping first, or check file path

3. **Chrome driver errors**
   - Ensure Chrome browser is installed
   - Check if Chrome driver is compatible with your Chrome version

4. **Database connection errors**
   - Verify database configuration
   - Check database service is running

### Getting Help

Check the log files for detailed error messages and stack traces. Each component logs to its own file for easier debugging. 