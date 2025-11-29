"""
Database utilities and helper functions.
"""
import time
from typing import Optional, Dict, Any, List
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorCollection
from pymongo.errors import PyMongoError, DuplicateKeyError, ConnectionFailure
from functools import wraps

from config import settings
from errors import DatabaseError
from logger import logger, log_database_operation

class DatabaseManager:
    """Manages database connections and operations."""
    
    def __init__(self):
        self.client: Optional[AsyncIOMotorClient] = None
        self.connected = False
    
    async def connect(self):
        """Establish database connection."""
        try:
            if not settings.MONGO_URI:
                raise ValueError("MONGO_URI not configured")
            
            self.client = AsyncIOMotorClient(
                settings.MONGO_URI,
                serverSelectionTimeoutMS=5000,
                connectTimeoutMS=5000,
                socketTimeoutMS=5000
            )

            await self.client.admin.command('ping')
            self.connected = True
            logger.info("✅ Database connected successfully")
            
        except Exception as e:
            logger.error(f"❌ Database connection failed: {str(e)}")
            raise DatabaseError(f"Failed to connect to database: {str(e)}")
    
    async def disconnect(self):
        """Close database connection."""
        if self.client:
            self.client.close()
            self.connected = False
            logger.info("🔌 Database connection closed")
    
    async def ping(self) -> bool:
        """Check if database connection is alive."""
        try:
            if self.client:
                await self.client.admin.command('ping')
                return True
            return False
        except Exception:
            return False

db_manager = DatabaseManager()

def with_retry(max_retries: int = 3, delay: float = 1.0):
    """
    Decorator to retry database operations on failure.
    
    Args:
        max_retries: Maximum number of retry attempts
        delay: Delay between retries in seconds
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(max_retries):
                try:
                    return await func(*args, **kwargs)
                
                except ConnectionFailure as e:
                    last_exception = e
                    if attempt < max_retries - 1:
                        logger.warning(
                            f"Database connection failed (attempt {attempt + 1}/{max_retries}). "
                            f"Retrying in {delay}s..."
                        )
                        time.sleep(delay)
                    else:
                        logger.error(f"Database operation failed after {max_retries} attempts")
                
                except Exception as e:

                    raise
            
            raise DatabaseError(f"Operation failed after {max_retries} retries: {last_exception}")
        
        return wrapper
    return decorator

def log_operation(operation_type: str):
    """
    Decorator to log database operations with timing.
    
    Args:
        operation_type: Type of operation (e.g., 'INSERT', 'UPDATE', 'FIND')
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            success = True
            
            try:
                result = await func(*args, **kwargs)
                return result
            
            except Exception as e:
                success = False
                raise
            
            finally:
                duration = time.time() - start_time
                collection_name = kwargs.get('collection', 'unknown')
                log_database_operation(operation_type, collection_name, duration, success)
        
        return wrapper
    return decorator

class DatabaseHelper:
    """Helper methods for common database operations."""
    
    @staticmethod
    @with_retry(max_retries=3)
    async def find_one(
        collection: AsyncIOMotorCollection,
        query: Dict[str, Any],
        projection: Optional[Dict[str, Any]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Find a single document with retry logic.
        
        Args:
            collection: MongoDB collection
            query: Query filter
            projection: Fields to include/exclude
        
        Returns:
            Document if found, None otherwise
        """
        try:
            return await collection.find_one(query, projection)
        except PyMongoError as e:
            logger.error(f"Database find_one error: {str(e)}")
            raise DatabaseError(f"Failed to find document: {str(e)}")
    
    @staticmethod
    @with_retry(max_retries=3)
    async def find_many(
        collection: AsyncIOMotorCollection,
        query: Dict[str, Any],
        projection: Optional[Dict[str, Any]] = None,
        sort: Optional[List[tuple]] = None,
        limit: Optional[int] = None,
        skip: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Find multiple documents with retry logic.
        
        Args:
            collection: MongoDB collection
            query: Query filter
            projection: Fields to include/exclude
            sort: Sort specification
            limit: Maximum number of documents
            skip: Number of documents to skip
        
        Returns:
            List of documents
        """
        try:
            cursor = collection.find(query, projection)
            
            if sort:
                cursor = cursor.sort(sort)
            
            if skip > 0:
                cursor = cursor.skip(skip)
            
            if limit:
                cursor = cursor.limit(limit)
            
            return await cursor.to_list(length=limit)
        
        except PyMongoError as e:
            logger.error(f"Database find_many error: {str(e)}")
            raise DatabaseError(f"Failed to find documents: {str(e)}")
    
    @staticmethod
    @with_retry(max_retries=3)
    async def insert_one(
        collection: AsyncIOMotorCollection,
        document: Dict[str, Any],
        add_timestamp: bool = True
    ) -> str:
        """
        Insert a single document with retry logic.
        
        Args:
            collection: MongoDB collection
            document: Document to insert
            add_timestamp: Whether to add created_at timestamp
        
        Returns:
            Inserted document ID as string
        """
        try:
            if add_timestamp:
                document['created_at'] = datetime.utcnow()
            
            result = await collection.insert_one(document)
            return str(result.inserted_id)
        
        except DuplicateKeyError as e:
            logger.warning(f"Duplicate key error: {str(e)}")
            raise DatabaseError("Resource already exists", details={"error": "duplicate_key"})
        
        except PyMongoError as e:
            logger.error(f"Database insert_one error: {str(e)}")
            raise DatabaseError(f"Failed to insert document: {str(e)}")
    
    @staticmethod
    @with_retry(max_retries=3)
    async def update_one(
        collection: AsyncIOMotorCollection,
        query: Dict[str, Any],
        update: Dict[str, Any],
        upsert: bool = False,
        add_timestamp: bool = True
    ) -> bool:
        """
        Update a single document with retry logic.
        
        Args:
            collection: MongoDB collection
            query: Query filter
            update: Update operations
            upsert: Create document if it doesn't exist
            add_timestamp: Whether to add updated_at timestamp
        
        Returns:
            True if document was modified, False otherwise
        """
        try:
            if add_timestamp:
                if '$set' not in update:
                    update['$set'] = {}
                update['$set']['updated_at'] = datetime.utcnow()
            
            result = await collection.update_one(query, update, upsert=upsert)
            return result.modified_count > 0 or (upsert and result.upserted_id is not None)
        
        except PyMongoError as e:
            logger.error(f"Database update_one error: {str(e)}")
            raise DatabaseError(f"Failed to update document: {str(e)}")
    
    @staticmethod
    @with_retry(max_retries=3)
    async def delete_one(
        collection: AsyncIOMotorCollection,
        query: Dict[str, Any]
    ) -> bool:
        """
        Delete a single document with retry logic.
        
        Args:
            collection: MongoDB collection
            query: Query filter
        
        Returns:
            True if document was deleted, False otherwise
        """
        try:
            result = await collection.delete_one(query)
            return result.deleted_count > 0
        
        except PyMongoError as e:
            logger.error(f"Database delete_one error: {str(e)}")
            raise DatabaseError(f"Failed to delete document: {str(e)}")
    
    @staticmethod
    @with_retry(max_retries=3)
    async def delete_many(
        collection: AsyncIOMotorCollection,
        query: Dict[str, Any]
    ) -> int:
        """
        Delete multiple documents with retry logic.
        
        Args:
            collection: MongoDB collection
            query: Query filter
        
        Returns:
            Number of documents deleted
        """
        try:
            result = await collection.delete_many(query)
            return result.deleted_count
        
        except PyMongoError as e:
            logger.error(f"Database delete_many error: {str(e)}")
            raise DatabaseError(f"Failed to delete documents: {str(e)}")
    
    @staticmethod
    @with_retry(max_retries=3)
    async def count_documents(
        collection: AsyncIOMotorCollection,
        query: Dict[str, Any]
    ) -> int:
        """
        Count documents matching query.
        
        Args:
            collection: MongoDB collection
            query: Query filter
        
        Returns:
            Number of matching documents
        """
        try:
            return await collection.count_documents(query)
        
        except PyMongoError as e:
            logger.error(f"Database count_documents error: {str(e)}")
            raise DatabaseError(f"Failed to count documents: {str(e)}")

db_helper = DatabaseHelper()
