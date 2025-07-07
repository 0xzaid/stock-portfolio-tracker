import json
import os
import time
from typing import Any, Optional
from datetime import datetime, timedelta

class CacheManager:
    """
    Simple file-based cache manager for API responses
    Helps avoid unnecessary API calls and rate limiting
    """
    
    def __init__(self, cache_dir: str = "data/cache"):
        self.cache_dir = cache_dir
        os.makedirs(cache_dir, exist_ok=True)
    
    def _get_cache_path(self, key: str) -> str:
        """Get file path for cache key"""
        # Sanitize key for filename
        safe_key = key.replace('/', '_').replace('\\', '_').replace(':', '_')
        return os.path.join(self.cache_dir, f"{safe_key}.json")
    
    def set(self, key: str, value: Any, ttl: int = 3600) -> bool:
        """
        Store value in cache with TTL (time to live) in seconds
        Default TTL: 1 hour
        """
        try:
            cache_data = {
                'value': value,
                'timestamp': time.time(),
                'ttl': ttl,
                'expires_at': time.time() + ttl
            }
            
            cache_path = self._get_cache_path(key)
            with open(cache_path, 'w') as f:
                json.dump(cache_data, f, indent=2, default=str)
            
            return True
            
        except Exception as e:
            print(f"⚠️ Cache write error for {key}: {e}")
            return False
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache if not expired"""
        try:
            cache_path = self._get_cache_path(key)
            
            if not os.path.exists(cache_path):
                return None
            
            with open(cache_path, 'r') as f:
                cache_data = json.load(f)
            
            # Check if expired
            current_time = time.time()
            if current_time > cache_data.get('expires_at', 0):
                # Clean up expired file
                try:
                    os.remove(cache_path)
                except:
                    pass
                return None
            
            return cache_data['value']
            
        except Exception as e:
            print(f"⚠️ Cache read error for {key}: {e}")
            return None
    
    def delete(self, key: str) -> bool:
        """Delete specific cache entry"""
        try:
            cache_path = self._get_cache_path(key)
            if os.path.exists(cache_path):
                os.remove(cache_path)
            return True
        except Exception as e:
            print(f"⚠️ Cache delete error for {key}: {e}")
            return False
    
    def clear_expired(self) -> int:
        """Remove all expired cache entries"""
        removed_count = 0
        current_time = time.time()
        
        try:
            for filename in os.listdir(self.cache_dir):
                if filename.endswith('.json'):
                    file_path = os.path.join(self.cache_dir, filename)
                    
                    try:
                        with open(file_path, 'r') as f:
                            cache_data = json.load(f)
                        
                        if current_time > cache_data.get('expires_at', 0):
                            os.remove(file_path)
                            removed_count += 1
                            
                    except Exception:
                        # If we can't read the file, remove it
                        try:
                            os.remove(file_path)
                            removed_count += 1
                        except:
                            pass
        
        except Exception as e:
            print(f"⚠️ Cache cleanup error: {e}")
        
        return removed_count
    
    def clear_all(self) -> int:
        """Remove all cache entries"""
        removed_count = 0
        
        try:
            for filename in os.listdir(self.cache_dir):
                if filename.endswith('.json'):
                    file_path = os.path.join(self.cache_dir, filename)
                    try:
                        os.remove(file_path)
                        removed_count += 1
                    except:
                        pass
        except Exception as e:
            print(f"⚠️ Cache clear error: {e}")
        
        return removed_count
    
    def get_cache_stats(self) -> dict:
        """Get cache statistics"""
        stats = {
            'total_entries': 0,
            'expired_entries': 0,
            'valid_entries': 0,
            'total_size_bytes': 0,
            'cache_dir': self.cache_dir
        }
        
        current_time = time.time()
        
        try:
            for filename in os.listdir(self.cache_dir):
                if filename.endswith('.json'):
                    file_path = os.path.join(self.cache_dir, filename)
                    stats['total_entries'] += 1
                    
                    try:
                        # Get file size
                        stats['total_size_bytes'] += os.path.getsize(file_path)
                        
                        # Check if expired
                        with open(file_path, 'r') as f:
                            cache_data = json.load(f)
                        
                        if current_time > cache_data.get('expires_at', 0):
                            stats['expired_entries'] += 1
                        else:
                            stats['valid_entries'] += 1
                            
                    except Exception:
                        stats['expired_entries'] += 1
        
        except Exception as e:
            print(f"⚠️ Cache stats error: {e}")
        
        return stats
    
    def is_cached(self, key: str) -> bool:
        """Check if key exists and is not expired"""
        return self.get(key) is not None