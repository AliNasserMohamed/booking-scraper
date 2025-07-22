#!/bin/bash

# Booking Scraper - AWS Deployment Script
# This script helps deploy the booking scraper to AWS EC2 or ECS

set -e

# Configuration
APP_NAME="booking-scraper"
DOCKER_IMAGE="booking-scraper:latest"
AWS_REGION="us-east-1"
ECR_REPO_URI=""  # Set this to your ECR repository URI if using ECR

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check if required tools are installed
check_requirements() {
    print_status "Checking requirements..."
    
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed. Please install Docker first."
        exit 1
    fi
    
    if ! command -v aws &> /dev/null; then
        print_error "AWS CLI is not installed. Please install AWS CLI first."
        exit 1
    fi
    
    print_status "All requirements are met."
}

# Function to build Docker image
build_image() {
    print_status "Building Docker image..."
    
    # Build the image
    docker build -t $DOCKER_IMAGE .
    
    if [ $? -eq 0 ]; then
        print_status "Docker image built successfully."
    else
        print_error "Failed to build Docker image."
        exit 1
    fi
}

# Function to test image locally
test_image() {
    print_status "Testing Docker image locally..."
    
    # Stop any existing containers
    docker stop $APP_NAME 2>/dev/null || true
    docker rm $APP_NAME 2>/dev/null || true
    
    # Run the container
    docker run -d \
        --name $APP_NAME \
        -p 8000:8000 \
        -v $(pwd)/data:/app/data \
        -v $(pwd)/logs:/app/logs \
        $DOCKER_IMAGE
    
    # Wait for the container to start
    sleep 10
    
    # Check if the container is running
    if [ $(docker ps -q -f name=$APP_NAME | wc -l) -eq 1 ]; then
        print_status "Container is running successfully."
        print_status "You can access the application at: http://localhost:8000"
        print_status "To stop the container, run: docker stop $APP_NAME"
    else
        print_error "Container failed to start."
        docker logs $APP_NAME
        exit 1
    fi
}

# Function to push to ECR (if ECR_REPO_URI is set)
push_to_ecr() {
    if [ -z "$ECR_REPO_URI" ]; then
        print_warning "ECR_REPO_URI not set. Skipping ECR push."
        return
    fi
    
    print_status "Pushing image to ECR..."
    
    # Login to ECR
    aws ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin $ECR_REPO_URI
    
    # Tag and push the image
    docker tag $DOCKER_IMAGE $ECR_REPO_URI:latest
    docker push $ECR_REPO_URI:latest
    
    print_status "Image pushed to ECR successfully."
}

# Function to deploy to EC2
deploy_to_ec2() {
    print_status "Deploying to EC2..."
    
    # This assumes you have an EC2 instance with Docker installed
    # and proper SSH access configured
    
    EC2_HOST=${EC2_HOST:-"your-ec2-instance.compute.amazonaws.com"}
    
    if [ "$EC2_HOST" == "your-ec2-instance.compute.amazonaws.com" ]; then
        print_error "Please set EC2_HOST environment variable to your EC2 instance hostname."
        exit 1
    fi
    
    # Copy docker-compose.yml to EC2
    scp docker-compose.yml $EC2_HOST:~/
    
    # SSH to EC2 and deploy
    ssh $EC2_HOST << 'EOF'
        # Stop existing containers
        docker-compose down || true
        
        # Pull latest image (if using ECR)
        # docker pull $ECR_REPO_URI:latest
        
        # Start the application
        docker-compose up -d
        
        # Check status
        docker-compose ps
EOF
    
    print_status "Deployment to EC2 completed."
}

# Function to create AWS resources using CloudFormation
create_aws_resources() {
    print_status "Creating AWS resources..."
    
    if [ ! -f "aws/cloudformation-template.yaml" ]; then
        print_error "CloudFormation template not found. Please create aws/cloudformation-template.yaml first."
        exit 1
    fi
    
    aws cloudformation create-stack \
        --stack-name $APP_NAME-stack \
        --template-body file://aws/cloudformation-template.yaml \
        --parameters ParameterKey=ImageUri,ParameterValue=$DOCKER_IMAGE \
        --capabilities CAPABILITY_IAM \
        --region $AWS_REGION
    
    print_status "CloudFormation stack creation initiated."
}

# Function to show usage
show_usage() {
    echo "Usage: $0 [OPTION]"
    echo "Options:"
    echo "  build      Build Docker image"
    echo "  test       Test Docker image locally"
    echo "  push       Push image to ECR"
    echo "  deploy     Deploy to EC2"
    echo "  create     Create AWS resources"
    echo "  all        Run all steps (build, test, push, deploy)"
    echo "  help       Show this help message"
    echo ""
    echo "Environment variables:"
    echo "  ECR_REPO_URI    - ECR repository URI (optional)"
    echo "  EC2_HOST        - EC2 instance hostname for deployment"
    echo "  AWS_REGION      - AWS region (default: us-east-1)"
}

# Main script logic
main() {
    case "${1:-help}" in
        "build")
            check_requirements
            build_image
            ;;
        "test")
            test_image
            ;;
        "push")
            push_to_ecr
            ;;
        "deploy")
            deploy_to_ec2
            ;;
        "create")
            create_aws_resources
            ;;
        "all")
            check_requirements
            build_image
            test_image
            push_to_ecr
            deploy_to_ec2
            ;;
        "help"|*)
            show_usage
            ;;
    esac
}

# Run main function
main "$@" 