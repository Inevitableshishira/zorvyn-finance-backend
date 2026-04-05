from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from database import engine, Base
from routers import auth, users, records, dashboard

# Create all tables on startup
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Zorvyn Finance Backend",
    description=(
        "Finance Data Processing and Access Control Backend. "
        "Supports role-based access (Viewer / Analyst / Admin), "
        "financial record management, and dashboard analytics."
    ),
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(records.router)
app.include_router(dashboard.router)


@app.get("/", tags=["Health"])
def root():
    return {
        "status": "ok",
        "message": "Zorvyn Finance Backend is running",
        "docs": "/docs",
    }
