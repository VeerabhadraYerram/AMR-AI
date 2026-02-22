from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any

class AnalysisRequest(BaseModel):
    antibiotic: str = Field(..., description="Name of the antibiotic to analyze")
    gene_presence: Dict[str, int] = Field(..., description="Dictionary of gene names and their presence (1) or absence (0)")

class PathogenResult(BaseModel):
    name: str
    risk: float
    risk_mass: Dict[str, Any]
    weight: float
    directions: Optional[Dict[str, str]] = None

class AnalysisResponse(BaseModel):
    overall_risk_score: float
    risk_category: str
    gene_drivers: Dict[str, Any]
    pathogen_breakdown: List[PathogenResult]

class MapDataPoint(BaseModel):
    region: str
    value: float
    metadata: Optional[Dict[str, Any]] = None

class MapResponse(BaseModel):
    map_type: str
    data: List[MapDataPoint]
    status: str
    message: Optional[str] = None
