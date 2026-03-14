# Memory Module - Refactored Version

## 🎯 Overview

This is the refactored version of AIOS Memory Module, meeting open-source project standards with:
- ✅ Complete error handling
- ✅ Full type annotations
- ✅ Detailed Google-style docstrings
- ✅ 33 unit tests (100% pass rate)
- ✅ 74% code coverage
- ✅ Configurable design
- ✅ Logging system

## 📦 Installation

```bash
# No additional dependencies required
# Uses only Python standard library + numpy
pip install numpy
```

## 🚀 Quick Start

```python
from pathlib import Path
from core.memory_refactored import MemoryManager, MemoryConfig

# Initialize with default config
workspace = Path("/path/to/workspace")
manager = MemoryManager(workspace)

# Or with custom config
config = MemoryConfig(
    embedding_dim=256,
    short_term_limit=50,
    importance_threshold=0.8
)
manager = MemoryManager(workspace, config)

# Store a memory
memory = manager.store(
    "Implemented Planning module with CoT",
    importance=0.9,
    metadata={"project": "AIOS", "module": "Planning"}
)

# Retrieve relevant memories
results = manager.retrieve("Planning module", k=5)
for mem in results:
    print(f"{mem.content[:50]}... (importance={mem.importance:.2f})")

# Working memory for tasks
task_id = "task_123"
manager.store_working(task_id, "Started implementation")
manager.store_working(task_id, "Completed feature X")
working_mems = manager.get_working(task_id)

# Consolidate memories (periodic maintenance)
stats = manager.consolidate()
print(f"Promoted {stats['promoted']} memories to long-term")

# Get statistics
stats = manager.get_stats()
print(f"Total memories: {stats['total_memories']}")
```

## 🏗️ Architecture

### Three-Tier Memory System

1. **Short-term Memory**
   - Recent memories (last 100 by default)
   - Fast access, no persistence
   - Automatically trimmed

2. **Long-term Memory**
   - Important memories (importance > 0.7)
   - Vector-indexed for semantic search
   - Persistent storage (JSON)

3. **Working Memory**
   - Task-specific temporary memories
   - Cleared when task completes
   - Useful for multi-step operations

### Components

```
MemoryManager
├── SimpleEmbedding (TF-IDF style)
├── VectorDB (cosine similarity search)
├── Memory (dataclass)
├── MemoryConfig (configuration)
└── MemoryType/MemorySource (enums)
```

## 🧪 Testing

```bash
# Run all tests
pytest tests/test_memory.py -v

# Run with coverage
pytest tests/test_memory.py --cov=core.memory_refactored --cov-report=html

# Run specific test class
pytest tests/test_memory.py::TestMemoryManager -v
```

## 📊 Configuration

```python
@dataclass
class MemoryConfig:
    embedding_dim: int = 128              # Embedding vector dimension
    short_term_limit: int = 100           # Max short-term memories
    importance_threshold: float = 0.7     # Threshold for long-term promotion
    consolidation_days: int = 7           # Days to look back for consolidation
    min_similarity: float = 0.1           # Min similarity for retrieval
```

## 🔍 API Reference

### MemoryManager

#### `__init__(workspace: Path, config: Optional[MemoryConfig] = None)`
Initialize memory manager.

#### `store(content: str, source: str = "user", importance: Optional[float] = None, metadata: Optional[Dict] = None) -> Memory`
Store a new memory. Automatically promotes to long-term if important.

#### `retrieve(query: str, k: int = 5, include_short_term: bool = True) -> List[Memory]`
Retrieve relevant memories by semantic search.

#### `store_working(task_id: str, content: str, metadata: Optional[Dict] = None) -> Memory`
Store working memory for a specific task.

#### `get_working(task_id: str) -> List[Memory]`
Get all working memories for a task.

#### `clear_working(task_id: str) -> None`
Clear working memories for a task.

#### `consolidate() -> Dict[str, int]`
Consolidate memories (periodic maintenance). Returns statistics.

#### `get_stats() -> Dict[str, Any]`
Get memory statistics.

### Memory

```python
@dataclass
class Memory:
    id: str                              # Unique ID (auto-generated)
    content: str                         # Memory content
    type: str                            # short_term/long_term/working
    importance: float                    # 0.0 - 1.0
    timestamp: float                     # Unix timestamp
    source: str                          # user/agent/system
    metadata: Dict[str, Any]             # Additional metadata
    embedding: Optional[List[float]]     # Embedding vector
```

## 🐛 Error Handling

All methods include proper error handling:

```python
try:
    memory = manager.store("Important note")
except ValueError as e:
    print(f"Invalid input: {e}")
except IOError as e:
    print(f"Storage error: {e}")
```

## 📝 Logging

Enable logging to see what's happening:

```python
import logging
logging.basicConfig(level=logging.INFO)

# Now you'll see logs like:
# INFO:core.memory_refactored:Initialized MemoryManager at /workspace
# INFO:core.memory_refactored:Promoted memory abc123 to long-term storage
```

## 🔄 Migration from Old Version

```python
# Old version
from core.memory import MemoryManager as OldMemoryManager

# New version
from core.memory_refactored import MemoryManager

# API is mostly compatible, but with better error handling
# and more configuration options
```

## 🤝 Contributing

See the main AIOS CONTRIBUTING.md for guidelines.

## 📄 License

Part of AIOS project. See main LICENSE file.

## 🙏 Acknowledgments

- Original implementation: 小九 + 珊瑚海
- Refactored for open source: 2026-03-14
- Test coverage: 74%
- Test pass rate: 100%
