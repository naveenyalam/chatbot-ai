import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app.main import app
from fastapi.routing import APIRoute

def print_routes():
    print("==============================================")
    print("NOVA AI — Route Inventory")
    print("==============================================")
    
    routes_list = []
    
    def process_routes(routes, prefix=""):
        for route in routes:
            if isinstance(route, APIRoute):
                methods = getattr(route, "methods", None)
                methods_str = ",".join(methods) if methods else "GET"
                routes_list.append({
                    "path": prefix + route.path,
                    "methods": methods_str,
                    "name": route.name
                })
            elif 'IncludedRouter' in type(route).__name__:
                sub_prefix = getattr(route.include_context, "prefix", "")
                process_routes(route.original_router.routes, prefix + sub_prefix)
            elif hasattr(route, "routes"):
                sub_prefix = getattr(route, "prefix", "")
                process_routes(route.routes, prefix + sub_prefix)
                
    process_routes(app.routes)
    
    # Sort by path
    for r in sorted(routes_list, key=lambda x: (x["path"], x["methods"])):
        print(f"Path: {r['path']:<60} | Methods: {r['methods']:<15} | Name: {r['name']}")
    print("==============================================")

if __name__ == "__main__":
    print_routes()
