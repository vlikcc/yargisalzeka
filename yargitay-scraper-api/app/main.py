# /yargitay-scraper-api/app/main.py dosyasının NİHAİ HALİ (MongoDB'siz)

import sys
import time
import asyncio
import concurrent.futures
import hashlib

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from loguru import logger
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from starlette import status
from contextlib import asynccontextmanager

# Yerel importlar
from . import schemas
from .config import settings
from .search_logic import search_single_keyword
from .database import init_database, close_database, db_manager, YargitayDecision, SearchQuery, UserActivity

# --- Loglama Yapılandırması ---
logger.remove()
logger.add(sys.stdout, format="{time} {level} {message}", level=settings.LOG_LEVEL.upper())

# Log to file in production
if settings.is_production and settings.LOG_FILE_PATH:
    logger.add(
        settings.LOG_FILE_PATH,
        rotation=settings.LOG_MAX_SIZE,
        retention=settings.LOG_BACKUP_COUNT,
        level=settings.LOG_LEVEL.upper()
    )

# --- Rate Limiter ---
limiter = Limiter(key_func=get_remote_address)

# --- In-memory cache for search results ---
search_cache = {}
search_stats = {"total_searches": 0, "total_results": 0}

# --- Uygulama Yaşam Döngüsü ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Yargıtay Scraper API başlatıldı")
    
    # MongoDB Atlas bağlantısını başlat (hata durumunda fallback)
    try:
        db_connected = await init_database()
        if db_connected:
            logger.info("MongoDB Atlas bağlantısı başarılı")
        else:
            logger.warning("MongoDB Atlas bağlantısı başarısız - in-memory cache modunda çalışılacak")
    except Exception as e:
        logger.error(f"Database initialization hatası: {e} - fallback mode aktif")
        db_connected = False
    
    yield
    
    # MongoDB bağlantısını güvenli şekilde kapat
    try:
        await close_database()
        logger.info("MongoDB bağlantısı kapatıldı")
    except Exception as e:
        logger.warning(f"Database kapatma hatası: {e}")
    logger.info("Yargıtay Scraper API kapatıldı")

# --- FastAPI Uygulaması ---
app = FastAPI(
    title="Yargıtay Scraper API",
    description="Yargıtay Karar Arama Servisi (MongoDB Atlas)",
    version="2.1.0",
    lifespan=lifespan,
    docs_url="/docs" if not settings.is_production else None,
    redoc_url="/redoc" if not settings.is_production else None
)

# Rate limiting
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Security middleware for production
if settings.is_production:
    # Trusted host middleware
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=["yargisalzeka.com", "www.yargisalzeka.com", "api.yargisalzeka.com", "localhost"]
    )

# CORS middleware
app.add_middleware(
    CORSMiddleware, 
    allow_origins=settings.cors_origins_list,
    allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
    allow_methods=settings.cors_methods_list,
    allow_headers=settings.cors_headers_list
)

# --- Helper Functions ---
def generate_cache_key(keywords):
    """Anahtar kelimelerden cache key oluşturur"""
    keywords_str = ",".join(sorted(keywords))
    return hashlib.md5(keywords_str.encode()).hexdigest()

# --- API Endpoints ---

@app.get("/health", tags=["Health"])
async def health_check():
    """API sağlık kontrolü"""
    return {
        "status": "healthy",
        "service": "Yargıtay Scraper API",
        "version": "2.1.0",
        "environment": settings.ENVIRONMENT,
        "stats": search_stats
    }

@app.get("/", tags=["Root"])
async def root():
    """Ana sayfa"""
    return {
        "message": "Yargıtay Scraper API'sine hoş geldiniz",
        "version": "2.1.0",
        "endpoints": {
            "health": "/health",
            "search": "/search",
            "docs": "/docs" if not settings.is_production else None
        }
    }

@app.post("/search", response_model=schemas.SearchResponse, tags=["Search"])
@limiter.limit(settings.USER_RATE_LIMIT)
async def search_decisions(request: Request, search_request: schemas.SearchRequest):
    """
    Yargıtay kararlarını anahtar kelimelerle arar
    
    - **keywords**: Aranacak anahtar kelimeler listesi
    - **max_results**: Maksimum sonuç sayısı (varsayılan: 10)
    """
    try:
        start_time = time.time()
        
        # Input validation
        if not search_request.keywords:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="En az bir anahtar kelime gerekli"
            )
        
        if len(search_request.keywords) > 10:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="En fazla 10 anahtar kelime kullanabilirsiniz"
            )
        
        # Cache kontrolü
        cache_key = generate_cache_key(search_request.keywords)
        if cache_key in search_cache:
            logger.info(f"Cache hit for keywords: {search_request.keywords}")
            cached_result = search_cache[cache_key]
            cached_result["from_cache"] = True
            return cached_result
        
        logger.info(f"Arama başlatıldı - Anahtar kelimeler: {search_request.keywords}")
        
        # MongoDB'den önce ara
        db_results = await db_manager.search_decisions(search_request.keywords)
        if db_results:
            logger.info(f"MongoDB'den {len(db_results)} sonuç bulundu")
            
            # SearchQuery kaydı oluştur
            await db_manager.create_search_query(
                keywords=search_request.keywords,
                results_count=len(db_results),
                source="mongodb"
            )
            
            response = schemas.SearchResponse(
                keywords=search_request.keywords,
                results=db_results,
                total_results=len(db_results),
                search_time=time.time() - start_time,
                from_cache=False,
                source="mongodb"
            )
            
            # Cache'e kaydet
            search_cache[cache_key] = response.dict()
            return response
        
        # MongoDB'de yoksa scraping yap
        logger.info("MongoDB'de sonuç bulunamadı, scraping başlatılıyor...")
        
        # Thread pool executor ile paralel arama
        all_results = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=settings.MAX_WORKERS) as executor:
            # Her anahtar kelime için ayrı bir thread başlat
            future_to_keyword = {
                executor.submit(search_single_keyword, keyword): keyword 
                for keyword in search_request.keywords
            }
            
            # Sonuçları topla
            for future in concurrent.futures.as_completed(future_to_keyword):
                keyword = future_to_keyword[future]
                try:
                    results = future.result()
                    logger.info(f"'{keyword}' için {len(results)} sonuç bulundu")
                    all_results.extend(results)
                except Exception as e:
                    logger.error(f"'{keyword}' aramasında hata: {str(e)}")
        
        # Duplicate'leri kaldır (URL bazlı)
        unique_results = []
        seen_urls = set()
        for result in all_results:
            if result.get("url") not in seen_urls:
                seen_urls.add(result.get("url"))
                unique_results.append(result)
        
        # Sonuçları MongoDB'ye kaydet
        if unique_results:
            saved_count = await db_manager.save_decisions(unique_results)
            logger.info(f"{saved_count} yeni karar MongoDB'ye kaydedildi")
        
        # SearchQuery kaydı oluştur
        await db_manager.create_search_query(
            keywords=search_request.keywords,
            results_count=len(unique_results),
            source="scraping"
        )
        
        # İstatistikleri güncelle
        search_stats["total_searches"] += 1
        search_stats["total_results"] += len(unique_results)
        
        # Response oluştur
        search_time = time.time() - start_time
        response = schemas.SearchResponse(
            keywords=search_request.keywords,
            results=unique_results[:search_request.max_results],
            total_results=len(unique_results),
            search_time=search_time,
            from_cache=False,
            source="scraping"
        )
        
        # Cache'e kaydet
        search_cache[cache_key] = response.dict()
        
        logger.info(f"Arama tamamlandı - Toplam {len(unique_results)} sonuç, {search_time:.2f} saniye")
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Arama hatası: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Arama sırasında hata oluştu: {str(e)}"
        )

@app.get("/stats", tags=["Statistics"])
async def get_stats():
    """API istatistiklerini döndürür"""
    return {
        "search_stats": search_stats,
        "cache_size": len(search_cache),
        "service_info": {
            "name": "Yargıtay Scraper API",
            "version": "2.0.0",
            "database": "In-Memory Cache",
            "rate_limit": settings.USER_RATE_LIMIT
        }
    }

@app.delete("/cache", tags=["Cache"])
async def clear_cache():
    """Cache'i temizler"""
    global search_cache
    cache_size = len(search_cache)
    search_cache.clear()
    logger.info(f"Cache temizlendi: {cache_size} kayıt silindi")
    return {
        "message": f"Cache başarıyla temizlendi",
        "cleared_entries": cache_size
    }

