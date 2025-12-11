from pydantic import BaseModel
from typing import Dict, Any

class OptimizeResponse(BaseModel):
    job_id: str
    original_size_mb: float
    final_size_mb: float
    compression_ratio: float
    config_used: Dict[str, Any]
    explanation: str
