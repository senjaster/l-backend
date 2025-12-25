from mangum import Mangum  # ASGI adapter for serverless
from app.main import app

# Mangum adapts FastAPI to event format
# Configure Mangum with explicit lifespan handling for serverless
# Set lifespan="off" to disable FastAPI lifespan events in serverless environment
# This prevents connection pool initialization issues in Lambda
lambda_handler = Mangum(
    app,
    lifespan="off"  # Disable lifespan for serverless (connection pooling handled per invocation)
)

def handler(event, context):
    return lambda_handler(event, context)
