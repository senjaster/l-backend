"""FastAPI application entry point"""
from fastapi import FastAPI
from contextlib import asynccontextmanager
import asyncpg
from app.database import init_db_pool, close_db_pool
from app.exceptions import asyncpg_exception_handler


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

# Register exception handlers
app.add_exception_handler(asyncpg.PostgresError, asyncpg_exception_handler)


@app.get("/")
async def root():
    """Health check endpoint"""
    return {"status": "ok", "message": "L-Inspector Backend API"}


# Include routers
from app.routers import inspector, image, log, sticker_type, equipment_type, plant

app.include_router(inspector.router)
app.include_router(image.router)
app.include_router(log.router)
app.include_router(sticker_type.router)
app.include_router(equipment_type.router)
app.include_router(plant.router)

# Additional routers will be included as they are implemented
# app.include_router(equipment.router)
# app.include_router(inspection.router)