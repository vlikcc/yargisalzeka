import time
import uuid
from typing import Callable
from fastapi import Request, Response
from fastapi.routing import APIRoute
from starlette.middleware.base import BaseHTTPMiddleware
from loguru import logger
from .database import log_api_usage
from .config import settings


class TimingMiddleware(BaseHTTPMiddleware):
    """API çağrılarının süresini ölçen middleware"""
    
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        
        # Request ID oluştur
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        
        # Log request
        logger.info(
            f"Request started | ID: {request_id} | Method: {request.method} | Path: {request.url.path} | IP: {request.client.host if request.client else 'unknown'}"
        )
        
        # Process request
        response = await call_next(request)
        
        # Calculate duration
        duration = time.time() - start_time
        
        # Add headers
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Process-Time"] = str(duration)
        
        # Log response
        logger.info(
            f"Request completed | ID: {request_id} | Status: {response.status_code} | Duration: {duration:.3f}s"
        )
        
        # Log to database in production
        if settings.is_production:
            try:
                await log_api_usage(
                    endpoint=str(request.url.path),
                    method=request.method,
                    status_code=response.status_code,
                    response_time=duration,
                    user_ip=request.client.host if request.client else "unknown",
                    user_agent=request.headers.get("user-agent", "unknown"),
                    request_id=request_id
                )
            except Exception as e:
                logger.error(f"Failed to log API usage: {e}")
        
        return response


class ErrorHandlingMiddleware(BaseHTTPMiddleware):
    """Hataları yakalayan ve loglayan middleware"""
    
    async def dispatch(self, request: Request, call_next):
        try:
            response = await call_next(request)
            return response
        except Exception as e:
            request_id = getattr(request.state, "request_id", "unknown")
            logger.error(
                f"Unhandled exception | ID: {request_id} | Error: {str(e)} | Path: {request.url.path}",
                exc_info=True
            )
            
            # Return generic error response
            return Response(
                content=f"Internal server error. Request ID: {request_id}",
                status_code=500,
                headers={"X-Request-ID": request_id}
            )


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Güvenlik başlıklarını ekleyen middleware"""
    
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        
        # Security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        
        # HSTS header for production
        if settings.is_production:
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        
        return response


class MetricsRoute(APIRoute):
    """API endpoint metriklerini toplayan custom route class"""
    
    def get_route_handler(self) -> Callable:
        original_route_handler = super().get_route_handler()
        
        async def custom_route_handler(request: Request) -> Response:
            start_time = time.time()
            
            # Increment request counter
            endpoint = f"{request.method}:{request.url.path}"
            
            try:
                response: Response = await original_route_handler(request)
                duration = time.time() - start_time
                
                # Log metrics
                logger.debug(
                    f"Metrics | Endpoint: {endpoint} | Status: {response.status_code} | Duration: {duration:.3f}s"
                )
                
                return response
            except Exception as e:
                duration = time.time() - start_time
                logger.error(
                    f"Metrics | Endpoint: {endpoint} | Error: {str(e)} | Duration: {duration:.3f}s"
                )
                raise
        
        return custom_route_handler