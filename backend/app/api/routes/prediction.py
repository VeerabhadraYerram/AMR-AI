from fastapi import APIRouter, HTTPException, UploadFile, File
from app.api.models import AnalysisRequest, AnalysisResponse
from app.services.gaara import GAARA
import logging

router = APIRouter()
logger = logging.getLogger(__name__)
gaara_service = GAARA()

from app.api.routes.maps import get_pathogen_counts

@router.post("/analyze", response_model=AnalysisResponse)
async def analyze_sample(request: AnalysisRequest):
    """
    Run GAARA analysis for a given antibiotic and gene profile.
    """
    try:
        result = gaara_service.predict_risk(request.antibiotic, request.gene_presence)
        if "error" in result:
             raise HTTPException(status_code=500, detail=result["error"])
        
        # Inject Isolate Counts
        counts = get_pathogen_counts()
        for p_data in result.get("pathogen_breakdown", []):
            p_name = p_data.get("name")
            # Map simplified pathogen names if needed, or rely on exact match
            # K. pneumoniae, E. coli, S. aureus are the keys in maps.py
            if p_name in counts:
                p_data["count"] = counts[p_name]
            else:
                p_data["count"] = 0 # Or leave as is if frontend handles 0
                
        return result
    except Exception as e:
        logger.error(f"Analysis failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

@router.post("/upload_fasta")
async def upload_fasta(file: UploadFile = File(...)):
    """
    Upload FASTA file for analysis.
    Current Status: Gene extraction module in validation phase.
    """
    lines = (await file.read()).decode("utf-8").splitlines()
    extracted_genes = {}
    
    # Simple heuristic to extract genes from headers
    # We look for known gene families/names in the FASTA headers
    target_genes = ["blaNDM", "blaCTX_M", "gyrA_D87N", "qnrS", "blaKPC", "blaOXA", "aac", "aad", "cat", "sul", "tet"]
    
    found_genes = []
    
    for line in lines:
        if line.startswith(">"):
            header = line.strip()
            header = line.strip()
            # Iterating target_genes for fuzzy matching
            # logic fix: Don't rely on 'gene.lower() in header' for the if/elif block
            
            # Explicit checks for key resistance families
            lower_header = header.lower()
            
            if "blandm" in lower_header: extracted_genes["blaNDM"] = 1
            if "blactx" in lower_header: extracted_genes["blaCTX_M"] = 1
            if "gyra" in lower_header and "d87n" in lower_header: extracted_genes["gyrA_D87N"] = 1
            if "qnrs" in lower_header: extracted_genes["qnrS"] = 1
            if "blakpc" in lower_header: extracted_genes["blaKPC"] = 1
            if "blaoxa" in lower_header: extracted_genes["blaOXA"] = 1
            if "mcr" in lower_header: extracted_genes["gene_mcr_1"] = 1 # Example mapping
            
            # Generic checks for others if not captured above
            for gene in target_genes:
                 # Skip if already found to avoid duplicates or overwrites
                 # Simple check:
                 if gene.lower() in lower_header:
                      # Avoid over-writing specific mappings if needed, 
                      # but for now, we just ensure we capture the presence.
                      # Ideally we map "tet" to "gene_tetA" etc, but without model schema, 
                      # we'll stick to the explicit map above for the Demo, and generic for others.
                      if gene not in extracted_genes: 
                           extracted_genes[gene] = 1
    
    # Ensure at least some genes are found for the demo
    if not extracted_genes:
         logger.warning("No genes extracted from FASTA. Using empty profile.")
    
    return {
        "filename": file.filename,
        "status": "success",
        "genes": extracted_genes,
        "message": f"Extracted {len(extracted_genes)} genes."
    }
