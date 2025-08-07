from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes import router
import uvicorn

# Create FastAPI app
app = FastAPI(
    title="WhatsApp Chat Analyzer API",
    description="""
    A comprehensive WhatsApp chat analysis API that provides insights into chat patterns, 
    user activity, and content analysis with visualizations.
    
    ## Features
    - Parse WhatsApp chat exports
    - Generate detailed statistics
    - User activity analysis
    - Content analysis (words, emojis)
    - Interactive visualizations
    """,
    version="1.0.0",
    contact={
        "name": "WhatsApp Chat Analyzer",
        "url": "https://github.com/yourusername/whatsapp-chat-analyzer",
    },
    license_info={
        "name": "MIT License",
        "url": "https://opensource.org/licenses/MIT",
    },
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this properly for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routes
app.include_router(router, prefix="/api/v1")

# Root endpoint
@app.get("/")
async def root():
    return {
        "message": "WhatsApp Chat Analyzer API",
        "version": "1.0.0",
        "docs": "/docs",
        "api_base": "/api/v1"
    }

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )