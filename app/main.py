# app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.api.routes import auth, opportunities
from app.db.mongodb import connect_db, close_db

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifecycle management for FastAPI app
    Runs on startup and shutdown
    """
    # Startup: Connect to MongoDB
    await connect_db()
    print("✅ Connected to MongoDB")
    
    yield
    
    # Shutdown: Close MongoDB connection
    await close_db()
    print("❌ Closed MongoDB connection")

# Initialize FastAPI app
app = FastAPI(
    title="Fortinet Salesforce API",
    description="API to check Salesforce opportunities using end-user credentials",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware - adjust origins for production
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Change to specific origins in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(auth.router)
app.include_router(opportunities.router)

# Health check endpoint
@app.get("/", tags=["health"])
async def root():
    return {
        "status": "healthy",
        "service": "Fortinet Salesforce API",
        "version": "1.0.0"
    }

@app.get("/health", tags=["health"])
async def health_check():
    return {"status": "ok"}