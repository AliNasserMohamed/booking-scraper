#!/bin/bash

echo "=== Chrome Setup Test for Ubuntu Server ==="
echo ""

# Check if Chrome is installed
echo "1. Checking Chrome installation..."
if command -v google-chrome-stable &> /dev/null; then
    echo "✅ google-chrome-stable found"
    google-chrome-stable --version
elif command -v google-chrome &> /dev/null; then
    echo "✅ google-chrome found" 
    google-chrome --version
elif command -v chromium-browser &> /dev/null; then
    echo "✅ chromium-browser found"
    chromium-browser --version
else
    echo "❌ Chrome/Chromium not found!"
    echo "Please install Chrome using:"
    echo "  wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | sudo apt-key add -"
    echo "  echo 'deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main' | sudo tee /etc/apt/sources.list.d/google-chrome.list"
    echo "  sudo apt update"
    echo "  sudo apt install -y google-chrome-stable"
    exit 1
fi

echo ""

# Check Python and dependencies
echo "2. Checking Python dependencies..."
python3 -c "import undetected_chromedriver; print('✅ undetected_chromedriver imported successfully')" 2>/dev/null || {
    echo "❌ undetected_chromedriver not found"
    echo "Please install it using: pip install undetected-chromedriver"
    exit 1
}

python3 -c "import selenium; print('✅ selenium imported successfully')" 2>/dev/null || {
    echo "❌ selenium not found" 
    echo "Please install it using: pip install selenium"
    exit 1
}

echo ""

# Test Chrome driver
echo "3. Testing Chrome driver functionality..."
if python3 test_chrome.py; then
    echo ""
    echo "🎉 All tests passed! Chrome driver is working properly."
    echo "You should be able to run the scraper now."
else
    echo ""
    echo "❌ Chrome driver test failed. Please check the error messages above."
    exit 1
fi

echo ""
echo "=== Chrome Setup Test Complete ===" 