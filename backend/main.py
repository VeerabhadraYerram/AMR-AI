from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import prediction, maps
from app.core.loader import ModelLoader
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="AMR Intelligence Platform API",
    description="API for Gene-Attributable Antibiotic Risk Aggregation (GAARA)",
    version="1.0.0"
)

# CORS Configuration
origins = [
    "http://localhost:5173",
    "http://localhost:5174",
    "http://localhost:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Model Loader on startup
@app.on_event("startup")
async def startup_event():
    logger.info("Initializing Model Loader...")
    ModelLoader.get_instance().load_models()
    logger.info("Model Loader initialized successfully.")

# Include Routers
app.include_router(prediction.router, prefix="/api/v1/prediction", tags=["prediction"])
app.include_router(maps.router, prefix="/api/v1/maps", tags=["maps"])

@app.get("/health")
def health_check():
    return {"status": "healthy", "version": "1.0.0"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
