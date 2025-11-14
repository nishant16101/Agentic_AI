from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from .config import settings
from .api.routes import chat, auth # Import other route modules here
from .utils.logger import get_logger

logger = get_logger(__name__)

def create_app() -> FastAPI:
    # --- CHANGE START ---
    docs_url = f"{settings.API_V1_STR}/docs"
    redoc_url = f"{settings.API_V1_STR}/redoc"
    # --- CHANGE END ---
    
    app = FastAPI(
        title=settings.PROJECT_NAME,
        version=settings.PROJECT_VERSION,
        openapi_url=f"{settings.API_V1_STR}/openapi.json",
        
        # --- NEW PARAMETERS ADDED ---
        docs_url=docs_url,
        redoc_url=redoc_url,
        # ----------------------------
    )

    # CORS Middleware to allow frontend to communicate
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[settings.FRONTEND_URL], # Allow frontend host
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Include API Routers
    app.include_router(auth.router, prefix=f"{settings.API_V1_STR}/auth", tags=["Authentication"])
    app.include_router(chat.router, prefix=f"{settings.API_V1_STR}/chat", tags=["Chat & Agent"])
    # Include other routers: gmail, gdocs, calendar, etc.

    @app.get("/")
    def read_root():
        return {"message": "Agentic Google Workspace Backend is Running!"}
    
    # --- DIAGNOSTIC LOG UPDATED ---
    logger.info(f"Swagger Documentation (Docs) URL is: http://{settings.HOST}:{settings.PORT}{docs_url}")
    logger.info(f"ReDoc Documentation (Redoc) URL is: http://{settings.HOST}:{settings.PORT}{redoc_url}")
    # ----------------------------

    return app

app = create_app()

if __name__ == "__main__":
    # Ensure RELOAD is cast to boolean for Uvicorn
    should_reload = settings.RELOAD.lower() in ('true', '1', 't')
    
    logger.info(f"Server is launching at http://{settings.HOST}:{settings.PORT}")
    uvicorn.run(
        "main:app", 
        host=settings.HOST, 
        port=settings.PORT, 
        reload=should_reload
    )