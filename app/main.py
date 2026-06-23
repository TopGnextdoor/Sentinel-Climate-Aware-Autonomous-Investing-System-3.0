import gc
from fastapi import FastAPI
from app.utils.quota_tracker import get_quota_summary

def register_quota_route(app: FastAPI):
    # Avoid registering the route multiple times
    for route in app.routes:
        if route.path == "/quota-status":
            return
            
    @app.get("/quota-status")
    def quota_status():
        return get_quota_summary()

# 1. Monkeypatch FastAPI.__init__ for any future FastAPI instances
original_init = FastAPI.__init__

def patched_init(self, *args, **kwargs):
    original_init(self, *args, **kwargs)
    register_quota_route(self)

FastAPI.__init__ = patched_init

# 2. Find and register route on any already existing FastAPI instances in memory
for obj in gc.get_objects():
    if isinstance(obj, FastAPI):
        try:
            register_quota_route(obj)
        except Exception:
            pass
