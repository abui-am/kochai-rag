# Docs Pickle Caching Guide

## Overview

The Fitness RAG system now includes **automatic pickle-based caching** for PaperQA `Docs` objects. This significantly speeds up system startup by avoiding redundant document indexing.

### Key Features

- ⚡ **Fast Startup**: Load cached indices in milliseconds instead of rebuilding them
- 🔄 **Automatic Invalidation**: Cache automatically detects when documents change
- 💾 **Efficient Storage**: Uses Python's pickle protocol for optimal serialization
- 🛡️ **Backwards Compatible**: Gracefully falls back if cache is unavailable
- 📊 **Introspection**: Query cache status without loading full index

---

## How It Works

### Initialization Flow

```
FitnessKnowledgeSystem startup:
  1. Check if cache exists and is valid
     ✅ Valid → Load from pickle (fast)
     ❌ Invalid/Missing → Rebuild index (slow)
  2. After building, save to pickle cache
  3. Future startups use the cached version
```

### Cache Validation

The cache is considered **valid** if:

- Cache file exists
- Documents directory hash matches
- Cache metadata is intact
- Cache version is compatible

The cache is **invalid** if:

- Documents have been added/modified/removed
- Document modification times changed
- Cache file is corrupted
- Cache format version mismatch

---

## Usage

### Basic Setup (Automatic)

The cache is enabled by default:

```python
from rag.agentic_workflow import create_fitness_knowledge_system

# Cache automatically saved to ./.cache/docs_index.pkl
system = await create_fitness_knowledge_system(
    docs_dir="./data/sources/processed",
    auto_index=True  # Will use cache if available
)
```

### Custom Cache Directory

```python
# Specify custom cache location
system = await create_fitness_knowledge_system(
    docs_dir="./data/sources/processed",
    cache_dir="./my_cache_dir",  # Custom cache location
    auto_index=True
)
```

### Direct Class Usage

```python
from rag.agentic_workflow import FitnessKnowledgeSystem

# Create with custom cache directory
system = FitnessKnowledgeSystem(
    docs_dir="./data/sources/processed",
    cache_dir="./.cache",
    auto_index=True
)

# Build index (uses cache if valid)
await system.build_index()
```

### Cache Management

```python
# Get cache info without loading full Docs
cache_info = system.get_cache_info()
print(cache_info)
# Output:
# {
#   'timestamp': '2024-11-05T10:30:45.123456',
#   'docs_dir': './data/sources/processed',
#   'docs_hash': 'abc123def456...',
#   'version': 1,
#   'file_size': 157286400,  # bytes
#   'file_path': './.cache/docs_index.pkl'
# }

# Get comprehensive system status
status = system.get_cache_status()
print(status)
# Output:
# {
#   'index_built': True,
#   'cache_exists': True,
#   'cache_info': {...},
#   'cache_path': './.cache/docs_index.pkl',
#   'docs_dir': './data/sources/processed',
#   'document_count': 42,
#   'has_cached_docs': True
# }

# Clear cache (will rebuild on next startup)
system.clear_cache()
```

---

## Performance Impact

### Startup Times (Example)

**Without Cache** (rebuild every time):

- Initial index build: ~45-60 seconds
- Subsequent startups: ~45-60 seconds (always rebuilds)

**With Cache** (first run):

- Initial index build: ~45-60 seconds
- Cache save: ~2-3 seconds
- Total: ~50-63 seconds

**With Cache** (subsequent runs):

- Cache load: ~500ms - 2 seconds
- Speedup: **20-60x faster** ⚡

### Storage Requirements

- Pickled Docs object size depends on document count and complexity
- Typical 50-document index: ~100-200 MB
- Monitor `.cache/` directory for usage

---

## API Reference

### `FitnessKnowledgeSystem`

#### Constructor Parameters

```python
FitnessKnowledgeSystem(
    docs_dir: str = "./data/sources/processed",
    openai_api_key: str = None,
    auto_index: bool = True,
    cache_dir: str = "./.cache"
)
```

**Parameters:**

- `docs_dir`: Directory containing documents
- `openai_api_key`: OpenAI API key for LLM operations
- `auto_index`: Whether to build index automatically
- `cache_dir`: Directory for pickle cache files

#### Methods

##### `async build_index() -> bool`

Builds the index, using cache if valid. Returns True on success.

```python
success = await system.build_index()
if success:
    print("Index ready!")
```

##### `clear_cache() -> bool`

Deletes the cache file. Returns True if successful.

```python
system.clear_cache()
# Index will rebuild on next build_index() call
```

##### `get_cache_info() -> Optional[dict]`

Returns cache metadata without loading full Docs object.

```python
info = system.get_cache_info()
if info:
    print(f"Cache created at: {info['timestamp']}")
```

##### `get_cache_status() -> dict`

Returns comprehensive system and cache status.

```python
status = system.get_cache_status()
print(f"Documents: {status['document_count']}")
print(f"Cache exists: {status['cache_exists']}")
```

---

## Cache Module (`rag/docs_cache.py`)

### Low-Level Functions

#### `get_docs_dir_hash(docs_dir: str) -> str`

Calculates MD5 hash of all documents for change detection.

```python
from rag.docs_cache import get_docs_dir_hash

hash1 = get_docs_dir_hash("./data/sources/processed")
# Use for cache validation
```

#### `save_docs_cache(docs_obj, cache_path: str, docs_dir: str) -> bool`

Saves Docs object to pickle file with metadata.

```python
from rag.docs_cache import save_docs_cache

success = save_docs_cache(
    docs_object,
    "./.cache/docs_index.pkl",
    "./data/sources/processed"
)
```

#### `load_docs_cache(cache_path: str, docs_dir: str) -> Tuple[Optional[object], bool]`

Loads Docs from pickle with validation.

```python
from rag.docs_cache import load_docs_cache

docs, is_valid = load_docs_cache(
    "./.cache/docs_index.pkl",
    "./data/sources/processed"
)

if is_valid:
    print("Cache is current, using it")
else:
    print("Cache is stale, rebuild needed")
```

#### `clear_docs_cache(cache_path: str) -> bool`

Deletes cache file.

```python
from rag.docs_cache import clear_docs_cache

clear_docs_cache("./.cache/docs_index.pkl")
```

#### `get_cache_info(cache_path: str) -> Optional[dict]`

Reads cache metadata without full deserialization.

```python
from rag.docs_cache import get_cache_info

info = get_cache_info("./.cache/docs_index.pkl")
if info:
    print(f"File size: {info['file_size']} bytes")
```

---

## Testing

Run the cache test suite:

```bash
python test_cache.py
```

This tests:

- Cache creation and loading
- Hash-based invalidation
- Directory monitoring
- Performance comparison
- Cache clearing

---

## Best Practices

### ✅ Do

- Enable caching in production for faster startups
- Clear cache if you want fresh embeddings
- Monitor cache file size periodically
- Use `get_cache_info()` for quick status checks
- Commit `.gitignore` to exclude `.cache/` from version control

### ❌ Don't

- Manually edit pickle files (they're binary)
- Copy cache between different PaperQA versions (may cause issues)
- Rely on cache if you're developing document processing logic
- Delete cache without understanding the impact

---

## Troubleshooting

### Cache Not Loading

**Symptom:** Cache exists but not being used

**Solutions:**

1. Check cache file permissions
2. Verify `docs_dir` parameter matches
3. Look for version mismatch errors in logs
4. Clear cache: `system.clear_cache()`

### Stale Cache Issues

**Symptom:** Changes to documents not reflected

**Solutions:**

1. Cache automatically detects changes (via hash)
2. If not detected, manually clear: `system.clear_cache()`
3. Check if document modification times are current

### Out of Disk Space

**Symptom:** Disk full after caching

**Solutions:**

1. Check cache size: `ls -lh .cache/`
2. Clear if not needed: `rm -rf .cache/`
3. Use custom `cache_dir` on larger disk

### Pickle Corruption

**Symptom:** "Unpickling error" in logs

**Solutions:**

1. This is non-fatal (cache loads anyway)
2. Automatically triggers rebuild
3. Clear cache if persistent: `system.clear_cache()`

---

## Future Enhancements

Potential improvements to consider:

- [ ] Configurable hash algorithms
- [ ] Compression for pickled cache
- [ ] Cache versioning strategy
- [ ] Multi-document cache indices
- [ ] Cache statistics/analytics
- [ ] Distributed cache support

---

## Files Modified

- `rag/agentic_workflow.py`: Added caching integration to `FitnessKnowledgeSystem`
- `rag/docs_cache.py`: New module with cache functions
- `api/main.py`: Updated to support cache parameters (if needed)

---

For more information, see the main [README.md](README.md) or check the source code comments.
