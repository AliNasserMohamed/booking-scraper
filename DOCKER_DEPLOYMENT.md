# Docker Deployment Guide

This guide explains how to deploy your Booking Scraper application using Docker to AWS Ubuntu servers.

## 📋 Prerequisites

### On Your Local Machine
- Docker installed and running
- AWS CLI configured with appropriate credentials
- SSH access to your AWS EC2 instance

### On Your AWS Ubuntu Server
- Ubuntu 20.04 LTS or later
- Docker installed
- Docker Compose installed
- At least 2GB RAM (4GB recommended)
- 20GB+ storage space

## 🚀 Quick Start

### 1. Build and Test Locally

#### On Windows:
```cmd
# Build Docker image
deploy.bat build

# Test locally
deploy.bat test

# Access your application at: http://localhost:8000
```

#### On Linux/macOS:
```bash
# Build Docker image
./deploy.sh build

# Test locally
./deploy.sh test

# Access your application at: http://localhost:8000
```

### 2. Using Docker Compose (Recommended)

```bash
# Start the application
docker-compose up -d

# View logs
docker-compose logs -f

# Stop the application
docker-compose down
```

## 🔧 Configuration

### Environment Variables

Create a `.env` file in your project root:

```env
# Database configuration
DATABASE_URL=sqlite:///booking_hotels.db

# Application settings
PORT=8000
PYTHONUNBUFFERED=1

# AWS settings (optional)
AWS_REGION=us-east-1
ECR_REPO_URI=your-account-id.dkr.ecr.us-east-1.amazonaws.com/booking-scraper

# EC2 deployment settings
EC2_HOST=your-ec2-instance.compute.amazonaws.com
```

### Docker Compose Configuration

The `docker-compose.yml` includes:

- **Main Application**: Booking scraper with Selenium + Chrome
- **Volume Mounts**: Data and logs persistence
- **Health Checks**: Automatic container health monitoring
- **Network Configuration**: Isolated network for security
- **Optional Nginx**: Reverse proxy for production

## 📦 Deployment Options

### Option 1: Direct Docker Commands

```bash
# Build the image
docker build -t booking-scraper:latest .

# Run the container
docker run -d \
  --name booking-scraper \
  -p 8000:8000 \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/logs:/app/logs \
  --shm-size=2g \
  booking-scraper:latest

# Check status
docker ps
docker logs booking-scraper
```

### Option 2: Using Docker Compose

```yaml
version: '3.8'

services:
  booking-scraper:
    build: .
    ports:
      - "8000:8000"
    volumes:
      - ./data:/app/data
      - ./logs:/app/logs
    environment:
      - DATABASE_URL=sqlite:///booking_hotels.db
      - PORT=8000
    restart: unless-stopped
    shm_size: '2gb'
```

### Option 3: AWS ECR + EC2

1. **Push to ECR**:
```bash
# Set your ECR repository URI
export ECR_REPO_URI=your-account-id.dkr.ecr.us-east-1.amazonaws.com/booking-scraper

# Push image
./deploy.sh push  # or deploy.bat push on Windows
```

2. **Deploy to EC2**:
```bash
# Set your EC2 hostname
export EC2_HOST=your-ec2-instance.compute.amazonaws.com

# Deploy
./deploy.sh deploy  # or deploy.bat deploy on Windows
```

## 🖥️ Server Setup

### Prepare Your Ubuntu Server

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Reboot to apply changes
sudo reboot
```

### Deploy Your Application

```bash
# Clone your repository
git clone <your-repo-url>
cd booking_scraper

# Create necessary directories
mkdir -p data/csv logs

# Start the application
docker-compose up -d

# Check status
docker-compose ps
docker-compose logs -f
```

## 🔍 Monitoring and Troubleshooting

### Check Application Status

```bash
# View running containers
docker ps

# View application logs
docker logs booking-scraper

# View Docker Compose logs
docker-compose logs -f

# Check container health
docker inspect booking-scraper | grep -A 10 Health
```

### Common Issues and Solutions

#### 1. Chrome/Selenium Issues
```bash
# Increase shared memory if Chrome crashes
docker run --shm-size=2g ...

# Or use --disable-dev-shm-usage in Chrome options
```

#### 2. Permission Issues
```bash
# Fix file permissions
sudo chown -R $USER:$USER ./data ./logs
chmod -R 755 ./data ./logs
```

#### 3. Memory Issues
```bash
# Monitor memory usage
docker stats

# Increase server memory if needed
# Recommended: 4GB+ RAM
```

#### 4. Port Conflicts
```bash
# Check what's using port 8000
sudo netstat -tlnp | grep :8000

# Use different port
docker run -p 8080:8000 ...
```

## 🌐 Production Deployment

### With Nginx Reverse Proxy

1. **Enable Nginx in Docker Compose**:
```bash
# Start with nginx
docker-compose --profile production up -d
```

2. **Configure Domain**:
```nginx
# Update nginx.conf
server_name your-domain.com;
```

3. **SSL Configuration**:
```bash
# Generate SSL certificates (Let's Encrypt)
sudo certbot certonly --webroot -w /var/www/html -d your-domain.com

# Copy certificates to ssl directory
sudo cp /etc/letsencrypt/live/your-domain.com/fullchain.pem ./ssl/cert.pem
sudo cp /etc/letsencrypt/live/your-domain.com/privkey.pem ./ssl/key.pem
```

### Environment-Specific Configurations

#### Development
```bash
# Use local database
DATABASE_URL=sqlite:///booking_hotels.db

# Enable debug mode
DEBUG=1
```

#### Production
```bash
# Use production database
DATABASE_URL=postgresql://user:pass@localhost/booking_hotels

# Disable debug mode
DEBUG=0

# Set proper host
HOST=0.0.0.0
```

## 🔐 Security Best Practices

1. **Use non-root user** (already configured in Dockerfile)
2. **Limit resource usage**:
   ```yaml
   deploy:
     resources:
       limits:
         cpus: '2.0'
         memory: 4G
       reservations:
         memory: 2G
   ```

3. **Use secrets for sensitive data**:
   ```bash
   # Use Docker secrets or environment files
   docker-compose --env-file .env.production up -d
   ```

4. **Network security**:
   ```yaml
   networks:
     booking-network:
       driver: bridge
       internal: true  # Isolate from internet
   ```

## 📊 Performance Optimization

### Resource Allocation
```yaml
services:
  booking-scraper:
    deploy:
      resources:
        limits:
          cpus: '2.0'
          memory: 4G
        reservations:
          cpus: '1.0'
          memory: 2G
```

### Chrome Optimization
```python
# In your scraper configuration
chrome_options = webdriver.ChromeOptions()
chrome_options.add_argument('--no-sandbox')
chrome_options.add_argument('--disable-dev-shm-usage')
chrome_options.add_argument('--disable-gpu')
chrome_options.add_argument('--remote-debugging-port=9222')
chrome_options.add_argument('--memory-pressure-off')
```

## 🆘 Support

If you encounter issues:

1. **Check logs**: `docker-compose logs -f booking-scraper`
2. **Verify container health**: `docker inspect booking-scraper`
3. **Test connectivity**: `curl http://localhost:8000/health`
4. **Monitor resources**: `docker stats`

## 📝 Maintenance

### Regular Updates
```bash
# Pull latest changes
git pull origin main

# Rebuild and restart
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

### Backup
```bash
# Backup database and data
tar -czf backup-$(date +%Y%m%d).tar.gz data/ booking_hotels.db logs/

# Upload to S3 (optional)
aws s3 cp backup-$(date +%Y%m%d).tar.gz s3://your-backup-bucket/
```

Your Booking Scraper is now ready for production deployment on AWS! 🚀 