from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
from agentpress.thread_manager import ThreadManager
from services.supabase import DBConnection
from datetime import datetime, timezone
from dotenv import load_dotenv
from utils.config import config, EnvMode
import asyncio
from utils.logger import logger
import uuid
import time
from collections import OrderedDict

# Import the API modules
from agent import api as agent_api
from sandbox import api as sandbox_api
from services import billing as billing_api
from admin import api as admin_api
from admin import activate_ai as activate_ai_api

# Load environment variables (these will be available through config)
load_dotenv()

# Initialize managers
db = DBConnection()
thread_manager = None
instance_id = "single"

# Rate limiter state
ip_tracker = OrderedDict()
MAX_CONCURRENT_IPS = 25

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    global thread_manager
    logger.info(f"Starting up FastAPI application with instance ID: {instance_id} in {config.ENV_MODE.value} mode")
    
    try:
        # Initialize database
        await db.initialize()
        thread_manager = ThreadManager()
        
        # Initialize the agent API with shared resources
        agent_api.initialize(
            thread_manager,
            db,
            instance_id
        )
        
        # Initialize the sandbox API with shared resources
        sandbox_api.initialize(db)
        
        # Initialize Redis connection
        from services import redis
        try:
            await redis.initialize_async()
            logger.info("Redis connection initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Redis connection: {e}")
            logger.warning("Continuing without Redis - some features may be limited")
            # Continue without Redis - the application will handle Redis failures gracefully
            # Set a flag to indicate Redis is not available
            redis._initialized = False
            redis.client = None
        
        # Start background tasks
        asyncio.create_task(agent_api.restore_running_agent_runs())
        
        yield
        
        # Clean up agent resources
        logger.info("Cleaning up agent resources")
        await agent_api.cleanup()
        
        # Clean up Redis connection
        try:
            logger.info("Closing Redis connection")
            await redis.close()
            logger.info("Redis connection closed successfully")
        except Exception as e:
            logger.error(f"Error closing Redis connection: {e}")
        
        # Clean up database connection
        logger.info("Disconnecting from database")
        await db.disconnect()
    except Exception as e:
        logger.error(f"Error during application startup: {e}")
        raise

app = FastAPI(lifespan=lifespan)

@app.middleware("http")
async def custom_cors_middleware(request: Request, call_next):
    # Handle preflight requests
    if request.method == "OPTIONS":
        response = Response()
        response.headers["Access-Control-Allow-Origin"] = "*"
        response.headers["Access-Control-Allow-Methods"] = "*"
        response.headers["Access-Control-Allow-Headers"] = "*"
        response.headers["Access-Control-Max-Age"] = "86400"
        return response

    # Process the request
    try:
        response = await call_next(request)
        
        # Add CORS headers to all responses
        response.headers["Access-Control-Allow-Origin"] = "*"
        response.headers["Access-Control-Allow-Methods"] = "*"
        response.headers["Access-Control-Allow-Headers"] = "*"
        
        return response
    except Exception as e:
        logger.error(f"Request error: {str(e)}")
        raise

@app.middleware("http")
async def log_requests_middleware(request: Request, call_next):
    start_time = time.time()
    client_ip = request.client.host
    method = request.method
    url = str(request.url)
    path = request.url.path
    query_params = str(request.query_params)
    
    # Log the incoming request
    logger.info(f"Request started: {method} {path} from {client_ip} | Query: {query_params}")
    
    try:
        response = await call_next(request)
        process_time = time.time() - start_time
        logger.debug(f"Request completed: {method} {path} | Status: {response.status_code} | Time: {process_time:.2f}s")
        return response
    except Exception as e:
        process_time = time.time() - start_time
        logger.error(f"Request failed: {method} {path} | Error: {str(e)} | Time: {process_time:.2f}s")
        raise

# Middleware for AI access verification is disabled to prevent authentication issues
# The verification will be handled directly by the endpoints using the ai_access_required dependency

# Define allowed origins based on environment
# For now, allow all origins to troubleshoot CORS issues
allowed_origins = ["*"]

# Original configuration (commented out for now)
"""
allowed_origins = [
    "https://www.defom-ai.vercel.app", 
    "https://defom-ai.vercel.app",
    "https://defom-ai-git-main-kierankerluke.vercel.app",
    "https://defom-ai-kierankerluke.vercel.app"
]
"""

# Add staging-specific origins
if config.ENV_MODE == EnvMode.STAGING:
    allowed_origins.append("http://localhost:3000")
    
# Add local-specific origins
if config.ENV_MODE == EnvMode.LOCAL:
    allowed_origins.append("http://localhost:3000")

# For development, you might want to allow all origins
# Uncomment the next line if needed during development
# allowed_origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],  # Allow all methods
    allow_headers=["*"],  # Allow all headers
    expose_headers=["*"],  # Expose all headers
    max_age=86400,  # Cache preflight requests for 24 hours
)

# Include the agent router with a prefix
app.include_router(agent_api.router, prefix="/api")

# Include the sandbox router with a prefix
app.include_router(sandbox_api.router, prefix="/api")

# Include the billing router with a prefix
app.include_router(billing_api.router, prefix="/api")

# Include the admin router with a prefix
app.include_router(admin_api.router, prefix="/api")

# Include the activate_ai router with a prefix
app.include_router(activate_ai_api.router, prefix="/api")


@app.get("/api/health")
async def health_check():
    """Health check endpoint to verify API is working."""
    logger.info("Health check endpoint called")
    return {
        "status": "ok", 
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "instance_id": instance_id
    }

if __name__ == "__main__":
    import uvicorn
    
    workers = 2
    
    logger.info(f"Starting server on 0.0.0.0:8000 with {workers} workers")
    uvicorn.run(
        "api:app", 
        host="0.0.0.0", 
        port=8000,
        workers=workers,
        # reload=True
    )
