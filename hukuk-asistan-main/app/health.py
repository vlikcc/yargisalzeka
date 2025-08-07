from fastapi import APIRouter, HTTPException
from typing import Dict, Any
import httpx
from loguru import logger
from .config import settings
from .database import db_manager
from .ai_service import gemini_service

router = APIRouter(prefix="/health", tags=["Health"])


@router.get("")
async def health_check() -> Dict[str, Any]:
    """Basit health check endpoint"""
    return {
        "status": "healthy",
        "service": "Yargısal Zeka API",
        "version": settings.API_VERSION,
        "environment": settings.ENVIRONMENT
    }


@router.get("/live")
async def liveness_probe() -> Dict[str, Any]:
    """
    Kubernetes liveness probe için endpoint
    Servisin çalışıp çalışmadığını kontrol eder
    """
    return {
        "status": "alive",
        "timestamp": str(db_manager.get_current_time())
    }


@router.get("/ready")
async def readiness_probe() -> Dict[str, Any]:
    """
    Kubernetes readiness probe için endpoint
    Servisin trafik almaya hazır olup olmadığını kontrol eder
    """
    checks = {
        "database": False,
        "scraper_api": False,
        "gemini_api": False
    }
    
    # Database check
    try:
        if db_manager.is_connected():
            # Simple query to verify connection
            await db_manager.get_system_settings()
            checks["database"] = True
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
    
    # Scraper API check
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{settings.SCRAPER_API_URL}/health",
                timeout=5.0
            )
            if response.status_code == 200:
                checks["scraper_api"] = True
    except Exception as e:
        logger.error(f"Scraper API health check failed: {e}")
    
    # Gemini API check
    try:
        # Simple test to verify Gemini API is accessible
        test_result = await gemini_service.extract_keywords_from_case("test")
        if isinstance(test_result, list):
            checks["gemini_api"] = True
    except Exception as e:
        logger.error(f"Gemini API health check failed: {e}")
    
    # Overall status
    all_healthy = all(checks.values())
    
    response = {
        "status": "ready" if all_healthy else "not_ready",
        "checks": checks,
        "timestamp": str(db_manager.get_current_time())
    }
    
    if not all_healthy:
        raise HTTPException(status_code=503, detail=response)
    
    return response


@router.get("/startup")
async def startup_probe() -> Dict[str, Any]:
    """
    Kubernetes startup probe için endpoint
    Uygulamanın başlangıç işlemlerini tamamlayıp tamamlamadığını kontrol eder
    """
    startup_checks = {
        "database_initialized": db_manager.is_connected(),
        "configs_loaded": bool(settings.GEMINI_API_KEY),
        "environment": settings.ENVIRONMENT
    }
    
    all_ready = all([
        startup_checks["database_initialized"],
        startup_checks["configs_loaded"]
    ])
    
    response = {
        "status": "started" if all_ready else "starting",
        "checks": startup_checks,
        "timestamp": str(db_manager.get_current_time())
    }
    
    if not all_ready:
        raise HTTPException(status_code=503, detail=response)
    
    return response


@router.get("/detailed")
async def detailed_health_check() -> Dict[str, Any]:
    """
    Detaylı health check - monitoring sistemleri için
    """
    health_data = {
        "service": {
            "name": "Yargısal Zeka API",
            "version": settings.API_VERSION,
            "environment": settings.ENVIRONMENT
        },
        "dependencies": {},
        "metrics": {},
        "timestamp": str(db_manager.get_current_time())
    }
    
    # Database metrics
    try:
        if db_manager.is_connected():
            db_stats = await db_manager.get_database_stats()
            health_data["dependencies"]["database"] = {
                "status": "healthy",
                "connected": True,
                "stats": db_stats
            }
        else:
            health_data["dependencies"]["database"] = {
                "status": "unhealthy",
                "connected": False
            }
    except Exception as e:
        health_data["dependencies"]["database"] = {
            "status": "error",
            "error": str(e)
        }
    
    # Scraper API status
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{settings.SCRAPER_API_URL}/health",
                timeout=5.0
            )
            health_data["dependencies"]["scraper_api"] = {
                "status": "healthy" if response.status_code == 200 else "unhealthy",
                "response_code": response.status_code,
                "data": response.json() if response.status_code == 200 else None
            }
    except Exception as e:
        health_data["dependencies"]["scraper_api"] = {
            "status": "error",
            "error": str(e)
        }
    
    # Gemini API status
    health_data["dependencies"]["gemini_api"] = {
        "status": "configured" if settings.GEMINI_API_KEY else "not_configured",
        "has_key": bool(settings.GEMINI_API_KEY)
    }
    
    # System metrics
    try:
        import psutil
        health_data["metrics"]["system"] = {
            "cpu_percent": psutil.cpu_percent(interval=1),
            "memory_percent": psutil.virtual_memory().percent,
            "disk_percent": psutil.disk_usage('/').percent
        }
    except:
        pass
    
    return health_data