# 🚀 Yargısal Zeka Production Deployment Guide

## 📋 Ön Gereksinimler

### Sunucu Gereksinimleri
- **OS**: Ubuntu 20.04+ veya CentOS 8+
- **CPU**: Minimum 4 vCPU (8 vCPU önerilir)
- **RAM**: Minimum 8GB (16GB önerilir)
- **Disk**: Minimum 50GB SSD
- **Network**: Açık portlar: 80, 443, 22

### Yazılım Gereksinimleri
- Docker 20.10+
- Docker Compose 2.0+
- Git
- Nginx (reverse proxy için)
- Certbot (SSL sertifikası için)

## 🔧 Kurulum Adımları

### 1. Sunucu Hazırlığı

```bash
# Sistem güncellemeleri
sudo apt update && sudo apt upgrade -y

# Docker kurulumu
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# Docker Compose kurulumu
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

### 2. Proje Kurulumu

```bash
# Proje dizini oluştur
sudo mkdir -p /opt/yargisalzeka
sudo chown $USER:$USER /opt/yargisalzeka
cd /opt/yargisalzeka

# Repository'yi klonla
git clone https://github.com/vlikcc/yargisalzeka.git .
```

### 3. Environment Ayarları

```bash
# Production environment dosyasını oluştur
cp .env.example .env.production

# Editör ile düzenle
nano .env.production
```

**Önemli Environment Variables:**
- `GEMINI_API_KEY`: Google Gemini API anahtarı
- `MONGODB_CONNECTION_STRING`: MongoDB Atlas bağlantı string'i
- `API_SECRET_KEY`: Güçlü bir secret key oluştur
- `JWT_SECRET_KEY`: JWT için güçlü bir secret key
- `CORS_ORIGINS`: Production domain'leri

### 4. SSL Sertifikası

```bash
# Certbot kurulumu
sudo apt install certbot python3-certbot-nginx -y

# SSL sertifikası al
sudo certbot --nginx -d yargisalzeka.com -d www.yargisalzeka.com -d api.yargisalzeka.com
```

### 5. Deployment

```bash
# Deploy script'ini çalıştırılabilir yap
chmod +x deploy.sh

# Production deployment
./deploy.sh production
```

## 🔒 Güvenlik Ayarları

### Firewall Konfigürasyonu

```bash
# UFW kurulumu ve ayarları
sudo apt install ufw -y
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow ssh
sudo ufw allow http
sudo ufw allow https
sudo ufw enable
```

### Fail2ban Kurulumu

```bash
# Fail2ban kurulumu
sudo apt install fail2ban -y

# Konfigürasyon
sudo cp /etc/fail2ban/jail.conf /etc/fail2ban/jail.local
sudo systemctl enable fail2ban
sudo systemctl start fail2ban
```

## 📊 Monitoring

### 1. Prometheus & Grafana Setup (Opsiyonel)

```yaml
# monitoring/docker-compose.yml
version: '3.8'
services:
  prometheus:
    image: prom/prometheus
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus-data:/prometheus
    ports:
      - "9090:9090"
  
  grafana:
    image: grafana/grafana
    volumes:
      - grafana-data:/var/lib/grafana
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=secure_password

volumes:
  prometheus-data:
  grafana-data:
```

### 2. Log Management

```bash
# Log rotation ayarları
sudo nano /etc/logrotate.d/yargisalzeka

# İçerik:
/opt/yargisalzeka/logs/*.log {
    daily
    rotate 14
    compress
    delaycompress
    notifempty
    create 0640 www-data www-data
    sharedscripts
    postrotate
        docker-compose -f /opt/yargisalzeka/docker-compose.production.yml kill -s USR1 nginx
    endscript
}
```

## 🔄 Backup Stratejisi

### Otomatik Backup Script

```bash
#!/bin/bash
# /opt/yargisalzeka/backup.sh

BACKUP_DIR="/backup/yargisalzeka"
DATE=$(date +%Y%m%d_%H%M%S)

# MongoDB backup (Atlas otomatik backup kullanılıyor)
# Logs backup
tar -czf "$BACKUP_DIR/logs_$DATE.tar.gz" /opt/yargisalzeka/logs/

# Environment backup
cp /opt/yargisalzeka/.env.production "$BACKUP_DIR/env_$DATE"

# Eski backupları temizle (30 günden eski)
find $BACKUP_DIR -type f -mtime +30 -delete
```

### Cron Job

```bash
# Crontab düzenle
crontab -e

# Her gün saat 02:00'de backup al
0 2 * * * /opt/yargisalzeka/backup.sh
```

## 🚨 Troubleshooting

### Container Loglarını Kontrol Et

```bash
# Tüm servislerin logları
docker-compose -f docker-compose.production.yml logs -f

# Belirli bir servisin logları
docker-compose -f docker-compose.production.yml logs -f main-api
```

### Health Check

```bash
# API health check
curl http://localhost:8000/health/detailed

# Frontend health check
curl http://localhost/health
```

### Container Restart

```bash
# Tek bir servisi restart et
docker-compose -f docker-compose.production.yml restart main-api

# Tüm servisleri restart et
docker-compose -f docker-compose.production.yml restart
```

## 📈 Performance Tuning

### Docker Resource Limits

```yaml
# docker-compose.production.yml içinde
services:
  main-api:
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 4G
        reservations:
          cpus: '1'
          memory: 2G
```

### Nginx Optimization

```nginx
# /etc/nginx/nginx.conf
worker_processes auto;
worker_rlimit_nofile 65535;

events {
    worker_connections 4096;
    use epoll;
    multi_accept on;
}

http {
    # Buffer sizes
    client_body_buffer_size 16K;
    client_header_buffer_size 1k;
    large_client_header_buffers 4 16k;
    
    # Timeouts
    client_body_timeout 12;
    client_header_timeout 12;
    keepalive_timeout 15;
    send_timeout 10;
    
    # Gzip
    gzip on;
    gzip_comp_level 6;
    gzip_types text/plain text/css text/xml text/javascript application/json application/javascript;
}
```

## 🔐 Security Checklist

- [ ] Tüm environment variable'lar güvenli değerlerle dolduruldu
- [ ] SSL sertifikası kuruldu ve otomatik yenileme aktif
- [ ] Firewall kuralları yapılandırıldı
- [ ] Fail2ban kuruldu ve yapılandırıldı
- [ ] Docker imajları güncel
- [ ] Gereksiz portlar kapatıldı
- [ ] Log rotation yapılandırıldı
- [ ] Backup stratejisi uygulandı
- [ ] Monitoring kuruldu
- [ ] Rate limiting aktif

## 📞 Destek

Deployment sırasında sorun yaşarsanız:
- GitHub Issues: https://github.com/vlikcc/yargisalzeka/issues
- Email: destek@yargisalzeka.com