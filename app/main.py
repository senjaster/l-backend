"""FastAPI application entry point"""

import asyncpg
import psycopg2
import logging

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi_bgtasks_dashboard import mount_bg_tasks_dashboard

from contextlib import asynccontextmanager
from app.database import init_db_pool, close_db_pool
from app.exceptions import (
    asyncpg_exception_handler,
    psycopg2_exception_handler,
    validation_exception_handler,
)
from app.middleware.auth import AuthMiddleware
from app.logging_config import setup_logging
from app.config import settings

from app.services.s3_connection import S3ConnectionManager
from app.services.s3_objects_service import S3ObjectService
from app.services.s3_queue_service import S3QueueService

from app.routers import (
    auth,
    inspector,
    image,
    log,
    sticker_type,
    equipment_type,
    facility_template,
    defect_type,
    plant,
    equipment,
    inspection,
    defect,
    work_log
)


# Initialize logging
setup_logging(log_level=settings.log_level, enable_json=settings.log_json) # DEV: log_level="DEBUG", enable_json=False
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    global s3_objects_service, s3_queue_service, connection_manager
    
    connection_manager = None
    
    try:
        # Startup
        logger.info("Initializing S3 services...")
        
        connection_manager = S3ConnectionManager()
        await connection_manager.initialize()
        logger.info("S3/SQS connection manager initialized successfully")
        
        
        s3_objects_service = S3ObjectService(connection_manager)
        s3_queue_service = S3QueueService(connection_manager)
        
        app.state.connection_manager = connection_manager
        app.state.s3_objects_service = s3_objects_service
        app.state.s3_queue_service = s3_queue_service
        
        logger.info("S3 services initialized successfully")
        
        await init_db_pool()
        logger.info("Database pool initialized")
        
        logger.info("Application started successfully")
        
        yield
        
    except Exception as e:
        logger.error(f"Error during startup: {e}")
        raise
    
    finally:
        logger.info("Shutting down application...")
        
        if connection_manager:
            try:
                await connection_manager.close()
                logger.info("S3/SQS connection manager closed successfully")
            except Exception as e:
                logger.error(f"Error closing S3/SQS connection manager: {e}")
        
        try:
            await close_db_pool()
            logger.info("Database pool closed successfully")
        except Exception as e:
            logger.error(f"Error closing database pool: {e}")
        
        logger.info("Application shutdown complete")


app = FastAPI(
    title="L-Inspector Backend API",
    version="1.0.0",
    description="REST API for L-Inspector mobile application",
    lifespan=lifespan,
    swagger_ui_parameters={"persistAuthorization": True},
)

# Configure OpenAPI security scheme for Swagger UI
app.openapi_schema = None  # Reset to regenerate with security scheme

mount_bg_tasks_dashboard(app=app)



def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema

    from fastapi.openapi.utils import get_openapi

    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )

    # Add security schemes - support both Authorization header and X-Auth-Token
    openapi_schema["components"]["securitySchemes"] = {
        "HTTPBearer": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
            "description": "Enter your JWT token (standard Authorization header - may not work in Yandex Cloud)",
        },
        "X-Auth-Token": {
            "type": "apiKey",
            "in": "header",
            "name": "X-Auth-Token",
            "description": "Enter 'Bearer <token>' or just '<token>' (works in Yandex Cloud where Authorization header is stripped)",
        }
    }

    # Apply security globally to all operations except public paths
    public_paths = {"/", "/auth/login", "/auth/refresh"}
    for path, path_item in openapi_schema.get("paths", {}).items():
        # Skip public paths
        if path in public_paths:
            continue

        # Apply security to all methods in this path
        # Allow either HTTPBearer OR X-Auth-Token
        for method in path_item.values():
            if isinstance(method, dict) and "security" not in method:
                method["security"] = [
                    {"HTTPBearer": []},
                    {"X-Auth-Token": []}
                ]

    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = custom_openapi

# Register exception handlers for both database drivers
app.add_exception_handler(asyncpg.PostgresError, asyncpg_exception_handler)
app.add_exception_handler(psycopg2.Error, psycopg2_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)


# Register authentication middleware (applies to all routes except /auth)
app.add_middleware(AuthMiddleware)

@app.get("/")
async def root():
    """Health check endpoint"""
    return {"status": "ok", "message": "L-Inspector Backend API"}


app.include_router(auth.router)
app.include_router(inspector.router)
app.include_router(image.router)
app.include_router(log.router)
app.include_router(sticker_type.router)
app.include_router(equipment_type.router)
app.include_router(facility_template.router)
app.include_router(defect_type.router)
app.include_router(plant.router)
app.include_router(equipment.router)
app.include_router(inspection.router)
app.include_router(defect.router)
app.include_router(work_log.router)
