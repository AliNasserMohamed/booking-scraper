#!/usr/bin/env python3
"""
Configuration file for Hotel Data Parser
Copy this file to 'config.py' and update with your actual credentials
"""

# Database configuration
DB_CONFIG = {
    'host': '15.184.143.183',
    'port': '3306',
    'username': 'btd_secure',
    'password': 'UvAbryxBIyBHAmkWyviMgQPT0q5lLVLc',
    'database': 'btd_db'
}

# S3 configuration (optional, for image upload)
# Set to None if you don't want to use S3 image upload
S3_CONFIG = {
    'access_key': 'YOUR_ACCESS_KEY_HERE',  # Replace with your actual S3 access key
    'secret_key': 'YOUR_SECRET_KEY_HERE',  # Replace with your actual S3 secret key
    'bucket_name': 'YOUR_BUCKET_NAME_HERE',  # Replace with your actual S3 bucket name
    'region': 'us-east-1'  # Replace with your actual S3 region
}

# To disable S3 image upload, uncomment the line below:
# S3_CONFIG = None

# Image processing settings
IMAGE_PROCESSING = {
    'max_width': 1920,  # Maximum image width
    'max_height': 1080,  # Maximum image height
    'quality': 85,  # JPEG quality (1-95)
    'format': 'JPEG',  # Output format
    'timeout': 30,  # Request timeout in seconds
    'delay_between_downloads': 0.5,  # Delay between image downloads in seconds
}

# Logging configuration
LOGGING_CONFIG = {
    'level': 'INFO',  # DEBUG, INFO, WARNING, ERROR, CRITICAL
    'format': '%(asctime)s - %(levelname)s - %(message)s',
    'file': None  # Set to filename if you want to log to file
} 