# firestore_db.py - Google Cloud Firestore integration
import os
import time
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from google.cloud import firestore
from google.cloud.firestore import DocumentReference
from loguru import logger
from pydantic import BaseModel

class FirestoreManager:
    """Google Cloud Firestore database manager"""
    
    def __init__(self):
        self.client = None
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize Firestore client"""
        try:
            # Initialize Firestore client
            # In Cloud Run, credentials are automatically provided
            self.client = firestore.Client()
            logger.info("Firestore client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Firestore client: {e}")
            self.client = None
    
    def is_connected(self) -> bool:
        """Check if Firestore is connected"""
        try:
            if not self.client:
                return False
            
            # Try to read a test document
            test_ref = self.client.collection('_health_check').document('test')
            test_ref.get()
            return True
        except Exception as e:
            logger.error(f"Firestore connection check failed: {e}")
            return False
    
    # User Management
    async def create_user(self, email: str, hashed_password: str, full_name: str) -> str:
        """Create a new user in Firestore"""
        try:
            user_ref = self.client.collection('users').document()
            user_data = {
                'email': email,
                'hashed_password': hashed_password,
                'full_name': full_name,
                'subscription_plan': 'free',
                'created_at': firestore.SERVER_TIMESTAMP,
                'updated_at': firestore.SERVER_TIMESTAMP,
                'is_active': True
            }
            user_ref.set(user_data)
            logger.info(f"User created with ID: {user_ref.id}")
            return user_ref.id
        except Exception as e:
            logger.error(f"Error creating user: {e}")
            raise

    async def create_user_with_trial(self, email: str, hashed_password: str, full_name: str) -> str:
        """Create a new user with trial package in Firestore"""
        try:
            user_ref = self.client.collection('users').document()
            
            # Trial başlangıç ve bitiş tarihleri (3 gün)
            trial_start = datetime.utcnow()
            trial_end = trial_start + timedelta(days=3)
            
            user_data = {
                'email': email,
                'hashed_password': hashed_password,
                'full_name': full_name,
                'subscription_plan': 'trial',
                'created_at': firestore.SERVER_TIMESTAMP,
                'updated_at': firestore.SERVER_TIMESTAMP,
                'is_active': True,
                # Trial package fields
                'trial_start_date': trial_start,
                'trial_end_date': trial_end,
                'trial_searches_limit': 5,
                'trial_searches_used': 0,
                'is_trial_active': True,
                'monthly_search_limit': 5,
                'monthly_searches_used': 0,
                'last_search_reset': trial_start
            }
            user_ref.set(user_data)
            logger.info(f"User with trial package created with ID: {user_ref.id}")
            return user_ref.id
        except Exception as e:
            logger.error(f"Error creating user with trial: {e}")
            raise
    
    async def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """Get user by email"""
        try:
            users_ref = self.client.collection('users')
            query = users_ref.where('email', '==', email).limit(1)
            docs = query.stream()
            
            for doc in docs:
                user_data = doc.to_dict()
                user_data['id'] = doc.id
                return user_data
            
            return None
        except Exception as e:
            logger.error(f"Error getting user by email: {e}")
            return None
    
    async def get_user_by_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user by ID"""
        try:
            user_ref = self.client.collection('users').document(user_id)
            doc = user_ref.get()
            
            if doc.exists:
                user_data = doc.to_dict()
                user_data['id'] = doc.id
                return user_data
            
            return None
        except Exception as e:
            logger.error(f"Error getting user by ID: {e}")
            return None
    
    async def update_user(self, user_id: str, update_data: Dict[str, Any]) -> bool:
        """Update user data"""
        try:
            user_ref = self.client.collection('users').document(user_id)
            update_data['updated_at'] = firestore.SERVER_TIMESTAMP
            user_ref.update(update_data)
            logger.info(f"User {user_id} updated successfully")
            return True
        except Exception as e:
            logger.error(f"Error updating user {user_id}: {e}")
            return False
    
    # API Usage Tracking
    async def log_api_usage(self, user_id: str, endpoint: str, method: str, 
                          ip_address: str, status_code: int, 
                          response_time: float = None) -> bool:
        """Log API usage to Firestore"""
        try:
            usage_ref = self.client.collection('api_usage').document()
            usage_data = {
                'user_id': user_id,
                'endpoint': endpoint,
                'method': method,
                'ip_address': ip_address,
                'status_code': status_code,
                'response_time': response_time,
                'timestamp': firestore.SERVER_TIMESTAMP
            }
            usage_ref.set(usage_data)
            return True
        except Exception as e:
            logger.error(f"Error logging API usage: {e}")
            return False
    
    # Analysis Results
    async def save_analysis_result(self, user_id: str, analysis_data: Dict[str, Any]) -> str:
        """Save analysis result to Firestore"""
        try:
            result_ref = self.client.collection('analysis_results').document()
            analysis_data.update({
                'user_id': user_id,
                'created_at': firestore.SERVER_TIMESTAMP,
                'id': result_ref.id
            })
            result_ref.set(analysis_data)
            logger.info(f"Analysis result saved with ID: {result_ref.id}")
            return result_ref.id
        except Exception as e:
            logger.error(f"Error saving analysis result: {e}")
            raise
    
    async def get_user_analysis_results(self, user_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Get user's analysis results"""
        try:
            results_ref = self.client.collection('analysis_results')
            query = results_ref.where('user_id', '==', user_id) \
                              .order_by('created_at', direction=firestore.Query.DESCENDING) \
                              .limit(limit)
            
            docs = query.stream()
            results = []
            
            for doc in docs:
                result_data = doc.to_dict()
                result_data['id'] = doc.id
                results.append(result_data)
            
            return results
        except Exception as e:
            logger.error(f"Error getting user analysis results: {e}")
            return []
    
    # Caching
    async def get_cached_keywords(self, case_text_hash: str) -> Optional[List[str]]:
        """Get cached keywords for case text"""
        try:
            cache_ref = self.client.collection('keywords_cache').document(case_text_hash)
            doc = cache_ref.get()
            
            if doc.exists:
                cache_data = doc.to_dict()
                # Check if cache is still valid (24 hours)
                created_at = cache_data.get('created_at')
                if created_at and (datetime.now() - created_at.replace(tzinfo=None)) < timedelta(hours=24):
                    return cache_data.get('keywords', [])
            
            return None
        except Exception as e:
            logger.error(f"Error getting cached keywords: {e}")
            return None
    
    async def cache_keywords(self, case_text_hash: str, keywords: List[str]) -> bool:
        """Cache keywords for case text"""
        try:
            cache_ref = self.client.collection('keywords_cache').document(case_text_hash)
            cache_data = {
                'case_text_hash': case_text_hash,
                'keywords': keywords,
                'created_at': firestore.SERVER_TIMESTAMP
            }
            cache_ref.set(cache_data)
            return True
        except Exception as e:
            logger.error(f"Error caching keywords: {e}")
            return False
    
    async def get_cached_search_results(self, keywords_hash: str) -> Optional[List[Dict[str, Any]]]:
        """Get cached search results"""
        try:
            cache_ref = self.client.collection('search_cache').document(keywords_hash)
            doc = cache_ref.get()
            
            if doc.exists:
                cache_data = doc.to_dict()
                # Check if cache is still valid (1 hour)
                created_at = cache_data.get('created_at')
                if created_at and (datetime.now() - created_at.replace(tzinfo=None)) < timedelta(hours=1):
                    return cache_data.get('results', [])
            
            return None
        except Exception as e:
            logger.error(f"Error getting cached search results: {e}")
            return None
    
    async def cache_search_results(self, keywords_hash: str, results: List[Dict[str, Any]]) -> bool:
        """Cache search results"""
        try:
            cache_ref = self.client.collection('search_cache').document(keywords_hash)
            cache_data = {
                'keywords_hash': keywords_hash,
                'results': results,
                'result_count': len(results),
                'created_at': firestore.SERVER_TIMESTAMP
            }
            cache_ref.set(cache_data)
            return True
        except Exception as e:
            logger.error(f"Error caching search results: {e}")
            return False
    
    # System Logs
    async def log_system_event(self, event_type: str, event_data: Dict[str, Any]) -> bool:
        """Log system events"""
        try:
            log_ref = self.client.collection('system_logs').document()
            log_data = {
                'event_type': event_type,
                'event_data': event_data,
                'timestamp': firestore.SERVER_TIMESTAMP
            }
            log_ref.set(log_data)
            return True
        except Exception as e:
            logger.error(f"Error logging system event: {e}")
            return False
    
    # Statistics
    async def get_user_stats(self, user_id: str) -> Dict[str, Any]:
        """Get user statistics"""
        try:
            # Get API usage count for last 30 days
            thirty_days_ago = datetime.now() - timedelta(days=30)
            usage_ref = self.client.collection('api_usage')
            usage_query = usage_ref.where('user_id', '==', user_id) \
                                 .where('timestamp', '>=', thirty_days_ago)
            
            usage_docs = usage_query.stream()
            api_calls = sum(1 for _ in usage_docs)
            
            # Get analysis results count
            results_ref = self.client.collection('analysis_results')
            results_query = results_ref.where('user_id', '==', user_id)
            results_docs = results_query.stream()
            analysis_count = sum(1 for _ in results_docs)
            
            return {
                'api_calls_30_days': api_calls,
                'total_analyses': analysis_count,
                'last_activity': datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Error getting user stats: {e}")
            return {}
    
    # Health and Monitoring
    async def health_check(self) -> Dict[str, Any]:
        """Perform Firestore health check"""
        try:
            start_time = time.time()
            
            # Test write
            test_ref = self.client.collection('_health_check').document('test')
            test_ref.set({'timestamp': firestore.SERVER_TIMESTAMP})
            
            # Test read
            doc = test_ref.get()
            
            # Test delete
            test_ref.delete()
            
            response_time = (time.time() - start_time) * 1000
            
            return {
                'status': 'healthy',
                'response_time_ms': round(response_time, 2),
                'connected': True,
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            return {
                'status': 'unhealthy',
                'error': str(e),
                'connected': False,
                'timestamp': datetime.now().isoformat()
            }

    # Usage Tracking Methods
    async def check_user_search_limit(self, user_id: str) -> Dict[str, Any]:
        """Check if user can perform a search based on their limits"""
        try:
            user_data = await self.get_user_by_id(user_id)
            if not user_data:
                return {"can_search": False, "reason": "User not found"}
            
            current_time = datetime.utcnow()
            
            # Check if trial is active and not expired
            if user_data.get('subscription_plan') == 'trial':
                trial_end = user_data.get('trial_end_date')
                if trial_end and current_time > trial_end:
                    # Trial expired, deactivate it
                    await self.deactivate_trial(user_id)
                    return {"can_search": False, "reason": "Trial period expired"}
                
                trial_used = user_data.get('trial_searches_used', 0)
                trial_limit = user_data.get('trial_searches_limit', 5)
                
                if trial_used >= trial_limit:
                    return {"can_search": False, "reason": "Trial search limit reached"}
                
                return {
                    "can_search": True, 
                    "remaining_searches": trial_limit - trial_used,
                    "plan": "trial"
                }
            
            # Check monthly limits for other plans
            monthly_used = user_data.get('monthly_searches_used', 0)
            monthly_limit = user_data.get('monthly_search_limit', 0)
            
            if monthly_limit > 0 and monthly_used >= monthly_limit:
                return {"can_search": False, "reason": "Monthly search limit reached"}
            
            return {
                "can_search": True,
                "remaining_searches": monthly_limit - monthly_used if monthly_limit > 0 else "unlimited",
                "plan": user_data.get('subscription_plan', 'free')
            }
            
        except Exception as e:
            logger.error(f"Error checking user search limit: {e}")
            return {"can_search": False, "reason": "System error"}

    async def increment_user_search_usage(self, user_id: str) -> bool:
        """Increment user's search usage count"""
        try:
            user_ref = self.client.collection('users').document(user_id)
            user_data = await self.get_user_by_id(user_id)
            
            if not user_data:
                return False
            
            # Update trial usage if on trial
            if user_data.get('subscription_plan') == 'trial':
                trial_used = user_data.get('trial_searches_used', 0)
                user_ref.update({
                    'trial_searches_used': trial_used + 1,
                    'updated_at': firestore.SERVER_TIMESTAMP
                })
            else:
                # Update monthly usage
                monthly_used = user_data.get('monthly_searches_used', 0)
                user_ref.update({
                    'monthly_searches_used': monthly_used + 1,
                    'updated_at': firestore.SERVER_TIMESTAMP
                })
            
            logger.info(f"Search usage incremented for user: {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error incrementing search usage: {e}")
            return False

    async def deactivate_trial(self, user_id: str) -> bool:
        """Deactivate trial for a user"""
        try:
            user_ref = self.client.collection('users').document(user_id)
            user_ref.update({
                'is_trial_active': False,
                'subscription_plan': 'free',
                'updated_at': firestore.SERVER_TIMESTAMP
            })
            logger.info(f"Trial deactivated for user: {user_id}")
            return True
        except Exception as e:
            logger.error(f"Error deactivating trial: {e}")
            return False

    async def get_user_usage_stats(self, user_id: str) -> Dict[str, Any]:
        """Get user's usage statistics"""
        try:
            user_data = await self.get_user_by_id(user_id)
            if not user_data:
                return {}
            
            stats = {
                "subscription_plan": user_data.get('subscription_plan', 'free'),
                "is_trial_active": user_data.get('is_trial_active', False),
                "monthly_searches_used": user_data.get('monthly_searches_used', 0),
                "monthly_search_limit": user_data.get('monthly_search_limit', 0)
            }
            
            # Add trial specific stats if applicable
            if user_data.get('subscription_plan') == 'trial':
                stats.update({
                    "trial_searches_used": user_data.get('trial_searches_used', 0),
                    "trial_searches_limit": user_data.get('trial_searches_limit', 5),
                    "trial_start_date": user_data.get('trial_start_date'),
                    "trial_end_date": user_data.get('trial_end_date')
                })
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting user usage stats: {e}")
            return {}

# Global Firestore manager instance
firestore_manager = FirestoreManager()

# Convenience functions for backward compatibility
async def init_firestore_db() -> bool:
    """Initialize Firestore database"""
    return firestore_manager.is_connected()

async def close_firestore_database():
    """Close Firestore database connection"""
    # Firestore client doesn't need explicit closing
    logger.info("Firestore database connection closed")

async def get_firestore_health() -> Dict[str, Any]:
    """Get Firestore health status"""
    return await firestore_manager.health_check()

async def log_api_usage(user_id: str, endpoint: str, request_data: Dict[str, Any], ip_address: str) -> bool:
    """Log API usage to Firestore"""
    return await firestore_manager.log_api_usage(
        user_id=user_id,
        endpoint=endpoint,
        method="POST",
        ip_address=ip_address,
        status_code=200,
        response_time=None
    )
