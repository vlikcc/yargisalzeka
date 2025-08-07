from pydantic import BaseModel, Field, validator
from typing import List, Dict, Any, Optional
from .validators import InputValidator, ContentFilter

# AI Özellikleri için schema'lar
class KeywordExtractionRequest(BaseModel):
    case_text: str = Field(..., min_length=50, max_length=10000)
    
    @validator('case_text')
    def validate_case_text(cls, v):
        return InputValidator.validate_case_text(v)

class KeywordExtractionResponse(BaseModel):
    keywords: List[str]
    success: bool
    message: str

class DecisionAnalysisRequest(BaseModel):
    case_text: str = Field(..., min_length=50, max_length=10000)
    decision: Dict[str, Any]
    
    @validator('case_text')
    def validate_case_text(cls, v):
        return InputValidator.validate_case_text(v)
    
    @validator('decision')
    def validate_decision(cls, v):
        if not v:
            raise ValueError("Karar bilgisi boş olamaz")
        return v

class DecisionAnalysisResponse(BaseModel):
    score: int = Field(..., ge=0, le=100)  # 0-100 arası
    explanation: str
    key_similarities: List[str]
    success: bool

class PetitionGenerationRequest(BaseModel):
    case_text: str = Field(..., min_length=50, max_length=10000)
    relevant_decisions: List[Dict[str, Any]] = Field(..., min_items=1, max_items=10)
    
    @validator('case_text')
    def validate_case_text(cls, v):
        return InputValidator.validate_case_text(v)
    
    @validator('relevant_decisions')
    def validate_decisions(cls, v):
        if not v:
            raise ValueError("En az bir karar gerekli")
        return v

class PetitionGenerationResponse(BaseModel):
    petition_template: str
    success: bool
    message: str

class SmartSearchRequest(BaseModel):
    case_text: str = Field(..., min_length=50, max_length=10000)
    max_results: Optional[int] = Field(default=10, ge=1, le=100)
    
    @validator('case_text')
    def validate_case_text(cls, v):
        return InputValidator.validate_case_text(v)
    
    @validator('max_results')
    def validate_max_results(cls, v):
        return InputValidator.validate_max_results(v)

class SmartSearchResponse(BaseModel):
    keywords: List[str]
    decisions: List[Dict[str, Any]]
    success: bool
    message: str

# Workflow mikroservisleri için yeni schema'lar
class WorkflowAnalysisRequest(BaseModel):
    case_text: str = Field(..., min_length=50, max_length=10000)
    max_results: Optional[int] = Field(default=10, ge=1, le=50)
    include_petition: Optional[bool] = Field(default=False)
    
    @validator('case_text')
    def validate_case_text(cls, v):
        # İçerik kontrolü
        if not ContentFilter.check_content(v):
            raise ValueError("Uygunsuz içerik tespit edildi")
        return InputValidator.validate_case_text(v)
    
    @validator('max_results')
    def validate_max_results(cls, v):
        return InputValidator.validate_max_results(v)

class WorkflowAnalysisResponse(BaseModel):
    keywords: List[str]
    search_results: List[Dict[str, Any]]
    analyzed_results: List[Dict[str, Any]]
    petition_template: Optional[str] = None
    processing_time: float
    success: bool
    message: str
    
    class Config:
        # Response filtering için
        @staticmethod
        def schema_extra(schema: Dict[str, Any], model) -> None:
            # Hassas bilgileri schema'dan kaldır
            if 'properties' in schema:
                schema['properties'] = ContentFilter.filter_response(schema['properties'])