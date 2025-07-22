@echo off
REM Booking Scraper - AWS Deployment Script for Windows
REM This script helps deploy the booking scraper to AWS EC2 or ECS

set APP_NAME=booking-scraper
set DOCKER_IMAGE=booking-scraper:latest
set AWS_REGION=us-east-1
set ECR_REPO_URI=

echo.
echo ==========================================
echo  Booking Scraper - AWS Deployment
echo ==========================================
echo.

if "%1"=="build" goto build
if "%1"=="test" goto test
if "%1"=="push" goto push
if "%1"=="deploy" goto deploy
if "%1"=="all" goto all
goto help

:check_requirements
echo [INFO] Checking requirements...
docker --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Docker is not installed. Please install Docker first.
    exit /b 1
)

aws --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] AWS CLI is not installed. Please install AWS CLI first.
    exit /b 1
)

echo [INFO] All requirements are met.
exit /b 0

:build
echo [INFO] Building Docker image...
call :check_requirements
if errorlevel 1 exit /b 1

docker build -t %DOCKER_IMAGE% .
if errorlevel 1 (
    echo [ERROR] Failed to build Docker image.
    exit /b 1
)

echo [INFO] Docker image built successfully.
exit /b 0

:test
echo [INFO] Testing Docker image locally...

REM Stop any existing containers
docker stop %APP_NAME% 2>nul
docker rm %APP_NAME% 2>nul

REM Run the container
docker run -d --name %APP_NAME% -p 8000:8000 -v "%cd%\data:/app/data" -v "%cd%\logs:/app/logs" %DOCKER_IMAGE%

REM Wait for the container to start
timeout /t 10 /nobreak > nul

REM Check if the container is running
docker ps -q -f name=%APP_NAME% | find /c /v "" > temp_count.txt
set /p container_count=<temp_count.txt
del temp_count.txt

if %container_count% geq 1 (
    echo [INFO] Container is running successfully.
    echo [INFO] You can access the application at: http://localhost:8000
    echo [INFO] To stop the container, run: docker stop %APP_NAME%
) else (
    echo [ERROR] Container failed to start.
    docker logs %APP_NAME%
    exit /b 1
)
exit /b 0

:push
if "%ECR_REPO_URI%"=="" (
    echo [WARNING] ECR_REPO_URI not set. Skipping ECR push.
    exit /b 0
)

echo [INFO] Pushing image to ECR...

REM Login to ECR
for /f "tokens=*" %%i in ('aws ecr get-login-password --region %AWS_REGION%') do set LOGIN_TOKEN=%%i
echo %LOGIN_TOKEN% | docker login --username AWS --password-stdin %ECR_REPO_URI%

REM Tag and push the image
docker tag %DOCKER_IMAGE% %ECR_REPO_URI%:latest
docker push %ECR_REPO_URI%:latest

echo [INFO] Image pushed to ECR successfully.
exit /b 0

:deploy
echo [INFO] Deploying to EC2...
if "%EC2_HOST%"=="" (
    echo [ERROR] Please set EC2_HOST environment variable to your EC2 instance hostname.
    exit /b 1
)

REM Copy docker-compose.yml to EC2
scp docker-compose.yml %EC2_HOST%:~/

REM SSH to EC2 and deploy
ssh %EC2_HOST% "docker-compose down || true && docker-compose up -d && docker-compose ps"

echo [INFO] Deployment to EC2 completed.
exit /b 0

:all
call :build
if errorlevel 1 exit /b 1
call :test
if errorlevel 1 exit /b 1
call :push
if errorlevel 1 exit /b 1
call :deploy
if errorlevel 1 exit /b 1
exit /b 0

:help
echo Usage: %0 [OPTION]
echo Options:
echo   build      Build Docker image
echo   test       Test Docker image locally
echo   push       Push image to ECR
echo   deploy     Deploy to EC2
echo   all        Run all steps (build, test, push, deploy)
echo   help       Show this help message
echo.
echo Environment variables:
echo   ECR_REPO_URI    - ECR repository URI (optional)
echo   EC2_HOST        - EC2 instance hostname for deployment
echo   AWS_REGION      - AWS region (default: us-east-1)
echo.
echo Examples:
echo   %0 build
echo   %0 test
echo   set ECR_REPO_URI=your-ecr-repo && %0 push
echo   set EC2_HOST=your-ec2-host && %0 deploy
exit /b 0 