"""
Usage tracking middleware for API endpoints
"""
from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from .firestore_db import firestore_manager
from .security import verify_token
from loguru import logger
import time

async def check_usage_limits(request: Request, call_next):
    """Middleware to check usage limits for protected endpoints"""
    
    # Skip usage check for auth endpoints and health checks
    skip_paths = ['/api/v1/auth/', '/health', '/docs', '/openapi.json']
    if any(request.url.path.startswith(path) for path in skip_paths):
        response = await call_next(request)
        return response
    
    # Skip for non-search endpoints
    search_endpoints = ['/api/v1/ai/', '/api/v1/workflow/']
    if not any(request.url.path.startswith(path) for path in search_endpoints):
        response = await call_next(request)
        return response
    
    try:
        # Get user from authorization header
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            # If no auth, let the endpoint handle it
            response = await call_next(request)
            return response
        
        token = auth_header.split(' ')[1]
        user_data = verify_token(token)
        
        if not user_data or not user_data.user_id:
            response = await call_next(request)
            return response

        user_id = user_data.user_id
        
        # Check usage limits
        usage_check = await firestore_manager.check_user_search_limit(user_id)
        
        if not usage_check.get('can_search', False):
            reason = usage_check.get('reason', 'Usage limit exceeded')
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "detail": f"Arama limiti aşıldı: {reason}",
                    "error_code": "USAGE_LIMIT_EXCEEDED",
                    "reason": reason
                }
            )
        
        # Process the request
        start_time = time.time()
        response = await call_next(request)
        
        # If request was successful, increment usage
        if response.status_code == 200:
            await firestore_manager.increment_user_search_usage(user_id)
            
            # Log the usage
            processing_time = time.time() - start_time
            logger.info(f"API usage logged for user {user_id}: {request.url.path} - {processing_time:.2f}s")
        
        return response
        
    except Exception as e:
        logger.error(f"Usage middleware error: {e}")
        # If middleware fails, let the request continue
        response = await call_next(request)
        return response

async def get_user_usage_info(user_id: str) -> dict:
    """Get user's current usage information"""
    try:
        usage_stats = await firestore_manager.get_user_usage_stats(user_id)
        usage_check = await firestore_manager.check_user_search_limit(user_id)
        
        return {
            "usage_stats": usage_stats,
            "can_search": usage_check.get('can_search', False),
            "remaining_searches": usage_check.get('remaining_searches', 0),
            "plan": usage_check.get('plan', 'free')
        }
    except Exception as e:
        logger.error(f"Error getting user usage info: {e}")
        # Return default values if there's an error
        return {
            "usage_stats": {
                "subscription_plan": "trial",
                "is_trial_active": True,
                "trial_searches_used": 0,
                "trial_searches_limit": 5,
                "monthly_searches_used": 0,
                "monthly_search_limit": 5
            },
            "can_search": True,
            "remaining_searches": 5,
            "plan": "trial"
        }

