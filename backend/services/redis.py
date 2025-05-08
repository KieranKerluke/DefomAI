import redis.asyncio as redis
import os
from dotenv import load_dotenv
import asyncio
from utils.logger import logger
from typing import List, Any, Optional
import time

# Redis client
client = None
_initialized = False
_init_lock = asyncio.Lock()
_last_connection_attempt = 0
_connection_retry_delay = 5  # seconds

# Constants
REDIS_KEY_TTL = 3600 * 24  # 24 hour TTL as safety mechanism
MAX_RECONNECT_ATTEMPTS = 3


def initialize():
    """Initialize Redis connection using environment variables."""
    global client

    # Load environment variables if not already loaded
    load_dotenv()

    # Get Redis configuration
    redis_host = os.getenv('REDIS_HOST', 'redis')
    redis_port = int(os.getenv('REDIS_PORT', 6379))
    redis_password = os.getenv('REDIS_PASSWORD', '')
    # Convert string 'True'/'False' to boolean
    redis_ssl_str = os.getenv('REDIS_SSL', 'False')
    redis_ssl = redis_ssl_str.lower() == 'true'

    logger.info(f"Initializing Redis connection to {redis_host}:{redis_port}")

    # Create Redis client with basic configuration
    client = redis.Redis(
        host=redis_host,
        port=redis_port,
        password=redis_password,
        ssl=redis_ssl,
        decode_responses=True,
        socket_timeout=5.0,
        socket_connect_timeout=5.0,
        retry_on_timeout=True,
        health_check_interval=30
    )

    return client


async def initialize_async():
    """Initialize Redis connection asynchronously."""
    global client, _initialized, _last_connection_attempt

    # Rate limit connection attempts
    current_time = time.time()
    if current_time - _last_connection_attempt < _connection_retry_delay:
        if client is not None and _initialized:
            return client
        logger.warning(f"Rate limiting Redis connection attempts. Waiting {_connection_retry_delay} seconds.")
        await asyncio.sleep(0.1)  # Small delay to prevent tight loops
        return None

    _last_connection_attempt = current_time

    async with _init_lock:
        if not _initialized:
            logger.info("Initializing Redis connection")
            initialize()

            try:
                await client.ping()
                logger.info("Successfully connected to Redis")
                _initialized = True
            except Exception as e:
                logger.error(f"Failed to connect to Redis: {e}")
                client = None
                # Don't raise the exception, just return None
                return None

    return client


async def close():
    """Close Redis connection."""
    global client, _initialized
    if client:
        logger.info("Closing Redis connection")
        await client.aclose()
        client = None
        _initialized = False
        logger.info("Redis connection closed")


async def get_client():
    """Get the Redis client, initializing if necessary."""
    global client, _initialized
    
    # If we already have a working client, return it
    if client is not None and _initialized:
        try:
            # Quick check to see if connection is still alive
            await client.ping()
            return client
        except Exception as e:
            logger.warning(f"Redis connection check failed: {e}")
            _initialized = False
    
    # Try to initialize or reconnect
    for attempt in range(MAX_RECONNECT_ATTEMPTS):
        try:
            redis_client = await initialize_async()
            if redis_client is not None:
                return redis_client
            
            # If initialization returned None, wait before retrying
            await asyncio.sleep(_connection_retry_delay)
        except Exception as e:
            logger.error(f"Redis reconnection attempt {attempt+1}/{MAX_RECONNECT_ATTEMPTS} failed: {e}")
            await asyncio.sleep(_connection_retry_delay)
    
    # If we get here, all reconnection attempts failed
    logger.error(f"All Redis reconnection attempts failed after {MAX_RECONNECT_ATTEMPTS} tries")
    return None


# Basic Redis operations
async def set(key: str, value: str, ex: int = None):
    """Set a Redis key."""
    redis_client = await get_client()
    if redis_client is None:
        logger.warning(f"Cannot set Redis key {key}: client is None")
        return False
    try:
        return await redis_client.set(key, value, ex=ex)
    except Exception as e:
        logger.error(f"Error setting Redis key {key}: {e}")
        return False


async def get(key: str, default: str = None):
    """Get a Redis key."""
    redis_client = await get_client()
    if redis_client is None:
        logger.warning(f"Cannot get Redis key {key}: client is None")
        return default
    try:
        result = await redis_client.get(key)
        return result if result is not None else default
    except Exception as e:
        logger.error(f"Error getting Redis key {key}: {e}")
        return default


async def delete(key: str):
    """Delete a Redis key."""
    redis_client = await get_client()
    if redis_client is None:
        logger.warning(f"Cannot delete Redis key {key}: client is None")
        return 0
    try:
        return await redis_client.delete(key)
    except Exception as e:
        logger.error(f"Error deleting Redis key {key}: {e}")
        return 0


async def publish(channel: str, message: str):
    """Publish a message to a Redis channel."""
    redis_client = await get_client()
    if redis_client is None:
        logger.warning(f"Cannot publish to Redis channel {channel}: client is None")
        return 0
    try:
        return await redis_client.publish(channel, message)
    except Exception as e:
        logger.error(f"Error publishing to Redis channel {channel}: {e}")
        return 0


async def create_pubsub():
    """Create a Redis pubsub object."""
    redis_client = await get_client()
    if redis_client is None:
        logger.warning("Cannot create Redis pubsub: client is None")
        return None
    try:
        return redis_client.pubsub()
    except Exception as e:
        logger.error(f"Error creating Redis pubsub: {e}")
        return None


# List operations
async def rpush(key: str, *values: Any):
    """Append one or more values to a list."""
    redis_client = await get_client()
    if redis_client is None:
        logger.warning(f"Cannot rpush to Redis list {key}: client is None")
        return 0
    try:
        return await redis_client.rpush(key, *values)
    except Exception as e:
        logger.error(f"Error rpushing to Redis list {key}: {e}")
        return 0


async def lrange(key: str, start: int, end: int):
    """Get a range of elements from a list."""
    redis_client = await get_client()
    if redis_client is None:
        logger.warning(f"Cannot lrange Redis list {key}: client is None")
        return []
    try:
        return await redis_client.lrange(key, start, end)
    except Exception as e:
        logger.error(f"Error lranging Redis list {key}: {e}")
        return []


async def llen(key: str):
    """Get the length of a list."""
    redis_client = await get_client()
    if redis_client is None:
        logger.warning(f"Cannot llen Redis list {key}: client is None")
        return 0
    try:
        return await redis_client.llen(key)
    except Exception as e:
        logger.error(f"Error getting llen of Redis list {key}: {e}")
        return 0


# Key management
async def expire(key: str, time: int):
    """Set a key's time to live in seconds."""
    redis_client = await get_client()
    if redis_client is None:
        logger.warning(f"Cannot expire Redis key {key}: client is None")
        return False
    try:
        return await redis_client.expire(key, time)
    except Exception as e:
        logger.error(f"Error expiring Redis key {key}: {e}")
        return False


async def keys(pattern: str):
    """Get keys matching a pattern."""
    redis_client = await get_client()
    if redis_client is None:
        logger.warning(f"Cannot get Redis keys matching {pattern}: client is None")
        return []
    try:
        return await redis_client.keys(pattern)
    except Exception as e:
        logger.error(f"Error getting Redis keys matching {pattern}: {e}")
        return []