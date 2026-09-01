import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.config import settings
from app.core.redis import cache_set, cache_get, get_redis_client

print("==================================================")
print("NOVA AI Cache Verification & Fallback Demo")
print("==================================================")
print(f"Active Environment: {settings.ENV_MODE}")
print(f"Configured Redis URL: {settings.REDIS_URL}")

# Check Redis connection pool availability
client = get_redis_client()
if client:
    print("Redis Connection: ONLINE (Direct Redis client operations active)")
else:
    print("Redis Connection: OFFLINE (Local in-memory fallback active)")

# 1. Set value in cache
print("\n[Step 1] Setting cache key 'nova:demo:key' to 'working'...")
set_success = cache_set("nova:demo:key", "working", ttl_seconds=60)
print(f"Status: {'Success' if set_success else 'Failed'}")

# 2. Retrieve value from cache
print("\n[Step 2] Retrieving cache key 'nova:demo:key'...")
value = cache_get("nova:demo:key")
print(f"Retrieved Value: '{value}'")

# 3. Clean up cache
print("\n[Step 3] Deleting cache key 'nova:demo:key'...")
from app.core.redis import cache_delete
del_success = cache_delete("nova:demo:key")
print(f"Deleted: {'Success' if del_success else 'Failed'}")
print("==================================================")
