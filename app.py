"""
Minimal FastAPI app for testing deployment
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Super Manager API", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "Super Manager API", "status": "operational", "version": "2.0.0"}

@app.get("/api/health")
async def health():
    return {"status": "healthy"}

@app.get("/api/status")
async def status():
    return {"status": "operational", "version": "2.0.0"}

# Import full functionality if available
try:
    from backend.main import app as full_app
    # Copy routes from full app
    for route in full_app.routes:
        if hasattr(route, 'path') and route.path not in ['/', '/api/health', '/api/status']:
            app.routes.append(route)
except Exception as e:
    print(f"[WARN] Running in minimal mode: {e}")
