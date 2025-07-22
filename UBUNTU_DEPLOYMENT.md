# Ubuntu Server Deployment Guide

This guide provides step-by-step instructions for deploying the Booking Scraper application on Ubuntu server.

## 🚀 Quick Deployment Commands

After setting up your GitHub repository, use these commands on your Ubuntu server:

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install required packages
sudo apt install -y git python3 python3-pip python3-venv wget gnupg curl unzip

# Install Docker (optional, for containerized deployment)
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# Install Google Chrome
wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | sudo apt-key add -
echo 'deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main' | sudo tee /etc/apt/sources.list.d/google-chrome.list
sudo apt update
sudo apt install -y google-chrome-stable

# Clone your repository
git clone https://github.com/YOUR_USERNAME/booking-scraper.git
cd booking-scraper

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Create necessary directories
mkdir -p data/csv static/css static/js logs

# Start the application
python -m uvicorn main:app --host 0.0.0.0 --port 8000
```

## 📋 Detailed Step-by-Step Instructions

### Step 1: Connect to Your Ubuntu Server
```bash
ssh username@your-server-ip
```

### Step 2: Update System Packages
```bash
sudo apt update && sudo apt upgrade -y
```

### Step 3: Install Essential Packages
```bash
sudo apt install -y \
    git \
    python3 \
    python3-pip \
    python3-venv \
    wget \
    gnupg \
    curl \
    unzip \
    build-essential \
    software-properties-common
```

### Step 4: Install Google Chrome (Required for Selenium)
```bash
# Add Google Chrome repository
wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | sudo apt-key add -
echo 'deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main' | sudo tee /etc/apt/sources.list.d/google-chrome.list

# Update package list and install Chrome
sudo apt update
sudo apt install -y google-chrome-stable

# Verify installation
google-chrome --version
```

### Step 5: Clone Your Repository
```bash
# Replace YOUR_USERNAME with your actual GitHub username
git clone https://github.com/YOUR_USERNAME/booking-scraper.git
cd booking-scraper
```

### Step 6: Set Up Python Environment
```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install project dependencies
pip install -r requirements.txt
```

### Step 7: Create Necessary Directories
```bash
mkdir -p data/csv static/css static/js logs
```

### Step 8: Configure Application (Optional)
If you need to modify any configuration:
```bash
# Edit main.py or other config files as needed
nano main.py
```

### Step 9: Test the Application
```bash
# Run a quick test
python test_chrome.py

# Check if Chrome driver works
python -c "from selenium import webdriver; from selenium.webdriver.chrome.options import Options; options = Options(); options.add_argument('--headless'); driver = webdriver.Chrome(options=options); print('Chrome driver works!'); driver.quit()"
```

### Step 10: Start the Application
```bash
# Method 1: Direct run (for testing)
python -m uvicorn main:app --host 0.0.0.0 --port 8000

# Method 2: With nohup (runs in background)
nohup python -m uvicorn main:app --host 0.0.0.0 --port 8000 > app.log 2>&1 &

# Method 3: Using screen (recommended for development)
sudo apt install screen
screen -S booking-scraper
python -m uvicorn main:app --host 0.0.0.0 --port 8000
# Press Ctrl+A then D to detach from screen
```

## 🐳 Docker Deployment (Alternative)

If you prefer Docker deployment:

### Install Docker and Docker Compose
```bash
# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Log out and back in, or run:
newgrp docker
```

### Deploy with Docker
```bash
# Clone repository
git clone https://github.com/YOUR_USERNAME/booking-scraper.git
cd booking-scraper

# Build and run with Docker Compose
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f
```

## 🔧 Production Setup

### Set Up Nginx (Reverse Proxy)
```bash
sudo apt install nginx

# Create Nginx configuration
sudo nano /etc/nginx/sites-available/booking-scraper
```

Add this configuration:
```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

Enable the site:
```bash
sudo ln -s /etc/nginx/sites-available/booking-scraper /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### Create Systemd Service (Auto-start on boot)
```bash
sudo nano /etc/systemd/system/booking-scraper.service
```

Add this content:
```ini
[Unit]
Description=Booking Scraper FastAPI App
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/booking-scraper
Environment=PATH=/home/ubuntu/booking-scraper/venv/bin
ExecStart=/home/ubuntu/booking-scraper/venv/bin/python -m uvicorn main:app --host 0.0.0.0 --port 8000
Restart=always

[Install]
WantedBy=multi-user.target
```

Enable and start the service:
```bash
sudo systemctl daemon-reload
sudo systemctl enable booking-scraper
sudo systemctl start booking-scraper
sudo systemctl status booking-scraper
```

## 🔍 Monitoring and Logs

### Check Application Status
```bash
# If running with systemd
sudo systemctl status booking-scraper

# If running with nohup
ps aux | grep uvicorn

# If running with Docker
docker-compose ps
```

### View Logs
```bash
# Application logs (if using nohup)
tail -f app.log

# Systemd logs
sudo journalctl -u booking-scraper -f

# Docker logs
docker-compose logs -f
```

### Check Port and Connections
```bash
# Check if port 8000 is listening
sudo netstat -tlnp | grep :8000

# Check if application is responding
curl http://localhost:8000/health
```

## 🚨 Troubleshooting

### Common Issues and Solutions

1. **Chrome/ChromeDriver Issues:**
```bash
# Install additional dependencies
sudo apt install -y libgconf-2-4 libxss1 libxtst6 libxrandr2 libasound2 libpangocairo-1.0-0 libcairo-gobject2 libgtk-3-0 libgdk-pixbuf2.0-0

# Set display environment variable
export DISPLAY=:0
```

2. **Permission Issues:**
```bash
# Fix file permissions
chmod +x deploy.sh
sudo chown -R $USER:$USER ~/booking-scraper
```

3. **Port Already in Use:**
```bash
# Find process using port 8000
sudo lsof -i :8000

# Kill process if needed
sudo kill -9 PID
```

4. **Memory Issues:**
```bash
# Check system resources
free -h
df -h
htop
```

## 🔐 Security Recommendations

1. **Firewall Setup:**
```bash
sudo ufw allow ssh
sudo ufw allow 80
sudo ufw allow 443
sudo ufw --force enable
```

2. **SSL Certificate (Let's Encrypt):**
```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d your-domain.com
```

3. **Update Dependencies:**
```bash
pip install --upgrade pip
pip install -r requirements.txt --upgrade
```

## 📞 Access Your Application

Once deployed, access your application at:
- **Direct access:** `http://your-server-ip:8000`
- **With Nginx:** `http://your-domain.com`
- **API Documentation:** `http://your-server-ip:8000/docs`

## 🔄 Updating Your Application

To update your application with new changes:
```bash
cd booking-scraper
git pull origin main
source venv/bin/activate
pip install -r requirements.txt
sudo systemctl restart booking-scraper  # if using systemd
# OR
docker-compose pull && docker-compose up -d  # if using Docker
``` 