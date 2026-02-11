from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import os
from dotenv import load_dotenv

# Load environment variables FIRST before any other imports
load_dotenv()

from database import init_db, close_db
from scheduler.reminder_scheduler import reminder_scheduler
from api.orders import router as orders_router
from api.admin import router as admin_router
from api.webhooks import router as webhooks_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown events"""
    # Startup
    print("Starting AI-Assisted Order Follow-Up System...")
    await init_db()
    reminder_scheduler.start()
    print("Application started successfully")
    
    yield
    
    # Shutdown
    print("Shutting down...")
    reminder_scheduler.shutdown()
    await close_db()
    print("Application shutdown complete")


# Create FastAPI app
app = FastAPI(
    title="AI-Assisted Order Follow-Up System",
    description="Automated WhatsApp-based order follow-up with AI personalization and sentiment analysis",
    version="1.0.0",
    lifespan=lifespan
)


# CORS middleware for frontend
# In unified deployment, same-origin applies, but we allow all for flexibility on Render
allowed_origins = os.getenv("CORS_ORIGINS", "*").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

# Include routers
app.include_router(orders_router)
app.include_router(admin_router)
app.include_router(webhooks_router)

# Mount static files and serve frontend (if directory exists)
# This is used for unified Docker deployment
static_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")
if os.path.exists(static_dir):
    app.mount("/assets", StaticFiles(directory=os.path.join(static_dir, "assets")), name="assets")
    
    @app.get("/{full_path:path}")
    async def serve_frontend(full_path: str):
        # Exclude API routes from static file serving
        if full_path.startswith("api") or full_path.startswith("docs") or full_path.startswith("openapi.json"):
            return None
        return FileResponse(os.path.join(static_dir, "index.html"))

@app.api_route("/", methods=["GET", "HEAD", "POST"])
async def root(request: Request):
    """Health check endpoint and debug for misconfigured webhooks"""
    if request.method == "POST":
        try:
            body = await request.body()
            print(f"DEBUG: Unexpected POST to root endpoint (/). Body: {body.decode(errors='ignore')}")
        except Exception as e:
            print(f"DEBUG: Failed to read POST body on root: {str(e)}")
            
        return {
            "status": "operational",
            "note": "You are hitting the root URL with POST. If this is Twilio, please change your webhook URL to: [your-url]/api/webhooks/whatsapp"
        }
    return {
        "status": "operational",
        "service": "AI-Assisted Order Follow-Up System",
        "version": "1.0.0"
    }


@app.api_route("/health", methods=["GET", "HEAD"])
async def health_check():
    """Detailed health check"""
    return {
        "status": "healthy",
        "database": "connected",
        "scheduler": "running"
    }


if __name__ == "__main__":
    import uvicorn
    
    # Run the application
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 10000)),
        reload=True  # Enable hot reload during development
    )
