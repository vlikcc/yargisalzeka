# Terraform configuration for Yargısal Zeka on Google Cloud
terraform {
  required_version = ">= 1.0"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }
}

# Variables
variable "project_id" {
  description = "GCP Project ID"
  type        = string
}

variable "region" {
  description = "GCP Region"
  type        = string
  default     = "europe-west1"
}

variable "domain_name" {
  description = "Domain name for the application"
  type        = string
  default     = "yargisalzeka.com"
}

variable "gemini_api_key" {
  description = "Google Gemini API Key"
  type        = string
  sensitive   = true
}

variable "jwt_secret_key" {
  description = "JWT Secret Key"
  type        = string
  sensitive   = true
}

# Provider configuration
provider "google" {
  project = var.project_id
  region  = var.region
}

# Enable required APIs
resource "google_project_service" "required_apis" {
  for_each = toset([
    "run.googleapis.com",
    "cloudbuild.googleapis.com",
    "cloudfunctions.googleapis.com",
    "firestore.googleapis.com",
    "secretmanager.googleapis.com",
    "storage.googleapis.com",
    "cloudresourcemanager.googleapis.com",
    "iam.googleapis.com",
    "monitoring.googleapis.com",
    "logging.googleapis.com"
  ])

  service = each.key
  project = var.project_id

  disable_dependent_services = false
}

# Firestore Database
resource "google_firestore_database" "database" {
  project     = var.project_id
  name        = "(default)"
  location_id = var.region
  type        = "FIRESTORE_NATIVE"

  depends_on = [google_project_service.required_apis]
}

# Secret Manager secrets
resource "google_secret_manager_secret" "gemini_api_key" {
  secret_id = "gemini-api-key"
  project   = var.project_id

  replication {
    auto {}
  }

  depends_on = [google_project_service.required_apis]
}

resource "google_secret_manager_secret_version" "gemini_api_key" {
  secret      = google_secret_manager_secret.gemini_api_key.id
  secret_data = var.gemini_api_key
}

resource "google_secret_manager_secret" "jwt_secret_key" {
  secret_id = "jwt-secret-key"
  project   = var.project_id

  replication {
    auto {}
  }

  depends_on = [google_project_service.required_apis]
}

resource "google_secret_manager_secret_version" "jwt_secret_key" {
  secret      = google_secret_manager_secret.jwt_secret_key.id
  secret_data = var.jwt_secret_key
}

# Cloud Storage bucket for static assets
resource "google_storage_bucket" "static_assets" {
  name          = "${var.project_id}-static-assets"
  location      = var.region
  force_destroy = true

  uniform_bucket_level_access = true

  website {
    main_page_suffix = "index.html"
    not_found_page   = "404.html"
  }

  cors {
    origin          = ["https://${var.domain_name}", "https://www.${var.domain_name}"]
    method          = ["GET", "HEAD", "PUT", "POST", "DELETE"]
    response_header = ["*"]
    max_age_seconds = 3600
  }
}

# Cloud Storage bucket for backups
resource "google_storage_bucket" "backups" {
  name          = "${var.project_id}-backups"
  location      = var.region
  force_destroy = false

  uniform_bucket_level_access = true

  lifecycle_rule {
    condition {
      age = 90
    }
    action {
      type = "Delete"
    }
  }

  lifecycle_rule {
    condition {
      age = 30
    }
    action {
      type          = "SetStorageClass"
      storage_class = "COLDLINE"
    }
  }
}

# Service Account for Cloud Run services
resource "google_service_account" "cloud_run_sa" {
  account_id   = "yargisalzeka-cloud-run"
  display_name = "Yargısal Zeka Cloud Run Service Account"
  project      = var.project_id
}

# IAM bindings for the service account
resource "google_project_iam_member" "cloud_run_sa_firestore" {
  project = var.project_id
  role    = "roles/datastore.user"
  member  = "serviceAccount:${google_service_account.cloud_run_sa.email}"
}

resource "google_project_iam_member" "cloud_run_sa_secretmanager" {
  project = var.project_id
  role    = "roles/secretmanager.secretAccessor"
  member  = "serviceAccount:${google_service_account.cloud_run_sa.email}"
}

resource "google_project_iam_member" "cloud_run_sa_storage" {
  project = var.project_id
  role    = "roles/storage.objectAdmin"
  member  = "serviceAccount:${google_service_account.cloud_run_sa.email}"
}

resource "google_project_iam_member" "cloud_run_sa_logging" {
  project = var.project_id
  role    = "roles/logging.logWriter"
  member  = "serviceAccount:${google_service_account.cloud_run_sa.email}"
}

resource "google_project_iam_member" "cloud_run_sa_monitoring" {
  project = var.project_id
  role    = "roles/monitoring.metricWriter"
  member  = "serviceAccount:${google_service_account.cloud_run_sa.email}"
}

# Cloud Run service for Main API
resource "google_cloud_run_service" "main_api" {
  name     = "yargisalzeka-api"
  location = var.region
  project  = var.project_id

  template {
    spec {
      service_account_name = google_service_account.cloud_run_sa.email
      
      containers {
        image = "gcr.io/${var.project_id}/yargisalzeka-main-api:latest"
        
        ports {
          container_port = 8000
        }
        
        env {
          name  = "ENVIRONMENT"
          value = "production"
        }
        
        env {
          name  = "GCP_PROJECT"
          value = var.project_id
        }
        
        env {
          name = "GEMINI_API_KEY"
          value_from {
            secret_key_ref {
              name = google_secret_manager_secret.gemini_api_key.secret_id
              key  = "latest"
            }
          }
        }
        
        env {
          name = "JWT_SECRET_KEY"
          value_from {
            secret_key_ref {
              name = google_secret_manager_secret.jwt_secret_key.secret_id
              key  = "latest"
            }
          }
        }
        
        resources {
          limits = {
            cpu    = "2000m"
            memory = "2Gi"
          }
        }
      }
      
      container_concurrency = 80
      timeout_seconds       = 300
    }
    
    metadata {
      annotations = {
        "autoscaling.knative.dev/maxScale" = "100"
        "autoscaling.knative.dev/minScale" = "1"
        "run.googleapis.com/cpu-throttling" = "false"
      }
    }
  }

  traffic {
    percent         = 100
    latest_revision = true
  }

  depends_on = [google_project_service.required_apis]
}

# Cloud Run service for Frontend
resource "google_cloud_run_service" "frontend" {
  name     = "yargisalzeka-frontend"
  location = var.region
  project  = var.project_id

  template {
    spec {
      service_account_name = google_service_account.cloud_run_sa.email
      
      containers {
        image = "gcr.io/${var.project_id}/yargisalzeka-frontend:latest"
        
        ports {
          container_port = 8080
        }
        
        env {
          name  = "API_URL"
          value = google_cloud_run_service.main_api.status[0].url
        }
        
        resources {
          limits = {
            cpu    = "1000m"
            memory = "512Mi"
          }
        }
      }
      
      container_concurrency = 1000
      timeout_seconds       = 60
    }
    
    metadata {
      annotations = {
        "autoscaling.knative.dev/maxScale" = "50"
        "autoscaling.knative.dev/minScale" = "0"
      }
    }
  }

  traffic {
    percent         = 100
    latest_revision = true
  }

  depends_on = [google_project_service.required_apis]
}

# Cloud Function for Yargıtay Scraper
resource "google_cloudfunctions_function" "yargitay_scraper" {
  name        = "yargitay-scraper"
  description = "Yargıtay decision scraper function"
  runtime     = "python311"
  region      = var.region
  project     = var.project_id
  entry_point = "scrape_yargitay"

  available_memory_mb   = 2048
  timeout               = 540
  max_instances         = 10
  service_account_email = google_service_account.cloud_run_sa.email

  source_archive_bucket = google_storage_bucket.static_assets.name
  source_archive_object = "scraper-function.zip"

  trigger_http = true

  environment_variables = {
    GCP_PROJECT  = var.project_id
    ENVIRONMENT  = "production"
  }

  depends_on = [google_project_service.required_apis]
}

# IAM policy for Cloud Run services (allow unauthenticated access)
resource "google_cloud_run_service_iam_member" "main_api_public" {
  service  = google_cloud_run_service.main_api.name
  location = google_cloud_run_service.main_api.location
  role     = "roles/run.invoker"
  member   = "allUsers"
}

resource "google_cloud_run_service_iam_member" "frontend_public" {
  service  = google_cloud_run_service.frontend.name
  location = google_cloud_run_service.frontend.location
  role     = "roles/run.invoker"
  member   = "allUsers"
}

# Cloud Load Balancer for custom domain
resource "google_compute_global_address" "default" {
  name         = "yargisalzeka-ip"
  ip_version   = "IPV4"
  address_type = "EXTERNAL"
}

# SSL Certificate (managed by Google)
resource "google_compute_managed_ssl_certificate" "default" {
  name = "yargisalzeka-ssl-cert"

  managed {
    domains = [var.domain_name, "www.${var.domain_name}"]
  }
}

# URL Map
resource "google_compute_url_map" "default" {
  name            = "yargisalzeka-url-map"
  default_service = google_compute_backend_service.frontend.id

  host_rule {
    hosts        = [var.domain_name, "www.${var.domain_name}"]
    path_matcher = "allpaths"
  }

  path_matcher {
    name            = "allpaths"
    default_service = google_compute_backend_service.frontend.id

    path_rule {
      paths   = ["/api/*"]
      service = google_compute_backend_service.main_api.id
    }
  }
}

# Backend service for Main API
resource "google_compute_backend_service" "main_api" {
  name        = "yargisalzeka-api-backend"
  protocol    = "HTTP"

  backend {
    group = google_compute_region_network_endpoint_group.main_api.id
  }
}

# Backend service for Frontend
resource "google_compute_backend_service" "frontend" {
  name        = "yargisalzeka-frontend-backend"
  protocol    = "HTTP"

  backend {
    group = google_compute_region_network_endpoint_group.frontend.id
  }
}

# Network Endpoint Groups
resource "google_compute_region_network_endpoint_group" "main_api" {
  name                  = "yargisalzeka-api-neg"
  network_endpoint_type = "SERVERLESS"
  region                = var.region

  cloud_run {
    service = google_cloud_run_service.main_api.name
  }
}

resource "google_compute_region_network_endpoint_group" "frontend" {
  name                  = "yargisalzeka-frontend-neg"
  network_endpoint_type = "SERVERLESS"
  region                = var.region

  cloud_run {
    service = google_cloud_run_service.frontend.name
  }
}

# HTTPS Proxy
resource "google_compute_target_https_proxy" "default" {
  name             = "yargisalzeka-https-proxy"
  url_map          = google_compute_url_map.default.id
  ssl_certificates = [google_compute_managed_ssl_certificate.default.id]
}

# Global Forwarding Rule
resource "google_compute_global_forwarding_rule" "default" {
  name       = "yargisalzeka-forwarding-rule"
  target     = google_compute_target_https_proxy.default.id
  port_range = "443"
  ip_address = google_compute_global_address.default.address
}

# HTTP to HTTPS redirect
resource "google_compute_url_map" "https_redirect" {
  name = "yargisalzeka-https-redirect"

  default_url_redirect {
    https_redirect         = true
    redirect_response_code = "MOVED_PERMANENTLY_DEFAULT"
    strip_query            = false
  }
}

resource "google_compute_target_http_proxy" "https_redirect" {
  name    = "yargisalzeka-http-proxy"
  url_map = google_compute_url_map.https_redirect.id
}

resource "google_compute_global_forwarding_rule" "https_redirect" {
  name       = "yargisalzeka-http-forwarding-rule"
  target     = google_compute_target_http_proxy.https_redirect.id
  port_range = "80"
  ip_address = google_compute_global_address.default.address
}

# Outputs
output "load_balancer_ip" {
  description = "IP address of the load balancer"
  value       = google_compute_global_address.default.address
}

output "main_api_url" {
  description = "URL of the main API service"
  value       = google_cloud_run_service.main_api.status[0].url
}

output "frontend_url" {
  description = "URL of the frontend service"
  value       = google_cloud_run_service.frontend.status[0].url
}

output "scraper_function_url" {
  description = "URL of the scraper function"
  value       = google_cloudfunctions_function.yargitay_scraper.https_trigger_url
}

output "domain_instructions" {
  description = "Instructions for domain configuration"
  value = <<EOF
To configure your domain:
1. Point your domain's A record to: ${google_compute_global_address.default.address}
2. Add CNAME record for www: www.${var.domain_name} -> ${var.domain_name}
3. Wait for SSL certificate to be provisioned (may take up to 60 minutes)
EOF
}

