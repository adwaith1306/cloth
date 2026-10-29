import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, RedirectResponse

from backend.config import settings
from backend.database import engine, Base, SessionLocal
from backend.routes import auth, products, orders, admin, misc
from backend.seed import seed_database

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application startup and shutdown events:
    Ensures tables exist and auto-seeds initial data if empty.
    """
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        seed_database(db)
    except Exception as e:
        print(f"Startup seed notice: {e}")
    finally:
        db.close()
    yield

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="High-performance REST API for VYBE Clothing - Premium Contemporary & Streetwear E-Commerce Store",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Configure Cross-Origin Resource Sharing (CORS)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API Routers under /api
app.include_router(auth.router, prefix=settings.API_V1_STR)
app.include_router(products.router, prefix=settings.API_V1_STR)
app.include_router(orders.router, prefix=settings.API_V1_STR)
app.include_router(admin.router, prefix=settings.API_V1_STR)
app.include_router(misc.router, prefix=settings.API_V1_STR)

# Mount frontend files for seamless single-port local hosting
frontend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "frontend"))

if os.path.isdir(frontend_dir):
    # Mount frontend directory for static assets
    app.mount("/frontend", StaticFiles(directory=frontend_dir, html=True), name="frontend")

    @app.get("/", include_in_schema=False)
    def root():
        """Serves index.html at root."""
        index_file = os.path.join(frontend_dir, "index.html")
        if os.path.exists(index_file):
            return FileResponse(index_file)
        return {"message": "VYBE Clothing API is running. Visit /docs for API documentation."}

    @app.get("/{page_name}.html", include_in_schema=False)
    def html_page(page_name: str):
        """Allows direct navigation like shop.html, cart.html, /product.html."""
        file_path = os.path.join(frontend_dir, f"{page_name}.html")
        if os.path.exists(file_path):
            return FileResponse(file_path)
        return RedirectResponse(url="/")
else:
    @app.get("/", include_in_schema=False)
    def root():
        return {"message": "VYBE Clothing API is running. Visit /docs for API documentation."}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)
