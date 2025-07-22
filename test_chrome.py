#!/usr/bin/env python3
"""
Test script to verify Chrome connectivity in Docker container
"""

import sys
import os
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import undetected_chromedriver as uc

def test_chrome_connection():
    """Test Chrome connection with Docker-optimized settings"""
    
    print("Testing Chrome connection...")
    print(f"Display: {os.environ.get('DISPLAY', 'Not set')}")
    print(f"Chrome Binary: {os.environ.get('GOOGLE_CHROME_BIN', 'Not set')}")
    
    try:
        # Create Chrome options with Docker-optimized settings
        options = uc.ChromeOptions()
        
        # Essential Docker options
        options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--disable-remote-debugging")
        options.add_argument("--no-zygote")
        options.add_argument("--single-process")
        options.add_argument("--disable-ipc-flooding-protection")
        options.add_argument("--disable-logging")
        options.add_argument("--disable-crash-reporter")
        options.add_argument("--disable-extensions")
        options.add_argument("--disable-plugins")
        options.add_argument("--disable-background-networking")
        options.add_argument("--disable-default-apps")
        options.add_argument("--disable-sync")
        options.add_argument("--no-first-run")
        options.add_argument("--disable-hang-monitor")
        options.add_argument("--disable-prompt-on-repost")
        options.add_argument("--disable-domain-reliability")
        options.add_argument("--disable-client-side-phishing-detection")
        options.add_argument("--disable-component-extensions-with-background-pages")
        options.add_argument("--memory-pressure-off")
        
        # Cache and data directories
        options.add_argument("--user-data-dir=/home/appuser/.config/google-chrome")
        options.add_argument("--disk-cache-dir=/home/appuser/.cache/chrome")
        options.add_argument("--data-path=/home/appuser/.local")
        
        # Window size for testing
        options.add_argument("--window-size=1920,1080")
        
        print("Creating Chrome driver...")
        driver = uc.Chrome(options=options)
        
        print("Chrome driver created successfully!")
        
        # Test navigation to a simple page
        print("Testing navigation to example.com...")
        driver.get("https://example.com")
        
        # Wait a moment
        time.sleep(2)
        
        # Get page title
        title = driver.title
        print(f"Page title: {title}")
        
        # Check if we got the expected title
        if "Example Domain" in title:
            print("✅ Chrome connection test PASSED!")
            success = True
        else:
            print("❌ Chrome connection test FAILED - unexpected page title")
            success = False
            
        # Close driver
        driver.quit()
        print("Chrome driver closed successfully")
        
        return success
        
    except Exception as e:
        print(f"❌ Chrome connection test FAILED with error: {str(e)}")
        return False

if __name__ == "__main__":
    success = test_chrome_connection()
    sys.exit(0 if success else 1) 