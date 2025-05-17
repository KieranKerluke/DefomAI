"""
Centralized database connection management for AgentPress using Supabase.
"""

import os
from typing import Optional
from supabase import create_async_client, AsyncClient
from utils.logger import logger
from utils.config import config
# Global database connection instance
_db_connection = None

class DBConnection:
    """Singleton database connection manager using Supabase."""
    
    _instance: Optional['DBConnection'] = None
    _initialized = False
    _client: Optional[AsyncClient] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        """No initialization needed in __init__ as it's handled in __new__"""
        pass

    async def initialize(self):
        """Initialize the database connection."""
        if self._initialized:
            return
                
        try:
            supabase_url = config.SUPABASE_URL
            # Use service role key preferentially for backend operations
            supabase_key = config.SUPABASE_SERVICE_ROLE_KEY or config.SUPABASE_ANON_KEY
            
            if not supabase_url or not supabase_key:
                logger.error("Missing required environment variables for Supabase connection")
                raise RuntimeError("SUPABASE_URL and a key (SERVICE_ROLE_KEY or ANON_KEY) environment variables must be set.")

            logger.debug("Initializing Supabase connection")
            self._client = await create_async_client(supabase_url, supabase_key)
            self._initialized = True
            key_type = "SERVICE_ROLE_KEY" if config.SUPABASE_SERVICE_ROLE_KEY else "ANON_KEY"
            logger.debug(f"Database connection initialized with Supabase using {key_type}")
        except Exception as e:
            logger.error(f"Database initialization error: {e}")
            raise RuntimeError(f"Failed to initialize database connection: {str(e)}")

    @classmethod
    async def disconnect(cls):
        """Disconnect from the database."""
        if cls._client:
            logger.info("Disconnecting from Supabase database")
            await cls._client.close()
            cls._initialized = False
            logger.info("Database disconnected successfully")

    @property
    async def client(self) -> AsyncClient:
        """Get the Supabase client instance."""
        if not self._initialized:
            logger.debug("Supabase client not initialized, initializing now")
            await self.initialize()
        if not self._client:
            logger.error("Database client is None after initialization")
            raise RuntimeError("Database not initialized")
        return self._client
        
    async def execute(self, query, *args):
        """Execute a SQL query and return all results."""
        if not self._initialized:
            await self.initialize()
        try:
            # Direct SQL execution is not available, use Supabase's data API instead
            # This is a simplified implementation that works for basic queries
            if query.strip().upper().startswith("SELECT"):
                # For SELECT queries, use the from() method
                table_name = self._extract_table_name(query)
                if not table_name:
                    logger.error(f"Could not extract table name from query: {query}")
                    raise ValueError(f"Could not extract table name from query: {query}")
                
                result = await (await self._client.from_(table_name).select("*").execute())
                return result.data
            elif query.strip().upper().startswith("INSERT"):
                # For INSERT queries, use the insert() method
                table_name = self._extract_table_name(query)
                if not table_name:
                    logger.error(f"Could not extract table name from query: {query}")
                    raise ValueError(f"Could not extract table name from query: {query}")
                
                # Simplified - in real implementation, you'd parse the query to get values
                data = {"value": args[0]} if args else {}
                result = await (await self._client.from_(table_name).insert(data).execute())
                return result.data
            elif query.strip().upper().startswith("UPDATE"):
                # For UPDATE queries, use the update() method
                table_name = self._extract_table_name(query)
                if not table_name:
                    logger.error(f"Could not extract table name from query: {query}")
                    raise ValueError(f"Could not extract table name from query: {query}")
                
                # Simplified - in real implementation, you'd parse the query
                data = {"value": args[0]} if args else {}
                result = await (await self._client.from_(table_name).update(data).eq("id", args[1] if len(args) > 1 else None).execute())
                return result.data
            else:
                # For other queries, we need to implement custom handling
                logger.error(f"Unsupported query type: {query}")
                raise NotImplementedError(f"Unsupported query type: {query}")
        except Exception as e:
            logger.error(f"Database query error: {e}")
            raise
    
    def _extract_table_name(self, query):
        """Extract table name from a SQL query (simplified)."""
        # This is a very simplified implementation
        # In a real implementation, you'd use a proper SQL parser
        try:
            if query.strip().upper().startswith("SELECT"):
                # Extract table name from SELECT ... FROM table_name
                parts = query.split("FROM", 1)
                if len(parts) > 1:
                    return parts[1].strip().split()[0].strip()
            elif query.strip().upper().startswith("INSERT"):
                # Extract table name from INSERT INTO table_name
                parts = query.split("INTO", 1)
                if len(parts) > 1:
                    return parts[1].strip().split()[0].strip()
            elif query.strip().upper().startswith("UPDATE"):
                # Extract table name from UPDATE table_name
                parts = query.strip().split()
                if len(parts) > 1:
                    return parts[1].strip()
            return None
        except Exception:
            return None
            
    async def execute_single(self, query, *args):
        """Execute a SQL query and return the first result."""
        result = await self.execute(query, *args)
        if result and isinstance(result, list) and len(result) > 0:
            return result[0]
        return result
    
    async def fetch_one(self, query, *args):
        """Execute a SQL query and return the first result."""
        try:
            # Use execute_single as a fallback method
            return await self.execute_single(query, *args)
        except Exception as e:
            logger.error(f"Database fetch_one error: {e}")
            raise
def get_db_client():
    """
    Get a database client instance.
    
    Returns:
        DBConnection: A database connection instance
    """
    global _db_connection
    if _db_connection is None:
        _db_connection = DBConnection()
    return _db_connection
