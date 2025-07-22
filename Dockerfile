# Use Python 3.11 base image
FROM python:3.11-slim

# Set environment variables
ENV DEBIAN_FRONTEND=noninteractive
ENV DISPLAY=:1

# Set working directory
WORKDIR /app

# Update system and install dependencies
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    curl \
    unzip \
    xvfb \
    && rm -rf /var/lib/apt/lists/*

# Install Google Chrome
RUN wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub > /usr/share/keyrings/chrome.pub && \
    echo 'deb [arch=amd64 signed-by=/usr/share/keyrings/chrome.pub] http://dl.google.com/linux/chrome/deb/ stable main' > /etc/apt/sources.list.d/google-chrome.list && \
    apt-get update -y && \
    apt-get install -y google-chrome-stable

# Copy requirements.txt and install Python packages
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p data/csv static/css static/js logs

# Create a startup script
RUN echo '#!/bin/bash\n\
echo "Starting Xvfb..."\n\
Xvfb $DISPLAY -screen $DISPLAY 1280x1024x16 &\n\
sleep 2\n\
echo "Starting FastAPI application..."\n\
python -m uvicorn main:app --host 0.0.0.0 --port 8000' > /app/start.sh

RUN chmod +x /app/start.sh

# Expose port
EXPOSE 8000

# Expose the app directory as volume for output
VOLUME ["/app"]

# Run the startup script
CMD ["/bin/bash", "/app/start.sh"] 