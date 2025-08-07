import re
from typing import List, Dict, Any
from pydantic import validator, BaseModel
from fastapi import HTTPException
from loguru import logger


class InputValidator:
    """Input validation ve sanitization için yardımcı sınıf"""
    
    @staticmethod
    def sanitize_text(text: str, max_length: int = 10000) -> str:
        """
        Metni temizle ve güvenli hale getir
        """
        if not text:
            return ""
        
        # Uzunluk kontrolü
        if len(text) > max_length:
            raise HTTPException(
                status_code=400,
                detail=f"Metin çok uzun. Maksimum {max_length} karakter olabilir."
            )
        
        # Tehlikeli karakterleri temizle
        # SQL injection karakterleri
        text = re.sub(r"[';\"\\]", "", text)
        
        # XSS karakterleri
        text = re.sub(r"[<>]", "", text)
        
        # Control karakterleri temizle
        text = re.sub(r"[\x00-\x1f\x7f-\x9f]", "", text)
        
        # Birden fazla boşluğu tek boşluğa çevir
        text = re.sub(r"\s+", " ", text)
        
        return text.strip()
    
    @staticmethod
    def validate_keywords(keywords: List[str], max_keywords: int = 20) -> List[str]:
        """
        Anahtar kelimeleri validate et
        """
        if not keywords:
            raise HTTPException(
                status_code=400,
                detail="En az bir anahtar kelime gerekli"
            )
        
        if len(keywords) > max_keywords:
            raise HTTPException(
                status_code=400,
                detail=f"En fazla {max_keywords} anahtar kelime kullanabilirsiniz"
            )
        
        # Her anahtar kelimeyi temizle
        cleaned_keywords = []
        for keyword in keywords:
            if not keyword or not keyword.strip():
                continue
            
            # Anahtar kelime uzunluğu kontrolü
            if len(keyword) > 100:
                logger.warning(f"Çok uzun anahtar kelime atlandı: {keyword[:50]}...")
                continue
            
            # Temizle
            cleaned = InputValidator.sanitize_text(keyword, max_length=100)
            if cleaned:
                cleaned_keywords.append(cleaned)
        
        if not cleaned_keywords:
            raise HTTPException(
                status_code=400,
                detail="Geçerli anahtar kelime bulunamadı"
            )
        
        return cleaned_keywords
    
    @staticmethod
    def validate_case_text(text: str) -> str:
        """
        Olay metnini validate et
        """
        if not text or not text.strip():
            raise HTTPException(
                status_code=400,
                detail="Olay metni boş olamaz"
            )
        
        # Minimum uzunluk kontrolü
        if len(text.strip()) < 50:
            raise HTTPException(
                status_code=400,
                detail="Olay metni en az 50 karakter olmalıdır"
            )
        
        # Temizle ve döndür
        return InputValidator.sanitize_text(text, max_length=10000)
    
    @staticmethod
    def validate_decision_text(text: str) -> str:
        """
        Karar metnini validate et
        """
        if not text or not text.strip():
            raise HTTPException(
                status_code=400,
                detail="Karar metni boş olamaz"
            )
        
        # Temizle ve döndür
        return InputValidator.sanitize_text(text, max_length=50000)
    
    @staticmethod
    def validate_max_results(value: int) -> int:
        """
        Maksimum sonuç sayısını validate et
        """
        if value < 1:
            raise HTTPException(
                status_code=400,
                detail="Maksimum sonuç sayısı en az 1 olmalıdır"
            )
        
        if value > 100:
            raise HTTPException(
                status_code=400,
                detail="Maksimum sonuç sayısı 100'den fazla olamaz"
            )
        
        return value


class ContentFilter:
    """İçerik filtreleme için yardımcı sınıf"""
    
    # Yasaklı kelimeler listesi (örnek)
    BLOCKED_WORDS = [
        # Buraya yasaklı kelimeler eklenebilir
    ]
    
    @staticmethod
    def check_content(text: str) -> bool:
        """
        İçeriği kontrol et, uygunsuz içerik varsa False döndür
        """
        if not text:
            return True
        
        text_lower = text.lower()
        
        # Yasaklı kelime kontrolü
        for word in ContentFilter.BLOCKED_WORDS:
            if word.lower() in text_lower:
                logger.warning(f"Yasaklı kelime tespit edildi: {word}")
                return False
        
        # Spam kontrolü - aynı karakterin çok fazla tekrarı
        for char in set(text):
            if text.count(char) > len(text) * 0.5:  # %50'den fazla aynı karakter
                logger.warning("Spam içerik tespit edildi")
                return False
        
        return True
    
    @staticmethod
    def filter_response(data: Dict[str, Any]) -> Dict[str, Any]:
        """
        API response'unu filtrele, hassas bilgileri kaldır
        """
        # Hassas alanlar
        sensitive_fields = [
            "password", "token", "secret", "api_key", 
            "connection_string", "mongodb_connection"
        ]
        
        def clean_dict(d: Dict[str, Any]) -> Dict[str, Any]:
            cleaned = {}
            for key, value in d.items():
                # Hassas alan kontrolü
                if any(sensitive in key.lower() for sensitive in sensitive_fields):
                    cleaned[key] = "***REDACTED***"
                elif isinstance(value, dict):
                    cleaned[key] = clean_dict(value)
                elif isinstance(value, list):
                    cleaned[key] = [
                        clean_dict(item) if isinstance(item, dict) else item
                        for item in value
                    ]
                else:
                    cleaned[key] = value
            return cleaned
        
        return clean_dict(data)