from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime

class TermResponse(BaseModel):
    term: str
    en_summary: str
    en_url: str
    zh_summary: str
    zh_url: str
    translations: Optional[Dict[str, Dict[str, str]]] = None

class BatchTaskCreate(BaseModel):
    terms: List[str]
    crawl_interval: int = 3
    max_depth: int = 1
    max_terms_per_layer: int = 10
    target_languages: List[str] = ['en', 'zh']  # Default to English and Chinese

class BatchTaskResponse(BaseModel):
    task_id: int
    total_terms: int
    message: str

class TaskStatus(BaseModel):
    task_id: int
    status: str
    total_terms: int
    completed_terms: int
    failed_terms: int
    progress_percent: float
    max_depth: int = 1
    target_languages: List[str] = ['en', 'zh']
    created_at: str
    updated_at: str

class Association(BaseModel):
    target_term: str
    association_type: str
    weight: float

class TermDetail(BaseModel):
    id: int
    task_id: int
    term: str
    status: str
    en_summary: Optional[str] = None
    en_url: Optional[str] = None
    zh_summary: Optional[str] = None
    zh_url: Optional[str] = None
    translations: Optional[Dict[str, Dict[str, str]]] = None
    error_message: Optional[str] = None
    depth_level: int = 0
    source_term_id: Optional[int] = None
    created_at: str
    updated_at: str

class TaskListItem(BaseModel):
    id: int
    status: str
    total_terms: int
    completed_terms: int
    failed_terms: int
    target_languages: Optional[str] = 'en,zh'
    created_at: str

