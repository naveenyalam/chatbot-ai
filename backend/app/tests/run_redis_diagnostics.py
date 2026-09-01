import sys
import os
import time
import unittest
from unittest.mock import patch

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app.core.redis import (
    get_redis_client,
    cache_set,
    cache_get,
    cache_delete,
    cache_delete_pattern,
    _mem_cache
)

def run_diagnostics():
    print("==============================================")
    print("NOVA AI — Redis Functional Diagnostic Suite")
    print("==============================================")

    # 1. Connectivity Check
    client = get_redis_client()
    if not client:
        print("[FAIL] Redis Connectivity: Offline")
        return
    else:
        try:
            ping_res = client.ping()
            print(f"[PASS] Redis Connectivity: Online (PING -> {ping_res})")
        except Exception as exc:
            print(f"[FAIL] Redis PING failed: {exc}")
            return

    # 2. Caching API Functional Verification (Active Redis)
    print("\n--- 2. Cache API Operations (Redis Active) ---")
    test_key = "nova:test:diag_key"
    test_val = "diagnostic_payload_123"

    # Set key
    set_res = cache_set(test_key, test_val, ttl_seconds=10)
    print(f"cache_set('{test_key}', ...): {'PASS' if set_res else 'FAIL'}")

    # Get key
    get_res = cache_get(test_key)
    print(f"cache_get('{test_key}'): {'PASS' if get_res == test_val else 'FAIL'} (Value: {get_res})")

    # TTL Check
    ttl = client.ttl(test_key)
    print(f"Key TTL remaining: {ttl}s (Expected ~10s)")

    # Delete key
    del_res = cache_delete(test_key)
    print(f"cache_delete('{test_key}'): {'PASS' if del_res else 'FAIL'}")
    
    get_after_del = cache_get(test_key)
    print(f"Verify key deleted: {'PASS' if get_after_del is None else 'FAIL'} (Value: {get_after_del})")

    # 3. Cache Expiration
    print("\n--- 3. Expiration Verification ---")
    exp_key = "nova:test:exp_key"
    cache_set(exp_key, "temp_data", ttl_seconds=2)
    print("Set key with 2s TTL. Sleeping 3s...")
    time.sleep(3)
    get_exp = cache_get(exp_key)
    print(f"Verify key expired: {'PASS' if get_exp is None else 'FAIL'} (Value: {get_exp})")

    # 4. Fallback Verification (Simulated Offline Redis)
    print("\n--- 4. Graceful Offline Fallback Operations ---")
    
    # We patch get_redis_client to return None, simulating a socket/connection failure
    with patch("app.core.redis.get_redis_client", return_value=None):
        fallback_key = "nova:test:fallback_key"
        fallback_val = "fallback_memory_payload"

        # Check offline cache set
        set_fb = cache_set(fallback_key, fallback_val, ttl_seconds=5)
        print(f"cache_set (Redis Offline) -> Mem cache fallback: {'PASS' if set_fb else 'FAIL'}")

        # Check offline cache get
        get_fb = cache_get(fallback_key)
        print(f"cache_get (Redis Offline) -> Mem cache fallback: {'PASS' if get_fb == fallback_val else 'FAIL'} (Value: {get_fb})")

        # Check memory dict contains item
        mem_keys = [k for k in _mem_cache.keys() if fallback_key in k]
        print(f"Verify memory cache stores item directly: {'PASS' if len(mem_keys) > 0 else 'FAIL'} (Keys: {mem_keys})")

        # Expiration in fallback memory
        print("Sleeping 6s for fallback key expiration...")
        time.sleep(6)
        get_fb_exp = cache_get(fallback_key)
        print(f"Verify fallback memory item expired: {'PASS' if get_fb_exp is None else 'FAIL'} (Value: {get_fb_exp})")

    # Clean up pattern keys
    cache_delete_pattern("nova:test:*")
    print("\n==============================================")
    print("Redis Functional Diagnostics Completed")
    print("==============================================")

if __name__ == "__main__":
    run_diagnostics()
