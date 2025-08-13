#!/usr/bin/env python3
"""
Test script to verify S3 functionality in hotel_data_parser.py works correctly
"""

import logging
from hotel_data_parser import HotelDataParser

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_s3_functionality():
    """Test S3 functionality in HotelDataParser."""
    logger.info("=== Testing S3 Functionality in HotelDataParser ===")
    
    # Database config (we won't use it for this test)
    db_config = {
        'host': '15.184.143.183',
        'port': '3306',
        'username': 'btd_secure',
        'password': 'UvAbryxBIyBHAmkWyviMgQPT0q5lLVLc',
        'database': 'btd_db'
    }
    
    # S3 configuration - same as in hotel_data_parser.py
    s3_config = {
        'access_key': 'AKIASG6MFOOFXQRVKWEA',
        'secret_key': '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',
        'bucket_name': 'bookingimages-public',
        'region': 'eu-north-1'
    }
    
    try:
        # Initialize parser with S3 config
        parser = HotelDataParser(db_config, s3_config)
        
        # Test S3 client initialization
        if parser.s3_client:
            logger.info("✅ S3 client initialized successfully!")
        else:
            logger.error("❌ S3 client initialization failed!")
            return False
        
        # Test image download and upload
        test_image_url = "https://cf.bstatic.com/xdata/images/hotel/max1024x768/576044366.jpg?k=b0dcb58fd68cb4c79f09c780d078d69ec31a7a2b4a940a2a670e6ce85a456e37&o="
        logger.info("Testing image download and upload...")
        
        # Test single image upload
        s3_url = parser.download_and_upload_image(test_image_url, hotel_id=999, image_index=0)
        
        if s3_url and s3_url != test_image_url:
            logger.info(f"✅ Image uploaded successfully!")
            logger.info(f"Original URL: {test_image_url}")
            logger.info(f"New S3 URL: {s3_url}")
            
            # Verify URL structure
            if 'eu-north-1' in s3_url:
                logger.info("✅ S3 URL has correct region!")
            else:
                logger.warning("⚠️ S3 URL doesn't contain expected region!")
                
            return True
        else:
            logger.error("❌ Image upload failed or returned original URL!")
            return False
            
    except Exception as e:
        logger.error(f"❌ Test failed with error: {e}")
        return False

if __name__ == "__main__":
    success = test_s3_functionality()
    
    if success:
        print("\n🎉 All tests passed! The hotel_data_parser S3 functionality is working correctly.")
    else:
        print("\n❌ Tests failed. Check the logs above for details.") 