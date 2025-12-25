from mangum import Mangum  # ASGI adapter for serverless
from main import app

# Mangum adapts FastAPI to event format
lambda_handler = Mangum(app)

def handler(event, context):
    return lambda_handler(event, context)
