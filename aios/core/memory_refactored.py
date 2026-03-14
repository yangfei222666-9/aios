"""
AIOS Memory Module - 记忆管理系统

This module provides a hierarchical memory system for AIOS with:
- Vector-based retrieval (FAISS-style)
- Three-tier memory architecture (short-term/long-term/working)
- Automatic consolidation and importance scoring
- Persistent storage with JSON serialization

Author: 小九 + 珊瑚海
Date: 2026-02-26
Refactored: 2026-03-14
"""

import json
import logging
import time
import numpy as np
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, asdict, field
from datetime import datetime, timedelta
from enum import Enum
import hashlib
import re

# Configure logging
logger = logging.getLogger(__name__)


# Constants
DEFAULT_EMBEDDING_DIM = 128
DEFAULT_SHORT_TERM_LIMIT = 100
DEFAULT_IMPORTANCE_THRESHOLD = 0.7
DEFAULT_CONSOLIDATION_DAYS = 7
MIN_PARAGRAPH_LENGTH = 20
MAX_RECENT_UPDATES = 10
MIN_SIMILARITY_THRESHOLD = 0.1


class MemoryType(Enum):
    """Memory type enumeration."""
    SHORT_TERM = "short_term"
    LONG_TERM = "long_term"
    WORKING = "working"


class MemorySource(Enum):
    """Memory source enumeration."""
    USER = "user"
    AGENT = "agent"
    SYSTEM = "system"


@dataclass
class MemoryConfig:
    """Configuration for Memory Manager.
    
    Attributes:
        embedding_dim: Dimension of embedding vectors
        short_term_limit: Maximum number of short-term memories
        importance_threshold: Threshold for promoting to long-term memory
        consolidation_days: Days to look back for consolidation
        min_similarity: Minimum similarity score for retrieval
    """
    embedding_dim: int = DEFAULT_EMBEDDING_DIM
    short_term_limit: int = DEFAULT_SHORT_TERM_LIMIT
    importance_threshold: float = DEFAULT_IMPORTANCE_THRESHOLD
    consolidation_days: int = DEFAULT_CONSOLIDATION_DAYS
    min_similarity: float = MIN_SIMILARITY_THRESHOLD


@dataclass
class Memory:
    """A single memory unit.
    
    Attributes:
        id: Unique identifier (auto-generated from content hash)
        content: The actual memory content
        type: Memory type (short_term/long_term/working)
        importance: Importance score (0.0 - 1.0)
        timestamp: Unix timestamp when created
        source: Source of the memory (user/agent/system)
        metadata: Additional metadata dictionary
        embedding: Optional embedding vector
    
    Example:
        >>> memory = Memory(
        ...     id="",
        ...     content="Implemented Planning module",
        ...     type=MemoryType.LONG_TERM.value,
        ...     importance=0.9,
        ...     timestamp=time.time(),
        ...     source=MemorySource.AGENT.value,
        ...     metadata={"project": "AIOS"}
        ... )
    """
    id: str
    content: str
    type: str
    importance: float
    timestamp: float
    source: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    embedding: Optional[List[float]] = None
    
    def __post_init__(self) -> None:
        """Generate unique ID if not provided."""
        if not self.id:
            self.id = self._generate_id()
        
        # Validate importance score
        if not 0.0 <= self.importance <= 1.0:
            raise ValueError(f"Importance must be between 0.0 and 1.0, got {self.importance}")
    
    def _generate_id(self) -> str:
        """Generate unique ID from content and timestamp.
        
        Returns:
            16-character hexadecimal ID
        """
        content_hash = hashlib.md5(
            f"{self.content}{self.timestamp}".encode()
        ).hexdigest()
        return content_hash[:16]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization.
        
        Returns:
            Dictionary representation
        """
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Memory':
        """Create Memory from dictionary.
        
        Args:
            data: Dictionary with memory data
            
        Returns:
            Memory instance
            
        Raises:
            ValueError: If required fields are missing
        """
        required_fields = ['content', 'type', 'importance', 'timestamp', 'source']
        missing = [f for f in required_fields if f not in data]
        if missing:
            raise ValueError(f"Missing required fields: {missing}")
        
        return cls(**data)


class SimpleEmbedding:
    """Simple TF-IDF style embedding implementation.
    
    This is a lightweight embedding model that doesn't require external
    dependencies. For production use, consider using sentence-transformers
    or OpenAI embeddings.
    
    Attributes:
        dim: Embedding dimension
        vocab: Word to index mapping
        idf: Inverse document frequency scores
    
    Example:
        >>> embedding = SimpleEmbedding(dim=128)
        >>> texts = ["hello world", "goodbye world"]
        >>> embedding.fit(texts)
        >>> vector = embedding.encode("hello")
    """
    
    def __init__(self, dim: int = DEFAULT_EMBEDDING_DIM):
        """Initialize embedding model.
        
        Args:
            dim: Embedding dimension (default: 128)
        """
        if dim <= 0:
            raise ValueError(f"Dimension must be positive, got {dim}")
        
        self.dim = dim
        self.vocab: Dict[str, int] = {}
        self.idf: Dict[str, float] = {}
        logger.info(f"Initialized SimpleEmbedding with dim={dim}")
    
    def fit(self, texts: List[str]) -> None:
        """Build vocabulary and IDF scores from texts.
        
        Args:
            texts: List of text documents
            
        Raises:
            ValueError: If texts is empty
        """
        if not texts:
            raise ValueError("Cannot fit on empty text list")
        
        try:
            # Count document frequency
            doc_freq: Dict[str, int] = {}
            for text in texts:
                words = set(self._tokenize(text))
                for word in words:
                    doc_freq[word] = doc_freq.get(word, 0) + 1
            
            # Build vocabulary (top dim words by frequency)
            sorted_words = sorted(
                doc_freq.items(), 
                key=lambda x: x[1], 
                reverse=True
            )
            self.vocab = {
                word: i 
                for i, (word, _) in enumerate(sorted_words[:self.dim])
            }
            
            # Calculate IDF
            n_docs = len(texts)
            for word, freq in doc_freq.items():
                self.idf[word] = np.log(n_docs / (freq + 1))
            
            logger.info(f"Fitted embedding on {len(texts)} documents, vocab size={len(self.vocab)}")
            
        except Exception as e:
            logger.error(f"Error fitting embedding: {e}")
            raise
    
    def encode(self, text: str) -> List[float]:
        """Encode text to embedding vector.
        
        Args:
            text: Input text
            
        Returns:
            Normalized embedding vector
            
        Raises:
            ValueError: If vocabulary is empty (call fit() first)
        """
        if not self.vocab:
            raise ValueError("Vocabulary is empty. Call fit() first.")
        
        try:
            vector = np.zeros(self.dim)
            words = self._tokenize(text)
            
            if not words:
                return vector.tolist()
            
            # Calculate TF-IDF
            word_count: Dict[str, int] = {}
            for word in words:
                word_count[word] = word_count.get(word, 0) + 1
            
            for word, count in word_count.items():
                if word in self.vocab:
                    idx = self.vocab[word]
                    tf = count / len(words)
                    idf = self.idf.get(word, 1.0)
                    vector[idx] = tf * idf
            
            # Normalize
            norm = np.linalg.norm(vector)
            if norm > 0:
                vector = vector / norm
            
            return vector.tolist()
            
        except Exception as e:
            logger.error(f"Error encoding text: {e}")
            raise
    
    def _tokenize(self, text: str) -> List[str]:
        """Tokenize text into words.
        
        Args:
            text: Input text
            
        Returns:
            List of tokens
        """
        # Remove punctuation, lowercase, split on whitespace
        text = re.sub(r'[^\w\s]', ' ', text.lower())
        return text.split()


class VectorDB:
    """Simple vector database for similarity search.
    
    Implements cosine similarity search over stored vectors.
    For production use, consider using FAISS, Pinecone, or Weaviate.
    
    Attributes:
        dim: Vector dimension
        vectors: List of stored vectors
        memories: List of corresponding memories
    
    Example:
        >>> db = VectorDB(dim=128)
        >>> db.add(embedding, memory)
        >>> results = db.search(query_embedding, k=5)
    """
    
    def __init__(self, dim: int = DEFAULT_EMBEDDING_DIM):
        """Initialize vector database.
        
        Args:
            dim: Vector dimension
        """
        if dim <= 0:
            raise ValueError(f"Dimension must be positive, got {dim}")
        
        self.dim = dim
        self.vectors: List[np.ndarray] = []
        self.memories: List[Memory] = []
        logger.info(f"Initialized VectorDB with dim={dim}")
    
    def add(self, embedding: List[float], memory: Memory) -> None:
        """Add vector and memory to database.
        
        Args:
            embedding: Embedding vector
            memory: Associated memory
            
        Raises:
            ValueError: If embedding dimension doesn't match
        """
        if len(embedding) != self.dim:
            raise ValueError(
                f"Embedding dimension mismatch: expected {self.dim}, got {len(embedding)}"
            )
        
        try:
            self.vectors.append(np.array(embedding))
            self.memories.append(memory)
            logger.debug(f"Added memory {memory.id} to VectorDB")
        except Exception as e:
            logger.error(f"Error adding to VectorDB: {e}")
            raise
    
    def search(
        self, 
        query_embedding: List[float], 
        k: int = 5,
        min_similarity: float = MIN_SIMILARITY_THRESHOLD
    ) -> List[Memory]:
        """Search for similar memories using cosine similarity.
        
        Args:
            query_embedding: Query vector
            k: Number of results to return
            min_similarity: Minimum similarity threshold
            
        Returns:
            List of top-k similar memories
            
        Raises:
            ValueError: If query dimension doesn't match
        """
        if not self.vectors:
            return []
        
        if len(query_embedding) != self.dim:
            raise ValueError(
                f"Query dimension mismatch: expected {self.dim}, got {len(query_embedding)}"
            )
        
        try:
            query_vec = np.array(query_embedding)
            
            # Calculate cosine similarities
            similarities = []
            for vec in self.vectors:
                sim = np.dot(query_vec, vec) / (
                    np.linalg.norm(query_vec) * np.linalg.norm(vec) + 1e-8
                )
                similarities.append(sim)
            
            # Get top-k indices above threshold
            top_k_indices = np.argsort(similarities)[-k:][::-1]
            results = [
                self.memories[i] 
                for i in top_k_indices 
                if similarities[i] > min_similarity
            ]
            
            logger.debug(f"Search returned {len(results)} results")
            return results
            
        except Exception as e:
            logger.error(f"Error searching VectorDB: {e}")
            raise
    
    def save(self, path: Path) -> None:
        """Save database to JSON file.
        
        Args:
            path: Output file path
            
        Raises:
            IOError: If file cannot be written
        """
        try:
            data = {
                "vectors": [v.tolist() for v in self.vectors],
                "memories": [m.to_dict() for m in self.memories]
            }
            
            path.parent.mkdir(parents=True, exist_ok=True)
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"Saved VectorDB to {path}")
            
        except Exception as e:
            logger.error(f"Error saving VectorDB: {e}")
            raise IOError(f"Failed to save VectorDB: {e}")
    
    def load(self, path: Path) -> None:
        """Load database from JSON file.
        
        Args:
            path: Input file path
            
        Raises:
            IOError: If file cannot be read
            ValueError: If data format is invalid
        """
        if not path.exists():
            logger.warning(f"VectorDB file not found: {path}")
            return
        
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            self.vectors = [np.array(v) for v in data["vectors"]]
            self.memories = [Memory.from_dict(m) for m in data["memories"]]
            
            logger.info(f"Loaded {len(self.memories)} memories from {path}")
            
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in VectorDB file: {e}")
            raise ValueError(f"Invalid JSON format: {e}")
        except Exception as e:
            logger.error(f"Error loading VectorDB: {e}")
            raise IOError(f"Failed to load VectorDB: {e}")


class MemoryManager:
    """Memory management system with hierarchical storage.
    
    Manages three tiers of memory:
    - Short-term: Recent memories (limited size)
    - Long-term: Important memories (persistent, vector-indexed)
    - Working: Task-specific temporary memories
    
    Attributes:
        workspace: Workspace directory path
        config: Memory configuration
        short_term: List of short-term memories
        long_term: Vector database for long-term memories
        working: Dictionary of task-specific memories
        embedding: Embedding model
    
    Example:
        >>> manager = MemoryManager(Path("/workspace"))
        >>> memory = manager.store("Implemented feature X", importance=0.9)
        >>> results = manager.retrieve("feature X", k=5)
    """
    
    def __init__(
        self, 
        workspace: Path, 
        config: Optional[MemoryConfig] = None
    ):
        """Initialize memory manager.
        
        Args:
            workspace: Workspace directory path
            config: Optional memory configuration
        """
        self.workspace = Path(workspace)
        self.config = config or MemoryConfig()
        self.memory_dir = self.workspace / "memory"
        self.memory_dir.mkdir(parents=True, exist_ok=True)
        
        # Three-tier memory
        self.short_term: List[Memory] = []
        self.long_term = VectorDB(self.config.embedding_dim)
        self.working: Dict[str, List[Memory]] = {}
        
        # Embedding model
        self.embedding = SimpleEmbedding(self.config.embedding_dim)
        
        # Load long-term memory
        self._load_long_term()
        
        # Initialize embedding if needed
        if not self.long_term.memories:
            self._init_embedding()
        
        logger.info(f"Initialized MemoryManager at {workspace}")
    
    def _load_long_term(self) -> None:
        """Load long-term memory from disk."""
        db_file = self.memory_dir / "long_term.json"
        try:
            self.long_term.load(db_file)
        except Exception as e:
            logger.error(f"Failed to load long-term memory: {e}")
    
    def _save_long_term(self) -> None:
        """Save long-term memory to disk."""
        db_file = self.memory_dir / "long_term.json"
        try:
            self.long_term.save(db_file)
        except Exception as e:
            logger.error(f"Failed to save long-term memory: {e}")
    
    def _init_embedding(self) -> None:
        """Initialize embedding model from MEMORY.md.
        
        Trains the embedding model on existing memory content
        and imports it into long-term storage.
        """
        memory_md = self.workspace / "MEMORY.md"
        if not memory_md.exists():
            logger.warning("MEMORY.md not found, skipping embedding initialization")
            return
        
        try:
            with open(memory_md, "r", encoding="utf-8") as f:
                content = f.read()
            
            # Split into paragraphs
            paragraphs = [
                p.strip() 
                for p in content.split("\n\n") 
                if p.strip() and len(p.strip()) > MIN_PARAGRAPH_LENGTH
            ]
            
            if not paragraphs:
                logger.warning("No valid paragraphs found in MEMORY.md")
                return
            
            # Train embedding
            self.embedding.fit(paragraphs)
            
            # Import into long-term memory
            for para in paragraphs:
                memory = Memory(
                    id="",
                    content=para,
                    type=MemoryType.LONG_TERM.value,
                    importance=0.8,
                    timestamp=time.time(),
                    source=MemorySource.SYSTEM.value,
                    metadata={"source_file": "MEMORY.md"}
                )
                embedding = self.embedding.encode(para)
                memory.embedding = embedding
                self.long_term.add(embedding, memory)
            
            self._save_long_term()
            logger.info(f"Initialized embedding with {len(paragraphs)} paragraphs from MEMORY.md")
            
        except Exception as e:
            logger.error(f"Error initializing embedding: {e}")
    
    def store(
        self, 
        content: str, 
        source: str = MemorySource.USER.value,
        importance: Optional[float] = None, 
        metadata: Optional[Dict] = None
    ) -> Memory:
        """Store a new memory.
        
        Automatically determines memory tier based on importance:
        - importance > threshold: Long-term (persistent)
        - importance <= threshold: Short-term (temporary)
        
        Args:
            content: Memory content
            source: Memory source (user/agent/system)
            importance: Optional importance score (auto-calculated if None)
            metadata: Optional metadata dictionary
            
        Returns:
            Created memory object
            
        Raises:
            ValueError: If content is empty
        
        Example:
            >>> memory = manager.store(
            ...     "Implemented Planning module",
            ...     source="agent",
            ...     importance=0.9,
            ...     metadata={"project": "AIOS"}
            ... )
        """
        if not content or not content.strip():
            raise ValueError("Memory content cannot be empty")
        
        try:
            # Calculate importance if not provided
            if importance is None:
                importance = self._calculate_importance(content)
            
            # Create memory
            memory = Memory(
                id="",
                content=content,
                type=MemoryType.SHORT_TERM.value,
                importance=importance,
                timestamp=time.time(),
                source=source,
                metadata=metadata or {}
            )
            
            # Add to short-term memory
            self.short_term.append(memory)
            
            # Promote to long-term if important
            if importance > self.config.importance_threshold:
                embedding = self.embedding.encode(content)
                memory.embedding = embedding
                memory.type = MemoryType.LONG_TERM.value
                self.long_term.add(embedding, memory)
                self._save_long_term()
                logger.info(f"Promoted memory {memory.id} to long-term storage")
            
            # Limit short-term memory size
            if len(self.short_term) > self.config.short_term_limit:
                self.short_term = self.short_term[-self.config.short_term_limit:]
            
            logger.debug(f"Stored memory {memory.id} (importance={importance:.2f})")
            return memory
            
        except Exception as e:
            logger.error(f"Error storing memory: {e}")
            raise
    
    def retrieve(
        self, 
        query: str, 
        k: int = 5,
        include_short_term: bool = True
    ) -> List[Memory]:
        """Retrieve relevant memories by semantic search.
        
        Searches both long-term (vector search) and short-term (recent)
        memories, then deduplicates and ranks by importance.
        
        Args:
            query: Search query
            k: Number of results to return
            include_short_term: Whether to include short-term memories
            
        Returns:
            List of relevant memories (up to k)
            
        Raises:
            ValueError: If query is empty
        
        Example:
            >>> results = manager.retrieve("Planning module", k=5)
            >>> for mem in results:
            ...     print(f"{mem.content[:50]}... (importance={mem.importance})")
        """
        if not query or not query.strip():
            raise ValueError("Query cannot be empty")
        
        try:
            results = []
            
            # 1. Vector search in long-term memory
            query_embedding = self.embedding.encode(query)
            long_term_results = self.long_term.search(
                query_embedding, 
                k=k,
                min_similarity=self.config.min_similarity
            )
            results.extend(long_term_results)
            
            # 2. Recent short-term memories
            if include_short_term:
                results.extend(self.short_term[-10:])
            
            # 3. Deduplicate and rank by importance
            seen = set()
            unique_results = []
            for mem in results:
                if mem.id not in seen:
                    seen.add(mem.id)
                    unique_results.append(mem)
            
            unique_results.sort(key=lambda m: m.importance, reverse=True)
            
            logger.debug(f"Retrieved {len(unique_results[:k])} memories for query: {query[:50]}")
            return unique_results[:k]
            
        except Exception as e:
            logger.error(f"Error retrieving memories: {e}")
            raise
    
    def store_working(
        self, 
        task_id: str, 
        content: str,
        metadata: Optional[Dict] = None
    ) -> Memory:
        """Store working memory for a specific task.
        
        Working memories are temporary and task-specific.
        They are automatically cleared when the task completes.
        
        Args:
            task_id: Task identifier
            content: Memory content
            metadata: Optional metadata
            
        Returns:
            Created memory object
            
        Raises:
            ValueError: If task_id or content is empty
        
        Example:
            >>> memory = manager.store_working(
            ...     "task_123",
            ...     "Started implementing feature X"
            ... )
        """
        if not task_id or not task_id.strip():
            raise ValueError("Task ID cannot be empty")
        if not content or not content.strip():
            raise ValueError("Memory content cannot be empty")
        
        try:
            memory = Memory(
                id="",
                content=content,
                type=MemoryType.WORKING.value,
                importance=0.5,
                timestamp=time.time(),
                source=MemorySource.AGENT.value,
                metadata=metadata or {"task_id": task_id}
            )
            
            if task_id not in self.working:
                self.working[task_id] = []
            
            self.working[task_id].append(memory)
            logger.debug(f"Stored working memory for task {task_id}")
            return memory
            
        except Exception as e:
            logger.error(f"Error storing working memory: {e}")
            raise
    
    def get_working(self, task_id: str) -> List[Memory]:
        """Get all working memories for a task.
        
        Args:
            task_id: Task identifier
            
        Returns:
            List of working memories
        """
        return self.working.get(task_id, [])
    
    def clear_working(self, task_id: str) -> None:
        """Clear working memories for a task.
        
        Args:
            task_id: Task identifier
        """
        if task_id in self.working:
            del self.working[task_id]
            logger.debug(f"Cleared working memory for task {task_id}")
    
    def consolidate(self) -> Dict[str, int]:
        """Consolidate memories (periodic maintenance).
        
        Performs the following operations:
        1. Promotes important short-term memories to long-term
        2. Trims short-term memory to size limit
        3. Saves long-term memory to disk
        4. Updates MEMORY.md with recent important memories
        
        Returns:
            Statistics dictionary with counts
        
        Example:
            >>> stats = manager.consolidate()
            >>> print(f"Promoted {stats['promoted']} memories to long-term")
        """
        try:
            promoted = 0
            
            # 1. Promote important short-term memories
            for memory in self.short_term:
                if (memory.importance > self.config.importance_threshold 
                    and memory.type == MemoryType.SHORT_TERM.value):
                    embedding = self.embedding.encode(memory.content)
                    memory.embedding = embedding
                    memory.type = MemoryType.LONG_TERM.value
                    self.long_term.add(embedding, memory)
                    promoted += 1
            
            # 2. Trim short-term memory
            original_count = len(self.short_term)
            self.short_term = self.short_term[-self.config.short_term_limit:]
            trimmed = original_count - len(self.short_term)
            
            # 3. Save long-term memory
            self._save_long_term()
            
            # 4. Update MEMORY.md
            self._update_memory_md()
            
            stats = {
                "promoted": promoted,
                "trimmed": trimmed,
                "short_term_count": len(self.short_term),
                "long_term_count": len(self.long_term.memories)
            }
            
            logger.info(f"Consolidation complete: {stats}")
            return stats
            
        except Exception as e:
            logger.error(f"Error during consolidation: {e}")
            raise
    
    def _calculate_importance(self, content: str) -> float:
        """Calculate importance score for content.
        
        Uses simple heuristics:
        - Length bonus (longer = more important)
        - Keyword matching (technical terms)
        
        Args:
            content: Memory content
            
        Returns:
            Importance score (0.0 - 1.0)
        """
        importance = 0.5  # Base score
        
        # Length bonus
        if len(content) > 100:
            importance += 0.1
        if len(content) > 500:
            importance += 0.1
        
        # Keyword bonus
        keywords = [
            "重要", "关键", "核心", "突破", "成功", "失败", "教训",
            "决策", "方案", "架构", "设计", "实现", "优化",
            "important", "critical", "key", "breakthrough", "success",
            "failure", "lesson", "decision", "architecture", "design"
        ]
        
        content_lower = content.lower()
        for kw in keywords:
            if kw in content_lower:
                importance += 0.05
        
        return min(importance, 1.0)
    
    def _update_memory_md(self) -> None:
        """Update MEMORY.md with recent important memories.
        
        Extracts recent high-importance memories and appends them
        to MEMORY.md in a structured format.
        """
        memory_md = self.workspace / "MEMORY.md"
        
        try:
            # Read existing content
            existing_content = ""
            if memory_md.exists():
                with open(memory_md, "r", encoding="utf-8") as f:
                    existing_content = f.read()
            
            # Get recent important memories
            cutoff_time = time.time() - (self.config.consolidation_days * 24 * 3600)
            recent_important = [
                m for m in self.long_term.memories
                if m.timestamp > cutoff_time and m.importance > 0.8
            ]
            
            if not recent_important:
                return
            
            # Sort by timestamp (newest first)
            recent_important.sort(key=lambda m: m.timestamp, reverse=True)
            
            # Generate new section
            new_section = "\n\n## 最近更新（自动生成）\n\n"
            for mem in recent_important[:MAX_RECENT_UPDATES]:
                date = datetime.fromtimestamp(mem.timestamp).strftime("%Y-%m-%d")
                new_section += f"### {date}\n\n{mem.content}\n\n"
            
            # Append if not already present
            if new_section not in existing_content:
                with open(memory_md, "a", encoding="utf-8") as f:
                    f.write(new_section)
                logger.info(f"Updated MEMORY.md with {len(recent_important[:MAX_RECENT_UPDATES])} recent memories")
                
        except Exception as e:
            logger.error(f"Error updating MEMORY.md: {e}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get memory statistics.
        
        Returns:
            Dictionary with memory counts and metrics
        
        Example:
            >>> stats = manager.get_stats()
            >>> print(f"Total memories: {stats['total_memories']}")
        """
        try:
            long_term_importances = [m.importance for m in self.long_term.memories]
            
            return {
                "short_term_count": len(self.short_term),
                "long_term_count": len(self.long_term.memories),
                "working_tasks": len(self.working),
                "total_memories": len(self.short_term) + len(self.long_term.memories),
                "avg_importance": (
                    np.mean(long_term_importances) 
                    if long_term_importances 
                    else 0.0
                )
            }
        except Exception as e:
            logger.error(f"Error getting stats: {e}")
            return {}


def demo():
    """Demonstrate Memory module functionality."""
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    workspace = Path(__file__).parent.parent.parent
    manager = MemoryManager(workspace)
    
    print("=== AIOS Memory Module Demo ===\n")
    
    # Test 1: Store memories
    print("Test 1: Store memories")
    mem1 = manager.store(
        "Implemented Planning module with CoT task decomposition",
        importance=0.9,
        metadata={"project": "AIOS", "module": "Planning"}
    )
    mem2 = manager.store("Fixed a minor bug", importance=0.3)
    mem3 = manager.store(
        "Designed Memory module architecture with vector retrieval and memory tiers",
        importance=0.9,
        metadata={"project": "AIOS", "module": "Memory"}
    )
    print(f"Stored 3 memories")
    print(f"- Memory 1: {mem1.content[:40]}... (importance: {mem1.importance})")
    print(f"- Memory 2: {mem2.content[:40]}... (importance: {mem2.importance})")
    print(f"- Memory 3: {mem3.content[:40]}... (importance: {mem3.importance})")
    print()
    
    # Test 2: Retrieve memories
    print("Test 2: Retrieve memories")
    query = "Planning module"
    results = manager.retrieve(query, k=3)
    print(f"Query: {query}")
    print(f"Found {len(results)} relevant memories:")
    for i, mem in enumerate(results):
        print(f"  {i+1}. {mem.content[:50]}... (importance: {mem.importance:.2f})")
    print()
    
    # Test 3: Working memory
    print("Test 3: Working memory")
    task_id = "task_123"
    manager.store_working(task_id, "Started designing Memory module")
    manager.store_working(task_id, "Completed vector retrieval implementation")
    working_mems = manager.get_working(task_id)
    print(f"Working memories for task {task_id}:")
    for mem in working_mems:
        print(f"  - {mem.content}")
    print()
    
    # Test 4: Statistics
    print("Test 4: Statistics")
    stats = manager.get_stats()
    print(f"Short-term memories: {stats['short_term_count']}")
    print(f"Long-term memories: {stats['long_term_count']}")
    print(f"Working tasks: {stats['working_tasks']}")
    print(f"Total memories: {stats['total_memories']}")
    print(f"Average importance: {stats['avg_importance']:.2f}")
    print()
    
    # Test 5: Consolidation
    print("Test 5: Consolidation")
    consolidation_stats = manager.consolidate()
    print(f"Promoted: {consolidation_stats['promoted']}")
    print(f"Trimmed: {consolidation_stats['trimmed']}")
    print(f"Short-term count: {consolidation_stats['short_term_count']}")
    print(f"Long-term count: {consolidation_stats['long_term_count']}")
    print()
    
    print("[OK] Demo complete!")


if __name__ == "__main__":
    demo()

