"""
Pickle-based caching for PaperQA Docs objects.

This module provides persistence for indexed documents to improve startup performance.
Instead of rebuilding the index on every startup, we cache the Docs object as a pickle file.
"""

import pickle
import hashlib
import logging
from pathlib import Path
from typing import Optional, Tuple
from datetime import datetime

logger = logging.getLogger(__name__)


def get_docs_dir_hash(docs_dir: str) -> str:
    """
    Calculate a hash of all documents in a directory.
    
    This is used to invalidate the cache if documents have changed.
    
    Args:
        docs_dir: Directory containing documents
        
    Returns:
        Hex hash string representing the current state of documents
    """
    docs_path = Path(docs_dir)
    hash_obj = hashlib.md5()
    
    if not docs_path.exists():
        return hash_obj.hexdigest()
    
    # Get all PDF and TXT files, sorted for consistency
    doc_files = sorted(
        list(docs_path.rglob("*.pdf")) + list(docs_path.rglob("*.txt"))
    )
    
    if not doc_files:
        return hash_obj.hexdigest()
    
    # Hash each file's path and modification time
    for file_path in doc_files:
        try:
            # Include file path and modification time in hash
            file_stat = file_path.stat()
            file_info = f"{file_path}:{file_stat.st_mtime}:{file_stat.st_size}"
            hash_obj.update(file_info.encode())
        except OSError as e:
            logger.warning(f"Could not stat file {file_path}: {e}")
    
    return hash_obj.hexdigest()


def save_docs_cache(docs_obj, cache_path: str, docs_dir: str) -> bool:
    """
    Save a PaperQA Docs object to a pickle file with metadata.
    
    Args:
        docs_obj: PaperQA Docs object to cache
        cache_path: Path where to save the pickle file
        docs_dir: Directory containing documents (for hash validation)
        
    Returns:
        True if save was successful, False otherwise
    """
    try:
        cache_file = Path(cache_path)
        cache_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Calculate current docs directory hash
        docs_hash = get_docs_dir_hash(docs_dir)
        
        # Create cache metadata
        cache_data = {
            'docs': docs_obj,
            'docs_hash': docs_hash,
            'timestamp': datetime.now().isoformat(),
            'docs_dir': docs_dir,
            'version': 1  # Cache format version for future compatibility
        }
        
        # Save to pickle file
        with open(cache_file, 'wb') as f:
            pickle.dump(cache_data, f, protocol=pickle.HIGHEST_PROTOCOL)
        
        logger.info(f"Docs cache saved to {cache_path}")
        logger.info(f"   Cache hash: {docs_hash[:8]}...")
        logger.info(f"   Timestamp: {cache_data['timestamp']}")
        
        return True
        
    except Exception as e:
        logger.error(f"Failed to save docs cache: {e}")
        return False


def load_docs_cache(cache_path: str, docs_dir: str) -> Tuple[Optional[object], bool]:
    """
    Load a PaperQA Docs object from a pickle file with validation.
    
    Args:
        cache_path: Path to the pickle file
        docs_dir: Directory containing documents (for hash validation)
        
    Returns:
        Tuple of (Docs object or None, is_valid)
        - Docs object if cache is valid and loaded successfully
        - None if cache doesn't exist, is invalid, or loading failed
        - is_valid indicates whether the cache matched current documents
    """
    try:
        cache_file = Path(cache_path)
        
        if not cache_file.exists():
            logger.debug(f"Cache file not found: {cache_path}. Creating new cache file.")
            return None, False
        
        with open(cache_file, 'rb') as f:
            cache_data = pickle.load(f)
        
        if not isinstance(cache_data, dict) or 'docs' not in cache_data:
            logger.warning("Cache file has invalid format")
            return None, False
        
        version = cache_data.get('version', 1)
        if version != 1:
            logger.warning(f"Cache version mismatch: {version} (expected 1)")
            return None, False
        
        cached_docs_dir = cache_data.get('docs_dir', '')
        if cached_docs_dir != docs_dir:
            logger.warning(
                f"Cache docs_dir mismatch: {cached_docs_dir} != {docs_dir}"
            )
            return None, False
        
        current_hash = get_docs_dir_hash(docs_dir)
        cached_hash = cache_data.get('docs_hash', '')
        
        if current_hash != cached_hash:
            logger.info("Documents have changed, cache is stale")
            logger.debug(f"Cached hash:  {cached_hash}")
            logger.debug(f"Current hash: {current_hash}")
            docs_obj = cache_data['docs']
            return docs_obj, False  # Return docs but mark as invalid
        
        docs_obj = cache_data['docs']
        timestamp = cache_data.get('timestamp', 'unknown')
        logger.info(f"Docs cache loaded successfully from {cache_path}")
        logger.info(f"Cache hash: {cached_hash[:8]}...")
        logger.info(f"Timestamp: {timestamp}")
        logger.info(f"Document count: {len(docs_obj.docs) if hasattr(docs_obj, 'docs') else 'unknown'}")
        
        return docs_obj, True
        
    except pickle.UnpicklingError as e:
        logger.error(f"Pickle unpickling error: {e}")
        return None, False
    except Exception as e:
        logger.error(f"Failed to load docs cache: {e}")
        return None, False


def clear_docs_cache(cache_path: str) -> bool:
    """
    Delete the cache file.
    
    Args:
        cache_path: Path to the cache file
        
    Returns:
        True if deletion was successful, False otherwise
    """
    try:
        cache_file = Path(cache_path)
        if cache_file.exists():
            cache_file.unlink()
            logger.info(f"Docs cache cleared: {cache_path}")
            return True
        else:
            logger.debug(f"Cache file not found (nothing to clear): {cache_path}")
            return True
    except Exception as e:
        logger.error(f"Failed to clear docs cache: {e}")
        return False


def get_cache_info(cache_path: str) -> Optional[dict]:
    """
    Get metadata about a cache file without loading the full Docs object.
    
    Args:
        cache_path: Path to the cache file
        
    Returns:
        Dictionary with cache metadata or None if file doesn't exist/invalid
    """
    try:
        cache_file = Path(cache_path)
        
        if not cache_file.exists():
            return None
        
        with open(cache_file, 'rb') as f:
            cache_data = pickle.load(f)
        
        return {
            'timestamp': cache_data.get('timestamp', 'unknown'),
            'docs_dir': cache_data.get('docs_dir', 'unknown'),
            'docs_hash': cache_data.get('docs_hash', 'unknown'),
            'version': cache_data.get('version', 'unknown'),
            'file_size': cache_file.stat().st_size,
            'file_path': str(cache_file)
        }
    except Exception as e:
        logger.debug(f"Could not get cache info: {e}")
        return None

