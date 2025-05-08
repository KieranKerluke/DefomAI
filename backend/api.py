from fastapi import FastAPI, Request
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

# Import the agent API module
from agent import api as agent_api
from sandbox import api as sandbox_api
from services import billing as billing_api

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
        # Initialize database with timeout
        logger.info("Attempting to initialize database connection")
        try:
            # Use asyncio.wait_for to add a timeout
            await asyncio.wait_for(db.initialize(), timeout=10.0)
            logger.info("Database connection initialized successfully")
        except asyncio.TimeoutError:
            logger.error("Database initialization timed out after 10 seconds")
            # Continue without properly initialized database - this will likely cause errors
            # but at least the application will start and can report the issue
        except Exception as db_error:
            logger.error(f"Failed to initialize database: {db_error}")
            # Continue without database - the health endpoint will report the issue
        
        thread_manager = ThreadManager()
        
        # Initialize the agent API with shared resources
        logger.info("Initializing agent API")
        agent_api.initialize(
            thread_manager,
            db,
            instance_id
        )
        
        # Initialize the sandbox API with shared resources
        logger.info("Initializing sandbox API")
        sandbox_api.initialize(db)
        
        # Initialize Redis connection
        from services import redis
        logger.info("Attempting to initialize Redis connection")
        try:
            # Use asyncio.wait_for to add a timeout
            await asyncio.wait_for(redis.initialize_async(), timeout=5.0)
            logger.info("Redis connection initialized successfully")
        except asyncio.TimeoutError:
            logger.error("Redis initialization timed out after 5 seconds")
            # Continue without Redis
        except Exception as redis_error:
            logger.error(f"Failed to initialize Redis connection: {redis_error}")
            # Continue without Redis - the application will handle Redis failures gracefully
        
        # Start background tasks
        logger.info("Starting background tasks")
        try:
            asyncio.create_task(agent_api.restore_running_agent_runs())
        except Exception as task_error:
            logger.error(f"Failed to start background tasks: {task_error}")
            # Continue without background tasks
        
        logger.info("Application startup sequence completed")
        yield
        
        # Clean up agent resources
        logger.info("Cleaning up agent resources")
        try:
            await agent_api.cleanup()
        except Exception as cleanup_error:
            logger.error(f"Error during agent cleanup: {cleanup_error}")
        
        # Clean up Redis connection
        try:
            logger.info("Closing Redis connection")
            await redis.close()
            logger.info("Redis connection closed successfully")
        except Exception as redis_close_error:
            logger.error(f"Error closing Redis connection: {redis_close_error}")
        
        # Clean up database connection
        try:
            logger.info("Disconnecting from database")
            await db.disconnect()
        except Exception as db_close_error:
            logger.error(f"Error disconnecting from database: {db_close_error}")
    except Exception as e:
        logger.error(f"Critical error during application startup: {e}")
        # Log the full traceback for better debugging
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        # Still raise the exception to properly signal startup failure
        raise

app = FastAPI(lifespan=lifespan)

# No custom CORS middleware needed, using FastAPI's CORSMiddleware instead

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

# CORS configuration with specific origins
origins = [
    "http://localhost:3000",
    "https://localhost:3000",
    "https://defom-ai.vercel.app",
    "https://www.defom-ai.vercel.app",
    # Add any other frontend domains that need to access this API
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,  # Allow cookies to be sent with requests
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=["*"],  # Allow all headers
    max_age=86400,  # Cache preflight requests for 24 hours
)

# Include the agent router with a prefix
app.include_router(agent_api.router, prefix="/api")

# Include the sandbox router with a prefix
app.include_router(sandbox_api.router, prefix="/api")

# Include the billing router with a prefix
app.include_router(billing_api.router, prefix="/api")

# OPTIONS requests are handled by FastAPI's CORSMiddleware

@app.get("/api/cors-test")
async def cors_test():
    """Test endpoint to verify CORS configuration."""
    logger.info("CORS test endpoint called")
    return {"message": "CORS is working!", "timestamp": datetime.now(timezone.utc).isoformat()}

@app.get("/api/health")
async def health_check():
    """Health check endpoint to verify API is working."""
    logger.info("Health check endpoint called")
    
    # Check database connection
    db_status = "ok"
    db_error = None
    try:
        # Add a simple database check if possible
        # This is a placeholder - replace with an actual lightweight DB check
        db_status = "ok" if db._client else "not_initialized"
    except Exception as e:
        db_status = "error"
        db_error = str(e)
    
    # Check Redis connection
    redis_status = "ok"
    redis_error = None
    try:
        from services import redis
        # Add a simple Redis check if possible
        redis_status = "ok" if redis.is_connected() else "not_connected"
    except Exception as e:
        redis_status = "error"
        redis_error = str(e)
    
    # Return detailed health information
    return {
        "status": "ok", 
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "instance_id": instance_id,
        "environment": config.ENV_MODE.value,
        "components": {
            "database": {
                "status": db_status,
                "error": db_error
            },
            "redis": {
                "status": redis_status,
                "error": redis_error
            }
        }
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
        reload=True
    )