#!/bin/bash

# Google Cloud Serverless Deployment Script for Yargısal Zeka
set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Configuration
PROJECT_ID=""
REGION="europe-west1"
DOMAIN_NAME="yargisalzeka.com"

# Functions
log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

error() {
    echo -e "${RED}[ERROR] $1${NC}"
    exit 1
}

success() {
    echo -e "${GREEN}[SUCCESS] $1${NC}"
}

warning() {
    echo -e "${YELLOW}[WARNING] $1${NC}"
}

# Check prerequisites
check_prerequisites() {
    log "Checking prerequisites..."
    
    # Check if gcloud is installed
    if ! command -v gcloud &> /dev/null; then
        error "gcloud CLI is not installed. Please install it first."
    fi
    
    # Check if terraform is installed
    if ! command -v terraform &> /dev/null; then
        error "Terraform is not installed. Please install it first."
    fi
    
    # Check if docker is installed
    if ! command -v docker &> /dev/null; then
        error "Docker is not installed. Please install it first."
    fi
    
    # Get project ID if not set
    if [[ -z "$PROJECT_ID" ]]; then
        PROJECT_ID=$(gcloud config get-value project 2>/dev/null)
        if [[ -z "$PROJECT_ID" ]]; then
            error "GCP Project ID not set. Run: gcloud config set project YOUR_PROJECT_ID"
        fi
    fi
    
    log "Using GCP Project: $PROJECT_ID"
    success "Prerequisites check completed"
}

# Setup environment
setup_environment() {
    log "Setting up environment..."
    
    # Authenticate with gcloud
    gcloud auth configure-docker gcr.io --quiet
    
    # Set default region
    gcloud config set run/region $REGION
    
    success "Environment setup completed"
}

# Build and push Docker images
build_and_push_images() {
    log "Building and pushing Docker images..."
    
    # Build Main API image
    log "Building Main API image..."
    docker build --platform linux/amd64 -t gcr.io/$PROJECT_ID/yargisalzeka-main-api:latest \
        -f gcp/main-api/Dockerfile ./hukuk-asistan-main
    
    # Build Frontend image
    log "Building Frontend image..."
    docker build --platform linux/amd64 -t gcr.io/$PROJECT_ID/yargisalzeka-frontend:latest \
        -f gcp/frontend/Dockerfile .
    
    # Push images
    log "Pushing images to Container Registry..."
    docker push gcr.io/$PROJECT_ID/yargisalzeka-main-api:latest
    docker push gcr.io/$PROJECT_ID/yargisalzeka-frontend:latest
    
    success "Docker images built and pushed"
}

# Deploy with Terraform
deploy_infrastructure() {
    log "Deploying infrastructure with Terraform..."
    
    cd gcp/terraform
    
    # Initialize Terraform
    terraform init
    
    # Validate configuration
    terraform validate
    
    # Plan deployment
    log "Creating Terraform plan..."
    terraform plan -var="project_id=$PROJECT_ID" \
                   -var="region=$REGION" \
                   -var="domain_name=$DOMAIN_NAME" \
                   -var="gemini_api_key=$GEMINI_API_KEY" \
                   -var="jwt_secret_key=$JWT_SECRET_KEY" \
                   -out=tfplan
    
    # Apply infrastructure
    log "Applying Terraform configuration..."
    terraform apply tfplan
    
    cd ../..
    success "Infrastructure deployed"
}

# Deploy Cloud Functions
deploy_cloud_functions() {
    log "Deploying Cloud Functions..."
    
    # Create deployment package for scraper function
    cd gcp/functions/scraper
    zip -r ../../../scraper-function.zip . -x "*.pyc" "__pycache__/*"
    cd ../../..
    
    # Upload to Cloud Storage
    gsutil cp scraper-function.zip gs://$PROJECT_ID-static-assets/
    
    # Deploy function
    gcloud functions deploy yargitay-scraper \
        --source=gcp/functions/scraper \
        --entry-point=scrape_yargitay \
        --runtime=python311 \
        --trigger=http \
        --allow-unauthenticated \
        --region=$REGION \
        --memory=2GB \
        --timeout=540s \
        --max-instances=10 \
        --set-env-vars=GCP_PROJECT=$PROJECT_ID,ENVIRONMENT=production
    
    # Clean up
    rm scraper-function.zip
    
    success "Cloud Functions deployed"
}

# Setup monitoring and logging
setup_monitoring() {
    log "Setting up monitoring and logging..."
    
    # Enable monitoring and logging APIs (if not already enabled)
    gcloud services enable monitoring.googleapis.com logging.googleapis.com
    
    # Create log-based metrics
    gcloud logging metrics create api_errors \
        --description="API Error Count" \
        --log-filter='resource.type="cloud_run_revision" AND severity>=ERROR' \
        --quiet || true
    
    gcloud logging metrics create api_latency \
        --description="API Response Latency" \
        --log-filter='resource.type="cloud_run_revision" AND httpRequest.latency>0' \
        --quiet || true
    
    success "Monitoring and logging configured"
}

# Verify deployment
verify_deployment() {
    log "Verifying deployment..."
    
    # Get service URLs
    API_URL=$(gcloud run services describe yargisalzeka-api --region=$REGION --format='value(status.url)')
    FRONTEND_URL=$(gcloud run services describe yargisalzeka-frontend --region=$REGION --format='value(status.url)')
    
    log "API URL: $API_URL"
    log "Frontend URL: $FRONTEND_URL"
    
    # Test API health
    if curl -f -s "$API_URL/health" > /dev/null; then
        success "API health check passed"
    else
        warning "API health check failed"
    fi
    
    # Test frontend
    if curl -f -s "$FRONTEND_URL/health" > /dev/null; then
        success "Frontend health check passed"
    else
        warning "Frontend health check failed"
    fi
    
    success "Deployment verification completed"
}

# Setup custom domain
setup_custom_domain() {
    log "Setting up custom domain..."
    
    # Get load balancer IP
    LB_IP=$(gcloud compute addresses describe yargisalzeka-ip --global --format='value(address)')
    
    log "Load Balancer IP: $LB_IP"
    log ""
    log "To complete domain setup:"
    log "1. Point your domain's A record to: $LB_IP"
    log "2. Add CNAME record: www.$DOMAIN_NAME -> $DOMAIN_NAME"
    log "3. Wait for SSL certificate provisioning (up to 60 minutes)"
    log ""
    
    success "Custom domain configuration instructions provided"
}

# Cleanup function
cleanup() {
    log "Cleaning up temporary files..."
    rm -f tfplan scraper-function.zip
}

# Main deployment function
main() {
    log "Starting Google Cloud Serverless Deployment for Yargısal Zeka..."
    
    # Check for required environment variables
    if [[ -z "$GEMINI_API_KEY" ]]; then
        error "GEMINI_API_KEY environment variable is required"
    fi
    
    if [[ -z "$JWT_SECRET_KEY" ]]; then
        error "JWT_SECRET_KEY environment variable is required"
    fi
    
    # Trap cleanup on exit
    trap cleanup EXIT
    
    # Run deployment steps
    check_prerequisites
    setup_environment
    build_and_push_images
    deploy_infrastructure
    deploy_cloud_functions
    setup_monitoring
    verify_deployment
    setup_custom_domain
    
    success "Deployment completed successfully!"
    log ""
    log "🎉 Yargısal Zeka is now running on Google Cloud!"
    log ""
    log "Services:"
    log "  - API: https://yargisalzeka-api-xxxxxxxxxx-ew.a.run.app"
    log "  - Frontend: https://yargisalzeka-frontend-xxxxxxxxxx-ew.a.run.app"
    log "  - Custom Domain: https://$DOMAIN_NAME (after DNS setup)"
    log ""
    log "Next steps:"
    log "1. Configure your domain DNS settings"
    log "2. Wait for SSL certificate provisioning"
    log "3. Test your application"
    log "4. Set up monitoring alerts"
}

# Script options
case "${1:-deploy}" in
    "deploy")
        main
        ;;
    "build")
        check_prerequisites
        build_and_push_images
        ;;
    "infrastructure")
        check_prerequisites
        deploy_infrastructure
        ;;
    "functions")
        check_prerequisites
        deploy_cloud_functions
        ;;
    "verify")
        verify_deployment
        ;;
    "domain")
        setup_custom_domain
        ;;
    *)
        echo "Usage: $0 {deploy|build|infrastructure|functions|verify|domain}"
        echo ""
        echo "Commands:"
        echo "  deploy         - Full deployment (default)"
        echo "  build          - Build and push Docker images only"
        echo "  infrastructure - Deploy infrastructure with Terraform"
        echo "  functions      - Deploy Cloud Functions only"
        echo "  verify         - Verify deployment"
        echo "  domain         - Show domain setup instructions"
        echo ""
        echo "Environment variables required:"
        echo "  GEMINI_API_KEY - Google Gemini API key"
        echo "  JWT_SECRET_KEY - JWT secret key"
        echo ""
        echo "Optional:"
        echo "  PROJECT_ID     - GCP Project ID (auto-detected if not set)"
        echo "  REGION         - GCP Region (default: europe-west1)"
        echo "  DOMAIN_NAME    - Custom domain (default: yargisalzeka.com)"
        exit 1
        ;;
esac

