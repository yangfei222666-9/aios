"""
Unit tests for AIOS Memory Module

Tests cover:
- Memory dataclass
- SimpleEmbedding
- VectorDB
- MemoryManager

Run with: pytest test_memory.py -v
"""

import pytest
import tempfile
import time
import json
from pathlib import Path
from unittest.mock import Mock, patch
import numpy as np

# Import from refactored module
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from core.memory_refactored import (
    Memory, MemoryType, MemorySource, MemoryConfig,
    SimpleEmbedding, VectorDB, MemoryManager
)


class TestMemory:
    """Test Memory dataclass."""
    
    def test_memory_creation(self):
        """Test creating a memory with all fields."""
        memory = Memory(
            id="test123",
            content="Test content",
            type=MemoryType.SHORT_TERM.value,
            importance=0.8,
            timestamp=time.time(),
            source=MemorySource.USER.value,
            metadata={"key": "value"}
        )
        
        assert memory.id == "test123"
        assert memory.content == "Test content"
        assert memory.importance == 0.8
    
    def test_memory_auto_id(self):
        """Test automatic ID generation."""
        memory = Memory(
            id="",
            content="Test content",
            type=MemoryType.SHORT_TERM.value,
            importance=0.5,
            timestamp=time.time(),
            source=MemorySource.USER.value,
            metadata={}
        )
        
        assert memory.id != ""
        assert len(memory.id) == 16
    
    def test_memory_importance_validation(self):
        """Test importance score validation."""
        with pytest.raises(ValueError):
            Memory(
                id="",
                content="Test",
                type=MemoryType.SHORT_TERM.value,
                importance=1.5,  # Invalid: > 1.0
                timestamp=time.time(),
                source=MemorySource.USER.value,
                metadata={}
            )
    
    def test_memory_to_dict(self):
        """Test converting memory to dictionary."""
        memory = Memory(
            id="test123",
            content="Test content",
            type=MemoryType.SHORT_TERM.value,
            importance=0.8,
            timestamp=time.time(),
            source=MemorySource.USER.value,
            metadata={"key": "value"}
        )
        
        data = memory.to_dict()
        assert data["id"] == "test123"
        assert data["content"] == "Test content"
        assert data["importance"] == 0.8
    
    def test_memory_from_dict(self):
        """Test creating memory from dictionary."""
        data = {
            "id": "test123",
            "content": "Test content",
            "type": MemoryType.SHORT_TERM.value,
            "importance": 0.8,
            "timestamp": time.time(),
            "source": MemorySource.USER.value,
            "metadata": {"key": "value"}
        }
        
        memory = Memory.from_dict(data)
        assert memory.id == "test123"
        assert memory.content == "Test content"
    
    def test_memory_from_dict_missing_fields(self):
        """Test error handling for missing required fields."""
        data = {
            "id": "test123",
            "content": "Test content"
            # Missing required fields
        }
        
        with pytest.raises(ValueError):
            Memory.from_dict(data)


class TestSimpleEmbedding:
    """Test SimpleEmbedding class."""
    
    def test_embedding_initialization(self):
        """Test embedding initialization."""
        embedding = SimpleEmbedding(dim=64)
        assert embedding.dim == 64
        assert len(embedding.vocab) == 0
    
    def test_embedding_invalid_dim(self):
        """Test error handling for invalid dimension."""
        with pytest.raises(ValueError):
            SimpleEmbedding(dim=0)
    
    def test_embedding_fit(self):
        """Test fitting embedding on texts."""
        embedding = SimpleEmbedding(dim=64)
        texts = [
            "hello world",
            "goodbye world",
            "hello universe"
        ]
        
        embedding.fit(texts)
        assert len(embedding.vocab) > 0
        assert "hello" in embedding.vocab or "world" in embedding.vocab
    
    def test_embedding_fit_empty(self):
        """Test error handling for empty text list."""
        embedding = SimpleEmbedding(dim=64)
        
        with pytest.raises(ValueError):
            embedding.fit([])
    
    def test_embedding_encode(self):
        """Test encoding text to vector."""
        embedding = SimpleEmbedding(dim=64)
        texts = ["hello world", "goodbye world"]
        embedding.fit(texts)
        
        vector = embedding.encode("hello")
        assert len(vector) == 64
        assert isinstance(vector, list)
        assert all(isinstance(v, float) for v in vector)
    
    def test_embedding_encode_without_fit(self):
        """Test error when encoding without fitting."""
        embedding = SimpleEmbedding(dim=64)
        
        with pytest.raises(ValueError):
            embedding.encode("hello")
    
    def test_embedding_encode_empty(self):
        """Test encoding empty text."""
        embedding = SimpleEmbedding(dim=64)
        embedding.fit(["hello world"])
        
        vector = embedding.encode("")
        assert len(vector) == 64
        assert all(v == 0.0 for v in vector)


class TestVectorDB:
    """Test VectorDB class."""
    
    def test_vectordb_initialization(self):
        """Test VectorDB initialization."""
        db = VectorDB(dim=64)
        assert db.dim == 64
        assert len(db.vectors) == 0
        assert len(db.memories) == 0
    
    def test_vectordb_invalid_dim(self):
        """Test error handling for invalid dimension."""
        with pytest.raises(ValueError):
            VectorDB(dim=-1)
    
    def test_vectordb_add(self):
        """Test adding vectors and memories."""
        db = VectorDB(dim=64)
        embedding = [0.1] * 64
        memory = Memory(
            id="test",
            content="Test",
            type=MemoryType.SHORT_TERM.value,
            importance=0.5,
            timestamp=time.time(),
            source=MemorySource.USER.value,
            metadata={}
        )
        
        db.add(embedding, memory)
        assert len(db.vectors) == 1
        assert len(db.memories) == 1
    
    def test_vectordb_add_wrong_dim(self):
        """Test error when adding vector with wrong dimension."""
        db = VectorDB(dim=64)
        embedding = [0.1] * 32  # Wrong dimension
        memory = Memory(
            id="test",
            content="Test",
            type=MemoryType.SHORT_TERM.value,
            importance=0.5,
            timestamp=time.time(),
            source=MemorySource.USER.value,
            metadata={}
        )
        
        with pytest.raises(ValueError):
            db.add(embedding, memory)
    
    def test_vectordb_search(self):
        """Test searching for similar vectors."""
        db = VectorDB(dim=64)
        
        # Add some memories
        for i in range(5):
            embedding = [0.1 * i] * 64
            memory = Memory(
                id=f"test{i}",
                content=f"Test {i}",
                type=MemoryType.SHORT_TERM.value,
                importance=0.5,
                timestamp=time.time(),
                source=MemorySource.USER.value,
                metadata={}
            )
            db.add(embedding, memory)
        
        # Search
        query = [0.2] * 64
        results = db.search(query, k=3)
        
        assert len(results) <= 3
        assert all(isinstance(m, Memory) for m in results)
    
    def test_vectordb_search_empty(self):
        """Test searching in empty database."""
        db = VectorDB(dim=64)
        query = [0.1] * 64
        results = db.search(query, k=5)
        
        assert len(results) == 0
    
    def test_vectordb_search_wrong_dim(self):
        """Test error when searching with wrong dimension."""
        db = VectorDB(dim=64)
        
        # Add at least one vector so search actually runs
        embedding = [0.1] * 64
        memory = Memory(
            id="test",
            content="Test",
            type=MemoryType.SHORT_TERM.value,
            importance=0.5,
            timestamp=time.time(),
            source=MemorySource.USER.value,
            metadata={}
        )
        db.add(embedding, memory)
        
        # Now test with wrong dimension
        query = [0.1] * 32  # Wrong dimension
        
        with pytest.raises(ValueError):
            db.search(query, k=5)
    
    def test_vectordb_save_load(self):
        """Test saving and loading database."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test_db.json"
            
            # Create and populate database
            db = VectorDB(dim=64)
            embedding = [0.1] * 64
            memory = Memory(
                id="test",
                content="Test content",
                type=MemoryType.SHORT_TERM.value,
                importance=0.8,
                timestamp=time.time(),
                source=MemorySource.USER.value,
                metadata={"key": "value"}
            )
            db.add(embedding, memory)
            
            # Save
            db.save(db_path)
            assert db_path.exists()
            
            # Load into new database
            db2 = VectorDB(dim=64)
            db2.load(db_path)
            
            assert len(db2.vectors) == 1
            assert len(db2.memories) == 1
            assert db2.memories[0].content == "Test content"


class TestMemoryManager:
    """Test MemoryManager class."""
    
    @pytest.fixture
    def temp_workspace(self):
        """Create temporary workspace for testing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir)
            
            # Create MEMORY.md for initialization
            memory_md = workspace / "MEMORY.md"
            memory_md.write_text(
                "# Test Memory\n\n"
                "This is a test memory file.\n\n"
                "It contains some paragraphs for testing.\n\n"
                "Each paragraph should be indexed."
            )
            
            yield workspace
    
    def test_manager_initialization(self, temp_workspace):
        """Test MemoryManager initialization."""
        manager = MemoryManager(temp_workspace)
        
        assert manager.workspace == temp_workspace
        assert (temp_workspace / "memory").exists()
        assert isinstance(manager.config, MemoryConfig)
    
    def test_manager_store(self, temp_workspace):
        """Test storing memories."""
        manager = MemoryManager(temp_workspace)
        
        memory = manager.store(
            "Test content",
            importance=0.9,
            metadata={"key": "value"}
        )
        
        assert memory.content == "Test content"
        assert memory.importance == 0.9
        assert len(manager.short_term) > 0
    
    def test_manager_store_empty_content(self, temp_workspace):
        """Test error when storing empty content."""
        manager = MemoryManager(temp_workspace)
        
        with pytest.raises(ValueError):
            manager.store("")
    
    def test_manager_store_auto_importance(self, temp_workspace):
        """Test automatic importance calculation."""
        manager = MemoryManager(temp_workspace)
        
        memory = manager.store("Short text")
        assert 0.0 <= memory.importance <= 1.0
    
    def test_manager_retrieve(self, temp_workspace):
        """Test retrieving memories."""
        manager = MemoryManager(temp_workspace)
        
        # Store some memories
        manager.store("Planning module implementation", importance=0.9)
        manager.store("Bug fix", importance=0.3)
        manager.store("Memory module design", importance=0.9)
        
        # Retrieve
        results = manager.retrieve("Planning", k=5)
        
        assert len(results) > 0
        assert all(isinstance(m, Memory) for m in results)
    
    def test_manager_retrieve_empty_query(self, temp_workspace):
        """Test error when retrieving with empty query."""
        manager = MemoryManager(temp_workspace)
        
        with pytest.raises(ValueError):
            manager.retrieve("")
    
    def test_manager_working_memory(self, temp_workspace):
        """Test working memory operations."""
        manager = MemoryManager(temp_workspace)
        
        task_id = "task_123"
        
        # Store working memories
        manager.store_working(task_id, "Step 1")
        manager.store_working(task_id, "Step 2")
        
        # Retrieve
        working_mems = manager.get_working(task_id)
        assert len(working_mems) == 2
        
        # Clear
        manager.clear_working(task_id)
        assert len(manager.get_working(task_id)) == 0
    
    def test_manager_working_memory_empty_task_id(self, temp_workspace):
        """Test error when storing working memory with empty task ID."""
        manager = MemoryManager(temp_workspace)
        
        with pytest.raises(ValueError):
            manager.store_working("", "Content")
    
    def test_manager_consolidate(self, temp_workspace):
        """Test memory consolidation."""
        manager = MemoryManager(temp_workspace)
        
        # Store some memories
        for i in range(10):
            manager.store(f"Memory {i}", importance=0.5 + i * 0.05)
        
        # Consolidate
        stats = manager.consolidate()
        
        assert "promoted" in stats
        assert "trimmed" in stats
        assert "short_term_count" in stats
        assert "long_term_count" in stats
    
    def test_manager_get_stats(self, temp_workspace):
        """Test getting memory statistics."""
        manager = MemoryManager(temp_workspace)
        
        # Store some memories
        manager.store("Test 1", importance=0.9)
        manager.store("Test 2", importance=0.5)
        
        stats = manager.get_stats()
        
        assert "short_term_count" in stats
        assert "long_term_count" in stats
        assert "total_memories" in stats
        assert stats["total_memories"] > 0


class TestMemoryConfig:
    """Test MemoryConfig dataclass."""
    
    def test_config_defaults(self):
        """Test default configuration values."""
        config = MemoryConfig()
        
        assert config.embedding_dim == 128
        assert config.short_term_limit == 100
        assert config.importance_threshold == 0.7
    
    def test_config_custom(self):
        """Test custom configuration."""
        config = MemoryConfig(
            embedding_dim=256,
            short_term_limit=50,
            importance_threshold=0.8
        )
        
        assert config.embedding_dim == 256
        assert config.short_term_limit == 50
        assert config.importance_threshold == 0.8


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
