import sys
import httpx
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from loguru import logger
from contextlib import asynccontextmanager

from .config import settings
from .schemas import (
    KeywordExtractionRequest, KeywordExtractionResponse,
    DecisionAnalysisRequest, DecisionAnalysisResponse,
    PetitionGenerationRequest, PetitionGenerationResponse,
    SmartSearchRequest, SmartSearchResponse,
    WorkflowAnalysisRequest, WorkflowAnalysisResponse
)
from .ai_service import gemini_service
from .workflow_service import workflow_service
from .database import init_database, close_database, db_manager, log_api_usage
from .middleware import TimingMiddleware, ErrorHandlingMiddleware, SecurityHeadersMiddleware, MetricsRoute
from .health import router as health_router

# --- Rate Limiter ---
limiter = Limiter(key_func=get_remote_address)

# --- Loglama ---
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

# --- Uygulama ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    # MongoDB Atlas bağlantısını başlat
    db_connected = await init_database()
    if db_connected:
        logger.info("Main API MongoDB Atlas bağlantısı başarılı")
    else:
        logger.warning("Main API MongoDB Atlas bağlantısı başarısız - cache modunda çalışılacak")
    
    # httpx client'ı yapılandır
    timeout = httpx.Timeout(
        connect=5.0,   # Bağlantı timeout'u
        read=settings.REQUEST_TIMEOUT,     # Okuma timeout'u (AI işlemleri için daha uzun)
        write=5.0,     # Yazma timeout'u
        pool=5.0       # Pool timeout'u
    )
    app.state.http_client = httpx.AsyncClient(timeout=timeout)
    logger.info("Yargısal Zeka API'si başlatıldı.")
    yield
    
    # Cleanup
    await app.state.http_client.aclose()
    await close_database()
    logger.info("Yargısal Zeka API'si kapatıldı.")

app = FastAPI(
    title=settings.API_TITLE,
    version=settings.API_VERSION,
    description=settings.API_DESCRIPTION + " (MongoDB Atlas)",
    lifespan=lifespan,
    docs_url="/docs" if not settings.is_production else None,
    redoc_url="/redoc" if not settings.is_production else None,
    # Custom route class for metrics
    route_class=MetricsRoute
)

# Add custom middleware
app.add_middleware(TimingMiddleware)
app.add_middleware(ErrorHandlingMiddleware)
app.add_middleware(SecurityHeadersMiddleware)

# Rate limiting
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Security middleware for production
if settings.is_production:
    # Trusted host middleware
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=["yargisalzeka.com", "www.yargisalzeka.com", "api.yargisalzeka.com"]
    )

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
    allow_methods=settings.cors_methods_list,
    allow_headers=settings.cors_headers_list,
)

# Include routers
app.include_router(health_router)

# --- Root Endpoints ---
@app.get("/")
async def root():
    """Ana sayfa"""
    return {
        "message": "Yargısal Zeka API'sine hoş geldiniz",
        "version": settings.API_VERSION,
        "docs": "/docs" if not settings.is_production else None
    }

# --- AI Mikroservisleri ---

@app.post("/api/v1/ai/extract-keywords", response_model=KeywordExtractionResponse)
@limiter.limit(settings.USER_RATE_LIMIT)
async def extract_keywords(request: Request, keyword_request: KeywordExtractionRequest):
    """
    Olay metninden hukuki anahtar kelimeleri çıkarır
    """
    try:
        keywords = await gemini_service.extract_keywords_from_case(keyword_request.case_text)
        return KeywordExtractionResponse(
            keywords=keywords,
            success=True,
            message=f"{len(keywords)} anahtar kelime başarıyla çıkarıldı"
        )
    except Exception as e:
        logger.error(f"Anahtar kelime çıkarma hatası: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/ai/analyze-decision", response_model=DecisionAnalysisResponse)
@limiter.limit(settings.USER_RATE_LIMIT)
async def analyze_decision(request: Request, analysis_request: DecisionAnalysisRequest):
    """
    Yargıtay kararını olay metni ile karşılaştırarak analiz eder
    """
    try:
        analysis = await gemini_service.analyze_decision_relevance(
            analysis_request.case_text, 
            analysis_request.decision
        )
        return DecisionAnalysisResponse(
            score=analysis["score"],
            explanation=analysis["explanation"],
            key_similarities=analysis["key_similarities"],
            success=True
        )
    except Exception as e:
        logger.error(f"Karar analizi hatası: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/ai/generate-petition", response_model=PetitionGenerationResponse)
@limiter.limit(settings.USER_RATE_LIMIT)
async def generate_petition(request: Request, petition_request: PetitionGenerationRequest):
    """
    Verilen kararlar ve olay metnine göre dilekçe şablonu oluşturur
    """
    try:
        petition = await gemini_service.generate_petition_template(
            petition_request.case_text, 
            petition_request.relevant_decisions
        )
        return PetitionGenerationResponse(
            petition_template=petition,
            success=True,
            message="Dilekçe şablonu başarıyla oluşturuldu"
        )
    except Exception as e:
        logger.error(f"Dilekçe oluşturma hatası: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/ai/smart-search", response_model=SmartSearchResponse)
@limiter.limit(settings.USER_RATE_LIMIT)
async def smart_search(request: Request, search_request: SmartSearchRequest):
    """
    Olay metnini analiz ederek akıllı arama yapar
    """
    try:
        # 1. Anahtar kelimeleri çıkar
        keywords = await gemini_service.extract_keywords_from_case(search_request.case_text)
        
        if not keywords:
            return SmartSearchResponse(
                keywords=[],
                decisions=[],
                success=False,
                message="Anahtar kelime çıkarılamadı"
            )
        
        # 2. Yargıtay kararlarını ara
        scraper_url = f"{settings.SCRAPER_API_URL}/search"
        
        try:
            response = await request.app.state.http_client.post(
                scraper_url,
                json={"keywords": keywords}
            )
            response.raise_for_status()
            search_results = response.json()
        except Exception as e:
            logger.error(f"Scraper API hatası: {str(e)}")
            return SmartSearchResponse(
                keywords=keywords,
                decisions=[],
                success=False,
                message=f"Arama servisi hatası: {str(e)}"
            )
        
        # 3. Sonuçları döndür
        decisions = search_results.get("results", [])
        
        # 4. Kararları analiz et ve puanla
        for decision in decisions:
            try:
                analysis = await gemini_service.analyze_decision_relevance(
                    search_request.case_text,
                    decision
                )
                decision["relevance_score"] = analysis["score"]
                decision["relevance_explanation"] = analysis["explanation"]
            except Exception as e:
                logger.warning(f"Karar analizi başarısız: {str(e)}")
                decision["relevance_score"] = 0
                decision["relevance_explanation"] = "Analiz başarısız"
        
        # 5. Puanına göre sırala
        decisions.sort(key=lambda x: x.get("relevance_score", 0), reverse=True)
        
        # 6. Limit uygula
        if search_request.max_results:
            decisions = decisions[:search_request.max_results]
        
        return SmartSearchResponse(
            keywords=keywords,
            decisions=decisions,
            success=True,
            message=f"{len(decisions)} karar bulundu ve analiz edildi"
        )
        
    except Exception as e:
        logger.error(f"Akıllı arama hatası: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# --- Workflow Mikroservisi ---

@app.post("/api/v1/workflow/complete-analysis", response_model=WorkflowAnalysisResponse)
@limiter.limit("5/minute")
async def complete_analysis(request: Request, workflow_request: WorkflowAnalysisRequest):
    """
    Tam analiz workflow'u: Anahtar kelime çıkarma, arama, analiz ve dilekçe oluşturma
    """
    try:
        result = await workflow_service.complete_analysis_workflow(
            request=request,
            case_text=workflow_request.case_text,
            max_results=workflow_request.max_results,
            include_petition=workflow_request.include_petition
        )
        
        # API kullanımını logla
        await log_api_usage(
            endpoint="/api/v1/workflow/complete-analysis",
            method="POST",
            status_code=200,
            response_time=0,  # TODO: Gerçek response time hesapla
            user_ip=request.client.host if request.client else "unknown",
            user_agent=request.headers.get("user-agent", "unknown")
        )
        
        return WorkflowAnalysisResponse(**result)
        
    except Exception as e:
        logger.error(f"Workflow hatası: {str(e)}")
        
        # Hata durumunu da logla
        await log_api_usage(
            endpoint="/api/v1/workflow/complete-analysis",
            method="POST",
            status_code=500,
            response_time=0,
            user_ip=request.client.host if request.client else "unknown",
            user_agent=request.headers.get("user-agent", "unknown"),
            error_message=str(e)
        )
        
        raise HTTPException(status_code=500, detail=str(e))

