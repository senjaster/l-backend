"""FastAPI application entry point"""
from fastapi import FastAPI
from contextlib import asynccontextmanager
from app.database import init_db_pool, close_db_pool


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    # Startup
    await init_db_pool()
    yield
    # Shutdown
    await close_db_pool()


app = FastAPI(
    title="L-Inspector Backend API",
    version="1.0.0",
    description="REST API for L-Inspector mobile application",
    lifespan=lifespan
)


@app.get("/")
async def root():
    """Health check endpoint"""
    return {"status": "ok", "message": "L-Inspector Backend API"}


# Routers will be included here as they are implemented
# app.include_router(inspector.router)
# app.include_router(sticker_type.router)
# app.include_router(equipment_type.router)
# app.include_router(plant.router)
# app.include_router(equipment.router)
# app.include_router(inspection.router)
# app.include_router(image.router)
# app.include_router(log.router)