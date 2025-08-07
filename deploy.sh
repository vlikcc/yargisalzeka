#!/bin/bash

# Yargısal Zeka Production Deployment Script
# Usage: ./deploy.sh [staging|production]

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
ENVIRONMENT=${1:-staging}
COMPOSE_FILE="docker-compose.production.yml"
ENV_FILE=".env.production"
BACKUP_DIR="./backups"
LOG_DIR="./logs"

# Functions
print_status() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# Check prerequisites
check_prerequisites() {
    print_status "Checking prerequisites..."
    
    # Check Docker
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed"
        exit 1
    fi
    
    # Check Docker Compose
    if ! command -v docker-compose &> /dev/null; then
        print_error "Docker Compose is not installed"
        exit 1
    fi
    
    # Check environment file
    if [ ! -f "$ENV_FILE" ]; then
        print_error "Environment file $ENV_FILE not found"
        exit 1
    fi
    
    # Check compose file
    if [ ! -f "$COMPOSE_FILE" ]; then
        print_error "Docker Compose file $COMPOSE_FILE not found"
        exit 1
    fi
    
    print_status "Prerequisites check passed"
}

# Create necessary directories
create_directories() {
    print_status "Creating necessary directories..."
    
    mkdir -p "$BACKUP_DIR"
    mkdir -p "$LOG_DIR/nginx"
    mkdir -p "$LOG_DIR/main-api"
    mkdir -p "$LOG_DIR/scraper-api"
    mkdir -p "./ssl"
    
    print_status "Directories created"
}

# Backup current deployment
backup_current() {
    print_status "Creating backup of current deployment..."
    
    BACKUP_NAME="backup_$(date +'%Y%m%d_%H%M%S')"
    mkdir -p "$BACKUP_DIR/$BACKUP_NAME"
    
    # Backup docker images
    if docker ps -q | grep -q .; then
        docker ps -a > "$BACKUP_DIR/$BACKUP_NAME/docker_ps.txt"
        print_status "Docker container list backed up"
    fi
    
    # Backup environment file
    if [ -f "$ENV_FILE" ]; then
        cp "$ENV_FILE" "$BACKUP_DIR/$BACKUP_NAME/"
        print_status "Environment file backed up"
    fi
    
    print_status "Backup completed: $BACKUP_NAME"
}

# Build images
build_images() {
    print_status "Building Docker images..."
    
    docker-compose -f "$COMPOSE_FILE" build --no-cache
    
    print_status "Docker images built successfully"
}

# Deploy services
deploy_services() {
    print_status "Deploying services..."
    
    # Stop existing containers
    print_status "Stopping existing containers..."
    docker-compose -f "$COMPOSE_FILE" down
    
    # Start new containers
    print_status "Starting new containers..."
    docker-compose -f "$COMPOSE_FILE" up -d
    
    # Wait for services to be ready
    print_status "Waiting for services to be ready..."
    sleep 10
    
    print_status "Services deployed"
}

# Health check
health_check() {
    print_status "Running health checks..."
    
    # Check main API
    if curl -f http://localhost:8000/health/ready > /dev/null 2>&1; then
        print_status "Main API is healthy"
    else
        print_error "Main API health check failed"
        return 1
    fi
    
    # Check scraper API
    if curl -f http://localhost:8001/health > /dev/null 2>&1; then
        print_status "Scraper API is healthy"
    else
        print_error "Scraper API health check failed"
        return 1
    fi
    
    # Check frontend
    if curl -f http://localhost/health > /dev/null 2>&1; then
        print_status "Frontend is healthy"
    else
        print_error "Frontend health check failed"
        return 1
    fi
    
    print_status "All health checks passed"
}

# Cleanup old images
cleanup() {
    print_status "Cleaning up old images..."
    
    docker image prune -f
    
    # Keep only last 5 backups
    if [ -d "$BACKUP_DIR" ]; then
        cd "$BACKUP_DIR"
        ls -t | tail -n +6 | xargs -r rm -rf
        cd - > /dev/null
    fi
    
    print_status "Cleanup completed"
}

# Main deployment flow
main() {
    print_status "Starting deployment for environment: $ENVIRONMENT"
    
    check_prerequisites
    create_directories
    backup_current
    build_images
    deploy_services
    
    # Run health check
    if health_check; then
        print_status "Deployment completed successfully!"
        cleanup
    else
        print_error "Deployment failed! Rolling back..."
        docker-compose -f "$COMPOSE_FILE" down
        exit 1
    fi
    
    # Show running containers
    print_status "Running containers:"
    docker-compose -f "$COMPOSE_FILE" ps
    
    print_status "Deployment logs available at: $LOG_DIR"
}

# Run main function
main