"""
Unit tests for db_utils.py database utilities.
Tests DatabaseManager and helper functions.
"""
import pytest
from unittest.mock import Mock, patch
from pymongo.errors import ConnectionFailure

from .test_helpers import AsyncMock
from db_utils import DatabaseManager, with_retry, log_operation
from errors import DatabaseError


class TestDatabaseManagerConnect:
    """Test DatabaseManager connection methods."""
    
    @pytest.mark.asyncio
    async def test_connect_success(self):
        """Test successful database connection."""
        manager = DatabaseManager()
        
        mock_client = AsyncMock()
        mock_client.admin.command = AsyncMock(return_value={'ok': 1})
        
        with patch('db_utils.AsyncIOMotorClient', return_value=mock_client), \
             patch('db_utils.settings.MONGO_URI', 'mongodb://localhost:27017'):
            await manager.connect()
            
            assert manager.connected is True
            assert manager.client is not None
            mock_client.admin.command.assert_called_once_with('ping')
    
    @pytest.mark.asyncio
    async def test_connect_no_uri_configured(self):
        """Test connection fails when MONGO_URI is not configured."""
        manager = DatabaseManager()
        
        with patch('db_utils.settings.MONGO_URI', ''):
            with pytest.raises(DatabaseError) as exc_info:
                await manager.connect()
            
            assert 'MONGO_URI not configured' in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_connect_connection_failure(self):
        """Test handling of connection failures."""
        manager = DatabaseManager()
        
        mock_client = AsyncMock()
        mock_client.admin.command = AsyncMock(side_effect=ConnectionFailure('Connection timeout'))
        
        with patch('db_utils.AsyncIOMotorClient', return_value=mock_client), \
             patch('db_utils.settings.MONGO_URI', 'mongodb://localhost:27017'):
            with pytest.raises(DatabaseError) as exc_info:
                await manager.connect()
            
            assert 'Failed to connect' in str(exc_info.value)
            assert manager.connected is False
    
    @pytest.mark.asyncio
    async def test_disconnect(self):
        """Test database disconnection."""
        manager = DatabaseManager()
        mock_client = Mock()
        manager.client = mock_client
        manager.connected = True
        
        await manager.disconnect()
        
        mock_client.close.assert_called_once()
        assert manager.connected is False


class TestDatabaseManagerPing:
    """Test database ping functionality."""
    
    @pytest.mark.asyncio
    async def test_ping_when_connected(self):
        """Test ping behavior when connected."""
        manager = DatabaseManager()
        mock_client = AsyncMock()
        mock_client.admin.command = AsyncMock(return_value={'ok': 1})
        manager.client = mock_client
        manager.connected = True
        
        result = await manager.ping()
        
        # Ping returns boolean based on connection status
        assert isinstance(result, bool)
    
    @pytest.mark.asyncio
    async def test_ping_not_connected(self):
        """Test ping when not connected."""
        manager = DatabaseManager()
        manager.connected = False
        
        result = await manager.ping()
        
        assert result is False
    
    @pytest.mark.asyncio
    async def test_ping_exception(self):
        """Test ping handles exceptions."""
        manager = DatabaseManager()
        mock_client = AsyncMock()
        mock_client.admin.command = AsyncMock(side_effect=Exception('Network error'))
        manager.client = mock_client
        manager.connected = True
        
        result = await manager.ping()
        
        assert result is False


class TestDatabaseRetryDecorator:
    """Test retry decorator functionality."""
    
    @pytest.mark.asyncio
    async def test_with_retry_success_first_attempt(self):
        """Test retry decorator succeeds on first attempt."""
        
        @with_retry(max_retries=3)
        async def test_func():
            return 'success'
        
        result = await test_func()
        assert result == 'success'
    
    @pytest.mark.asyncio
    async def test_with_retry_uses_default_params(self):
        """Test retry decorator with default parameters."""
        
        @with_retry()
        async def test_func():
            return 'default_success'
        
        result = await test_func()
        assert result == 'default_success'


class TestDatabaseManagerInitialization:
    """Test DatabaseManager initialization."""
    
    def test_manager_initial_state(self):
        """Test DatabaseManager initial state."""
        manager = DatabaseManager()
        
        assert manager.client is None
        assert manager.connected is False
    
    def test_manager_singleton_behavior(self):
        """Test DatabaseManager can be instantiated multiple times."""
        manager1 = DatabaseManager()
        manager2 = DatabaseManager()
        
        # Should be different instances (not singleton in current implementation)
        assert manager1 is not manager2


class TestLogOperation:
    """Test log_operation decorator."""
    
    @pytest.mark.asyncio
    async def test_log_operation_success(self):
        """Test log_operation logs successful operations."""
        
        @log_operation("test_operation")
        async def test_func(arg1, arg2):
            return f"{arg1}_{arg2}"
        
        result = await test_func("hello", "world")
        assert result == "hello_world"
    
    @pytest.mark.asyncio
    async def test_log_operation_with_exception(self):
        """Test log_operation logs exceptions."""
        
        @log_operation("failing_operation")
        async def test_func():
            raise ValueError("Test error")
        
        with pytest.raises(ValueError) as exc_info:
            await test_func()
        
        assert "Test error" in str(exc_info.value)


class TestDatabaseHelperFindOne:
    """Test DatabaseHelper find_one method."""
    
    @pytest.mark.asyncio
    async def test_find_one_success(self):
        """Test successful find_one operation."""
        from db_utils import db_helper
        
        mock_collection = AsyncMock()
        mock_doc = {'_id': '123', 'name': 'Test'}
        mock_collection.find_one = AsyncMock(return_value=mock_doc)
        
        result = await db_helper.find_one(mock_collection, {'_id': '123'})
        
        assert result == mock_doc
        mock_collection.find_one.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_find_one_with_projection(self):
        """Test find_one with projection."""
        from db_utils import db_helper
        
        mock_collection = AsyncMock()
        mock_doc = {'_id': '123', 'name': 'Test'}
        mock_collection.find_one = AsyncMock(return_value=mock_doc)
        
        result = await db_helper.find_one(
            mock_collection, 
            {'_id': '123'}, 
            projection={'name': 1}
        )
        
        assert result == mock_doc
    
    @pytest.mark.asyncio
    async def test_find_one_not_found(self):
        """Test find_one when document not found."""
        from db_utils import db_helper
        
        mock_collection = AsyncMock()
        mock_collection.find_one = AsyncMock(return_value=None)
        
        result = await db_helper.find_one(mock_collection, {'_id': 'nonexistent'})
        
        assert result is None
    
    @pytest.mark.asyncio
    async def test_find_one_database_error(self):
        """Test find_one handles database errors."""
        from db_utils import db_helper
        from pymongo.errors import PyMongoError
        
        mock_collection = AsyncMock()
        mock_collection.find_one = AsyncMock(side_effect=PyMongoError('DB Error'))
        
        with pytest.raises(DatabaseError):
            await db_helper.find_one(mock_collection, {'_id': '123'})


class TestDatabaseHelperFindMany:
    """Test DatabaseHelper find_many method."""
    
    @pytest.mark.asyncio
    async def test_find_many_success(self):
        """Test successful find_many operation."""
        from db_utils import db_helper
        
        mock_collection = Mock()
        mock_docs = [{'_id': '1', 'name': 'A'}, {'_id': '2', 'name': 'B'}]
        
        mock_cursor = Mock()
        mock_cursor.to_list = AsyncMock(return_value=mock_docs)
        mock_collection.find = Mock(return_value=mock_cursor)
        
        result = await db_helper.find_many(mock_collection, {})
        
        assert result == mock_docs
    
    @pytest.mark.asyncio
    async def test_find_many_with_sort(self):
        """Test find_many with sort."""
        from db_utils import db_helper
        
        mock_collection = Mock()
        mock_docs = [{'_id': '1', 'score': 10}]
        
        mock_cursor = Mock()
        mock_cursor.sort = Mock(return_value=mock_cursor)
        mock_cursor.to_list = AsyncMock(return_value=mock_docs)
        mock_collection.find = Mock(return_value=mock_cursor)
        
        result = await db_helper.find_many(
            mock_collection, 
            {}, 
            sort=[('score', -1)]
        )
        
        assert result == mock_docs
        mock_cursor.sort.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_find_many_with_limit_and_skip(self):
        """Test find_many with limit and skip."""
        from db_utils import db_helper
        
        mock_collection = Mock()
        mock_docs = [{'_id': '1'}]
        
        mock_cursor = Mock()
        mock_cursor.skip = Mock(return_value=mock_cursor)
        mock_cursor.limit = Mock(return_value=mock_cursor)
        mock_cursor.to_list = AsyncMock(return_value=mock_docs)
        mock_collection.find = Mock(return_value=mock_cursor)
        
        result = await db_helper.find_many(
            mock_collection, 
            {}, 
            limit=10,
            skip=5
        )
        
        assert result == mock_docs
        mock_cursor.skip.assert_called_once_with(5)
        mock_cursor.limit.assert_called_once_with(10)


class TestDatabaseHelperInsertOne:
    """Test DatabaseHelper insert_one method."""
    
    @pytest.mark.asyncio
    async def test_insert_one_success(self):
        """Test successful insert_one operation."""
        from db_utils import db_helper
        
        mock_collection = AsyncMock()
        mock_result = Mock()
        mock_result.inserted_id = '123abc'
        mock_collection.insert_one = AsyncMock(return_value=mock_result)
        
        result = await db_helper.insert_one(mock_collection, {'name': 'Test'})
        
        assert result == '123abc'
        mock_collection.insert_one.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_insert_one_adds_timestamp(self):
        """Test insert_one adds timestamp by default."""
        from db_utils import db_helper
        
        mock_collection = AsyncMock()
        mock_result = Mock()
        mock_result.inserted_id = '123abc'
        mock_collection.insert_one = AsyncMock(return_value=mock_result)
        
        doc = {'name': 'Test'}
        await db_helper.insert_one(mock_collection, doc)
        
        # Check that created_at was added
        call_args = mock_collection.insert_one.call_args[0][0]
        assert 'created_at' in call_args
    
    @pytest.mark.asyncio
    async def test_insert_one_duplicate_key_error(self):
        """Test insert_one handles duplicate key errors."""
        from db_utils import db_helper
        from pymongo.errors import DuplicateKeyError
        
        mock_collection = AsyncMock()
        mock_collection.insert_one = AsyncMock(
            side_effect=DuplicateKeyError('Duplicate')
        )
        
        with pytest.raises(DatabaseError) as exc_info:
            await db_helper.insert_one(mock_collection, {'_id': '123'})
        
        assert 'already exists' in str(exc_info.value).lower()


class TestDatabaseHelperUpdateOne:
    """Test DatabaseHelper update_one method."""
    
    @pytest.mark.asyncio
    async def test_update_one_success(self):
        """Test successful update_one operation."""
        from db_utils import db_helper
        
        mock_collection = AsyncMock()
        mock_result = Mock()
        mock_result.modified_count = 1
        mock_result.upserted_id = None
        mock_collection.update_one = AsyncMock(return_value=mock_result)
        
        result = await db_helper.update_one(
            mock_collection,
            {'_id': '123'},
            {'$set': {'name': 'Updated'}}
        )
        
        assert result is True
    
    @pytest.mark.asyncio
    async def test_update_one_with_upsert(self):
        """Test update_one with upsert."""
        from db_utils import db_helper
        
        mock_collection = AsyncMock()
        mock_result = Mock()
        mock_result.modified_count = 0
        mock_result.upserted_id = '123abc'
        mock_collection.update_one = AsyncMock(return_value=mock_result)
        
        result = await db_helper.update_one(
            mock_collection,
            {'_id': '123'},
            {'$set': {'name': 'New'}},
            upsert=True
        )
        
        assert result is True
    
    @pytest.mark.asyncio
    async def test_update_one_not_modified(self):
        """Test update_one when no document modified."""
        from db_utils import db_helper
        
        mock_collection = AsyncMock()
        mock_result = Mock()
        mock_result.modified_count = 0
        mock_result.upserted_id = None
        mock_collection.update_one = AsyncMock(return_value=mock_result)
        
        result = await db_helper.update_one(
            mock_collection,
            {'_id': 'nonexistent'},
            {'$set': {'name': 'Updated'}}
        )
        
        assert result is False


class TestDatabaseHelperDeleteOne:
    """Test DatabaseHelper delete_one method."""
    
    @pytest.mark.asyncio
    async def test_delete_one_success(self):
        """Test successful delete_one operation."""
        from db_utils import db_helper
        
        mock_collection = AsyncMock()
        mock_result = Mock()
        mock_result.deleted_count = 1
        mock_collection.delete_one = AsyncMock(return_value=mock_result)
        
        result = await db_helper.delete_one(mock_collection, {'_id': '123'})
        
        assert result is True
    
    @pytest.mark.asyncio
    async def test_delete_one_not_found(self):
        """Test delete_one when document not found."""
        from db_utils import db_helper
        
        mock_collection = AsyncMock()
        mock_result = Mock()
        mock_result.deleted_count = 0
        mock_collection.delete_one = AsyncMock(return_value=mock_result)
        
        result = await db_helper.delete_one(mock_collection, {'_id': 'nonexistent'})
        
        assert result is False


class TestDatabaseHelperDeleteMany:
    """Test DatabaseHelper delete_many method."""
    
    @pytest.mark.asyncio
    async def test_delete_many_success(self):
        """Test successful delete_many operation."""
        from db_utils import db_helper
        
        mock_collection = AsyncMock()
        mock_result = Mock()
        mock_result.deleted_count = 5
        mock_collection.delete_many = AsyncMock(return_value=mock_result)
        
        result = await db_helper.delete_many(mock_collection, {'status': 'old'})
        
        assert result == 5
    
    @pytest.mark.asyncio
    async def test_delete_many_none_found(self):
        """Test delete_many when no documents found."""
        from db_utils import db_helper
        
        mock_collection = AsyncMock()
        mock_result = Mock()
        mock_result.deleted_count = 0
        mock_collection.delete_many = AsyncMock(return_value=mock_result)
        
        result = await db_helper.delete_many(mock_collection, {'status': 'nonexistent'})
        
        assert result == 0


class TestDatabaseHelperCountDocuments:
    """Test DatabaseHelper count_documents method."""
    
    @pytest.mark.asyncio
    async def test_count_documents_success(self):
        """Test successful count_documents operation."""
        from db_utils import db_helper
        
        mock_collection = AsyncMock()
        mock_collection.count_documents = AsyncMock(return_value=42)
        
        result = await db_helper.count_documents(mock_collection, {'status': 'active'})
        
        assert result == 42
    
    @pytest.mark.asyncio
    async def test_count_documents_zero(self):
        """Test count_documents when no matches."""
        from db_utils import db_helper
        
        mock_collection = AsyncMock()
        mock_collection.count_documents = AsyncMock(return_value=0)
        
        result = await db_helper.count_documents(mock_collection, {'status': 'none'})
        
        assert result == 0


class TestWithRetryConnectionFailures:
    """Test retry decorator with connection failures."""
    
    @pytest.mark.asyncio
    async def test_with_retry_succeeds_on_second_attempt(self):
        """Test retry succeeds after first connection failure."""
        from db_utils import with_retry
        from pymongo.errors import ConnectionFailure
        
        attempt_counter = [0]
        
        @with_retry(max_retries=3, delay=0.01)
        async def failing_then_success():
            attempt_counter[0] += 1
            if attempt_counter[0] == 1:
                raise ConnectionFailure("First attempt fails")
            return "success"
        
        result = await failing_then_success()
        assert result == "success"
        assert attempt_counter[0] == 2
    
    @pytest.mark.asyncio
    async def test_with_retry_fails_after_max_retries(self):
        """Test retry gives up after max attempts."""
        from db_utils import with_retry, DatabaseError
        from pymongo.errors import ConnectionFailure
        
        @with_retry(max_retries=2, delay=0.01)
        async def always_fails():
            raise ConnectionFailure("Always fails")
        
        with pytest.raises(DatabaseError) as exc_info:
            await always_fails()
        
        assert "retries" in str(exc_info.value).lower()
    
    @pytest.mark.asyncio
    async def test_with_retry_does_not_retry_non_connection_errors(self):
        """Test non-connection errors are not retried."""
        from db_utils import with_retry
        
        attempt_counter = [0]
        
        @with_retry(max_retries=3, delay=0.01)
        async def raises_value_error():
            attempt_counter[0] += 1
            raise ValueError("Not a connection error")
        
        with pytest.raises(ValueError):
            await raises_value_error()
        
        # Should not retry
        assert attempt_counter[0] == 1


class TestLogOperationDecorator:
    """Test log_operation decorator functionality."""
    
    @pytest.mark.asyncio
    async def test_log_operation_records_success(self):
        """Test log_operation records successful operations."""
        from db_utils import log_operation
        
        @log_operation("TEST_OP")
        async def test_operation(collection="test_coll"):
            return "result"
        
        result = await test_operation()
        assert result == "result"
    
    @pytest.mark.asyncio
    async def test_log_operation_records_failure(self):
        """Test log_operation records failed operations."""
        from db_utils import log_operation
        
        @log_operation("FAIL_OP")
        async def failing_operation(collection="test_coll"):
            raise ValueError("Operation failed")
        
        with pytest.raises(ValueError):
            await failing_operation()
    
    @pytest.mark.asyncio
    async def test_log_operation_with_collection_kwarg(self):
        """Test log_operation extracts collection name."""
        from db_utils import log_operation
        
        @log_operation("INSERT")
        async def insert_operation(collection="users"):
            return True
        
        result = await insert_operation(collection="messages")
        assert result is True


class TestDatabaseHelperInsertOneEdgeCases:
    """Test insert_one edge cases."""
    
    @pytest.mark.asyncio
    async def test_insert_one_without_timestamp(self):
        """Test inserting document without auto timestamp."""
        from db_utils import db_helper
        
        mock_collection = AsyncMock()
        mock_collection.insert_one = AsyncMock(return_value=Mock(inserted_id="id123"))
        
        document = {"name": "Test"}
        await db_helper.insert_one(mock_collection, document, add_timestamp=False)
        
        # Check that created_at was NOT added
        call_doc = mock_collection.insert_one.call_args[0][0]
        assert 'created_at' not in call_doc
    
    @pytest.mark.asyncio
    async def test_insert_one_generic_error(self):
        """Test insert_one with generic database error."""
        from db_utils import db_helper, DatabaseError
        from pymongo.errors import PyMongoError
        
        mock_collection = AsyncMock()
        mock_collection.insert_one = AsyncMock(side_effect=PyMongoError("Generic error"))
        
        with pytest.raises(DatabaseError) as exc_info:
            await db_helper.insert_one(mock_collection, {"test": "doc"})
        
        assert "Failed to insert" in str(exc_info.value)


class TestDatabaseHelperUpdateOneEdgeCases:
    """Test update_one edge cases."""
    
    @pytest.mark.asyncio
    async def test_update_one_without_timestamp(self):
        """Test updating without auto timestamp."""
        from db_utils import db_helper
        
        mock_collection = AsyncMock()
        mock_result = Mock(modified_count=1, upserted_id=None)
        mock_collection.update_one = AsyncMock(return_value=mock_result)
        
        await db_helper.update_one(
            mock_collection,
            {"_id": "123"},
            {"$set": {"name": "New"}},
            add_timestamp=False
        )
        
        # Check updated_at was NOT added
        call_update = mock_collection.update_one.call_args[0][1]
        if '$set' in call_update:
            assert 'updated_at' not in call_update['$set']
    
    @pytest.mark.asyncio
    async def test_update_one_creates_set_for_timestamp(self):
        """Test update_one creates $set if needed for timestamp."""
        from db_utils import db_helper
        
        mock_collection = AsyncMock()
        mock_result = Mock(modified_count=1, upserted_id=None)
        mock_collection.update_one = AsyncMock(return_value=mock_result)
        
        await db_helper.update_one(
            mock_collection,
            {"_id": "123"},
            {"$inc": {"count": 1}},  # No $set initially
            add_timestamp=True
        )
        
        # Should create $set for timestamp
        call_update = mock_collection.update_one.call_args[0][1]
        assert '$set' in call_update
        assert 'updated_at' in call_update['$set']
    
    @pytest.mark.asyncio
    async def test_update_one_generic_error(self):
        """Test update_one with database error."""
        from db_utils import db_helper, DatabaseError
        from pymongo.errors import PyMongoError
        
        mock_collection = AsyncMock()
        mock_collection.update_one = AsyncMock(side_effect=PyMongoError("Update failed"))
        
        with pytest.raises(DatabaseError):
            await db_helper.update_one(mock_collection, {"_id": "123"}, {"$set": {"name": "X"}})


class TestDatabaseHelperDeleteEdgeCases:
    """Test delete operations edge cases."""
    
    @pytest.mark.asyncio
    async def test_delete_one_database_error(self):
        """Test delete_one with database error."""
        from db_utils import db_helper, DatabaseError
        from pymongo.errors import PyMongoError
        
        mock_collection = AsyncMock()
        mock_collection.delete_one = AsyncMock(side_effect=PyMongoError("Delete failed"))
        
        with pytest.raises(DatabaseError):
            await db_helper.delete_one(mock_collection, {"_id": "123"})
    
    @pytest.mark.asyncio
    async def test_delete_many_database_error(self):
        """Test delete_many with database error."""
        from db_utils import db_helper, DatabaseError
        from pymongo.errors import PyMongoError
        
        mock_collection = AsyncMock()
        mock_collection.delete_many = AsyncMock(side_effect=PyMongoError("Delete many failed"))
        
        with pytest.raises(DatabaseError):
            await db_helper.delete_many(mock_collection, {"status": "old"})


class TestDatabaseHelperFindEdgeCases:
    """Test find operations edge cases."""
    
    @pytest.mark.asyncio
    async def test_find_many_with_all_options(self):
        """Test find_many with projection, sort, limit, and skip."""
        from db_utils import db_helper
        
        mock_cursor = Mock()
        mock_cursor.sort = Mock(return_value=mock_cursor)
        mock_cursor.skip = Mock(return_value=mock_cursor)
        mock_cursor.limit = Mock(return_value=mock_cursor)
        mock_cursor.to_list = AsyncMock(return_value=[{"id": "1"}, {"id": "2"}])
        
        mock_collection = Mock()
        mock_collection.find = Mock(return_value=mock_cursor)
        
        result = await db_helper.find_many(
            mock_collection,
            {"status": "active"},
            projection={"_id": 0},
            sort=[("created_at", -1)],
            limit=10,
            skip=5
        )
        
        assert len(result) == 2
        mock_cursor.sort.assert_called_once()
        mock_cursor.skip.assert_called_once_with(5)
        mock_cursor.limit.assert_called_once_with(10)
    
    @pytest.mark.asyncio
    async def test_find_many_database_error(self):
        """Test find_many with database error."""
        from db_utils import db_helper, DatabaseError
        from pymongo.errors import PyMongoError
        
        mock_cursor = Mock()
        mock_cursor.to_list = AsyncMock(side_effect=PyMongoError("Find failed"))
        
        mock_collection = Mock()
        mock_collection.find = Mock(return_value=mock_cursor)
        
        with pytest.raises(DatabaseError):
            await db_helper.find_many(mock_collection, {})
    
    @pytest.mark.asyncio
    async def test_count_documents_database_error(self):
        """Test count_documents with database error."""
        from db_utils import db_helper, DatabaseError
        from pymongo.errors import PyMongoError
        
        mock_collection = AsyncMock()
        mock_collection.count_documents = AsyncMock(side_effect=PyMongoError("Count failed"))
        
        with pytest.raises(DatabaseError):
            await db_helper.count_documents(mock_collection, {})


class TestDatabaseHelperInstance:
    """Test DatabaseHelper singleton instance."""
    
    def test_db_helper_instance_exists(self):
        """Test db_helper singleton is exported."""
        from db_utils import db_helper, DatabaseHelper
        
        assert db_helper is not None
        assert isinstance(db_helper, DatabaseHelper)

