#!/usr/bin/env python3
"""
S3 Upload Test Script - Test uploading images to S3 bucket
"""

import boto3
import requests
from PIL import Image
import io
import uuid
import os
from urllib.parse import urlparse
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# S3 configuration - using your actual credentials
s3_config = {
    'access_key': 'AKIASG6MFOOFXQRVKWEA',
    'secret_key': 'rPRP2KHC2fuNw3aqNcpNQoi20YK9TEta+PIcJZ6I',
    'bucket_name': 'bookingimages-public',
    'region': 'eu-north-1'
}

def init_s3_client():
    """Initialize S3 client."""
    try:
        s3_client = boto3.client(
            's3',
            aws_access_key_id=s3_config['access_key'],
            aws_secret_access_key=s3_config['secret_key'],
            region_name=s3_config['region']
        )
        logger.info("S3 client initialized successfully")
        return s3_client
    except Exception as e:
        logger.error(f"Error initializing S3 client: {e}")
        return None

def upload_image_from_url(image_url: str, s3_client, folder_name: str = "test") -> str:
    """
    Download image from URL and upload to S3.
    
    Args:
        image_url (str): URL of the image to download
        s3_client: Boto3 S3 client
        folder_name (str): Folder name in S3 bucket
        
    Returns:
        str: S3 URL of uploaded image
    """
    try:
        logger.info(f"Downloading image from: {image_url}")
        
        # Download image
        response = requests.get(image_url, timeout=30, headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        response.raise_for_status()
        
        # Verify it's actually an image
        try:
            img = Image.open(io.BytesIO(response.content))
            img.verify()
            logger.info(f"Image verified: {img.format}, {img.size}")
        except Exception:
            logger.error(f"Invalid image format for URL: {image_url}")
            return None
        
        # Generate unique filename
        parsed_url = urlparse(image_url)
        original_ext = os.path.splitext(parsed_url.path)[1] or '.jpg'
        filename = f"{folder_name}/{uuid.uuid4()}{original_ext}"
        
        logger.info(f"Uploading to S3 as: {filename}")
        
        # Upload to S3
        s3_client.put_object(
            Bucket=s3_config['bucket_name'],
            Key=filename,
            Body=response.content,
            ContentType=f"image/{original_ext[1:] if original_ext else 'jpeg'}",
            ACL='public-read'
        )
        
        # Generate S3 URL
        s3_url = f"https://{s3_config['bucket_name']}.s3.{s3_config['region']}.amazonaws.com/{filename}"
        
        logger.info(f"✅ Successfully uploaded! S3 URL: {s3_url}")
        return s3_url
        
    except requests.RequestException as e:
        logger.error(f"Error downloading image: {e}")
        return None
    except Exception as e:
        logger.error(f"Error uploading to S3: {e}")
        return None

def upload_local_image(local_path: str, s3_client, folder_name: str = "test") -> str:
    """
    Upload a local image file to S3.
    
    Args:
        local_path (str): Path to local image file
        s3_client: Boto3 S3 client
        folder_name (str): Folder name in S3 bucket
        
    Returns:
        str: S3 URL of uploaded image
    """
    try:
        if not os.path.exists(local_path):
            logger.error(f"Local file not found: {local_path}")
            return None
        
        logger.info(f"Uploading local image: {local_path}")
        
        # Get file extension
        _, ext = os.path.splitext(local_path)
        if not ext:
            ext = '.jpg'
        
        # Generate unique filename
        filename = f"{folder_name}/{uuid.uuid4()}{ext}"
        
        # Upload to S3
        with open(local_path, 'rb') as file:
            s3_client.put_object(
                Bucket=s3_config['bucket_name'],
                Key=filename,
                Body=file,
                ContentType=f"image/{ext[1:] if ext else 'jpeg'}",
                ACL='public-read'
            )
        
        # Generate S3 URL
        s3_url = f"https://{s3_config['bucket_name']}.s3.{s3_config['region']}.amazonaws.com/{filename}"
        
        logger.info(f"✅ Successfully uploaded! S3 URL: {s3_url}")
        return s3_url
        
    except Exception as e:
        logger.error(f"Error uploading local image to S3: {e}")
        return None

def test_bucket_access(s3_client):
    """Test if we can access the S3 bucket."""
    try:
        logger.info("Testing bucket access...")
        response = s3_client.head_bucket(Bucket=s3_config['bucket_name'])
        logger.info("✅ Bucket access successful!")
        return True
    except Exception as e:
        logger.error(f"❌ Bucket access failed: {e}")
        return False

def main():
    """Main function to test S3 upload."""
    logger.info("=== S3 Upload Test Script ===")
    logger.info(f"Bucket: {s3_config['bucket_name']}")
    logger.info(f"Region: {s3_config['region']}")
    
    # Initialize S3 client
    s3_client = init_s3_client()
    if not s3_client:
        logger.error("Failed to initialize S3 client")
        return
    
    # Test bucket access
    if not test_bucket_access(s3_client):
        return
    
    # Test with a sample Booking.com image URL
    test_image_url = "https://cf.bstatic.com/xdata/images/hotel/max1024x768/576044366.jpg?k=b0dcb58fd68cb4c79f09c780d078d69ec31a7a2b4a940a2a670e6ce85a456e37&o="
    
    logger.info("Testing image upload from URL...")
    s3_url = upload_image_from_url(test_image_url, s3_client, "test-upload")
    
    if s3_url:
        logger.info("🎉 Upload test successful!")
        logger.info(f"Original URL: {test_image_url}")
        logger.info(f"New S3 URL: {s3_url}")
        
        # Test if the uploaded image is accessible
        try:
            test_response = requests.head(s3_url, timeout=10)
            if test_response.status_code == 200:
                logger.info("✅ Uploaded image is publicly accessible!")
            else:
                logger.warning(f"⚠️ Uploaded image returned status: {test_response.status_code}")
        except Exception as e:
            logger.error(f"❌ Error testing uploaded image accessibility: {e}")
    else:
        logger.error("❌ Upload test failed!")

if __name__ == "__main__":
    main() 