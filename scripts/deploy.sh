#!/bin/bash

# Booking Scraper AWS Deployment Script
# This script deploys the booking scraper to AWS using ECS Fargate

set -e

# Configuration
REGION=${AWS_REGION:-us-east-1}
ENVIRONMENT=${ENVIRONMENT:-production}
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
ECR_REPOSITORY=booking-scraper
IMAGE_TAG=${IMAGE_TAG:-latest}
STACK_NAME=${ENVIRONMENT}-booking-scraper-infrastructure

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Functions
log() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check prerequisites
check_prerequisites() {
    log "Checking prerequisites..."
    
    # Check AWS CLI
    if ! command -v aws &> /dev/null; then
        error "AWS CLI is not installed. Please install it first."
        exit 1
    fi
    
    # Check Docker
    if ! command -v docker &> /dev/null; then
        error "Docker is not installed. Please install it first."
        exit 1
    fi
    
    # Check AWS credentials
    if ! aws sts get-caller-identity &> /dev/null; then
        error "AWS credentials not configured. Please run 'aws configure' first."
        exit 1
    fi
    
    log "Prerequisites check passed!"
}

# Create ECR repository if it doesn't exist
create_ecr_repository() {
    log "Creating ECR repository..."
    
    aws ecr describe-repositories --repository-names $ECR_REPOSITORY --region $REGION &> /dev/null || {
        log "Creating ECR repository: $ECR_REPOSITORY"
        aws ecr create-repository --repository-name $ECR_REPOSITORY --region $REGION
    }
    
    log "ECR repository ready!"
}

# Build and push Docker image
build_and_push_image() {
    log "Building Docker image..."
    
    # Build the image
    docker build -t $ECR_REPOSITORY:$IMAGE_TAG .
    
    # Get ECR login token
    aws ecr get-login-password --region $REGION | docker login --username AWS --password-stdin $ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com
    
    # Tag the image
    docker tag $ECR_REPOSITORY:$IMAGE_TAG $ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com/$ECR_REPOSITORY:$IMAGE_TAG
    
    # Push the image
    log "Pushing Docker image to ECR..."
    docker push $ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com/$ECR_REPOSITORY:$IMAGE_TAG
    
    log "Docker image pushed successfully!"
}

# Deploy infrastructure using CloudFormation
deploy_infrastructure() {
    log "Deploying infrastructure..."
    
    # Check if stack exists
    if aws cloudformation describe-stacks --stack-name $STACK_NAME --region $REGION &> /dev/null; then
        log "Updating existing stack: $STACK_NAME"
        aws cloudformation update-stack \
            --stack-name $STACK_NAME \
            --template-body file://aws/cloudformation-template.yaml \
            --parameters ParameterKey=Environment,ParameterValue=$ENVIRONMENT \
                        ParameterKey=ImageTag,ParameterValue=$IMAGE_TAG \
            --capabilities CAPABILITY_IAM \
            --region $REGION
    else
        log "Creating new stack: $STACK_NAME"
        aws cloudformation create-stack \
            --stack-name $STACK_NAME \
            --template-body file://aws/cloudformation-template.yaml \
            --parameters ParameterKey=Environment,ParameterValue=$ENVIRONMENT \
                        ParameterKey=ImageTag,ParameterValue=$IMAGE_TAG \
            --capabilities CAPABILITY_IAM \
            --region $REGION
    fi
    
    log "Waiting for stack deployment to complete..."
    aws cloudformation wait stack-create-complete --stack-name $STACK_NAME --region $REGION || \
    aws cloudformation wait stack-update-complete --stack-name $STACK_NAME --region $REGION
    
    log "Infrastructure deployed successfully!"
}

# Create ECS service
create_ecs_service() {
    log "Creating ECS service..."
    
    # Get stack outputs
    CLUSTER_NAME=$(aws cloudformation describe-stacks \
        --stack-name $STACK_NAME \
        --region $REGION \
        --query 'Stacks[0].Outputs[?OutputKey==`ECSClusterName`].OutputValue' \
        --output text)
    
    TARGET_GROUP_ARN=$(aws cloudformation describe-stacks \
        --stack-name $STACK_NAME \
        --region $REGION \
        --query 'Stacks[0].Outputs[?OutputKey==`ALBTargetGroupArn`].OutputValue' \
        --output text)
    
    # Update task definition with correct values
    sed -e "s/YOUR_ACCOUNT_ID/$ACCOUNT_ID/g" \
        -e "s/YOUR_REGION/$REGION/g" \
        aws/ecs-task-definition.json > /tmp/task-definition.json
    
    # Register task definition
    aws ecs register-task-definition \
        --cli-input-json file:///tmp/task-definition.json \
        --region $REGION
    
    # Create or update service
    SERVICE_NAME="$ENVIRONMENT-booking-scraper-service"
    
    if aws ecs describe-services --cluster $CLUSTER_NAME --services $SERVICE_NAME --region $REGION &> /dev/null; then
        log "Updating existing service: $SERVICE_NAME"
        aws ecs update-service \
            --cluster $CLUSTER_NAME \
            --service $SERVICE_NAME \
            --task-definition booking-scraper \
            --region $REGION
    else
        log "Creating new service: $SERVICE_NAME"
        aws ecs create-service \
            --cluster $CLUSTER_NAME \
            --service-name $SERVICE_NAME \
            --task-definition booking-scraper \
            --desired-count 1 \
            --launch-type FARGATE \
            --network-configuration "awsvpcConfiguration={subnets=[$(aws ec2 describe-subnets --filters Name=tag:Name,Values=*private-subnet* --query 'Subnets[].SubnetId' --output text | tr '\t' ',')],securityGroups=[$(aws ec2 describe-security-groups --filters Name=tag:Name,Values=*ecs-sg* --query 'SecurityGroups[].GroupId' --output text)]}" \
            --region $REGION
    fi
    
    log "ECS service created/updated successfully!"
}

# Get deployment information
get_deployment_info() {
    log "Getting deployment information..."
    
    # Get Load Balancer DNS
    ALB_DNS=$(aws cloudformation describe-stacks \
        --stack-name $STACK_NAME \
        --region $REGION \
        --query 'Stacks[0].Outputs[?OutputKey==`LoadBalancerDNS`].OutputValue' \
        --output text)
    
    echo ""
    echo "======================================"
    echo "        DEPLOYMENT SUCCESSFUL!        "
    echo "======================================"
    echo ""
    echo "Application URL: http://$ALB_DNS"
    echo "Dashboard URL: http://$ALB_DNS/"
    echo "API Documentation: http://$ALB_DNS/docs"
    echo ""
    echo "AWS Resources:"
    echo "- Stack Name: $STACK_NAME"
    echo "- ECR Repository: $ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com/$ECR_REPOSITORY:$IMAGE_TAG"
    echo "- ECS Cluster: $CLUSTER_NAME"
    echo ""
    echo "To monitor your deployment:"
    echo "- CloudWatch Logs: https://console.aws.amazon.com/cloudwatch/home?region=$REGION#logsV2:log-groups"
    echo "- ECS Console: https://console.aws.amazon.com/ecs/home?region=$REGION#/clusters"
    echo ""
}

# Main deployment function
main() {
    log "Starting AWS deployment for Booking Scraper..."
    
    check_prerequisites
    create_ecr_repository
    build_and_push_image
    deploy_infrastructure
    create_ecs_service
    get_deployment_info
    
    log "Deployment completed successfully!"
}

# Run main function
main "$@" 