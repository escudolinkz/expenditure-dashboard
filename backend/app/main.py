from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.database import init_db
from app.routes import (
    auth_router,
    statements_router,
    transactions_router,
    categories_router,
    analytics_router,
    merchant_rules_router,
)
from app.utils.seed_data import seed_default_categories


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan event handler for startup and shutdown"""
    # Startup
    print("Initializing database...")
    init_db()
    print("Seeding default categories...")
    seed_default_categories()
    yield
    # Shutdown
    print("Shutting down...")


app = FastAPI(
    title="Credit Card Analyzer API",
    description="API for analyzing credit card statements and tracking spending",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost"],  # Frontend URLs
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(auth_router, prefix="/api")
app.include_router(statements_router, prefix="/api")
app.include_router(transactions_router, prefix="/api")
app.include_router(categories_router, prefix="/api")
app.include_router(analytics_router, prefix="/api")
app.include_router(merchant_rules_router, prefix="/api")


@app.get("/")
def root():
    """Root endpoint"""
    return {
        "message": "Credit Card Analyzer API",
        "version": "1.0.0",
        "docs": "/docs",
    }


@app.get("/health")
def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}
