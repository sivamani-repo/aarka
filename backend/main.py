import os
from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.database import Base, engine
import app.models
from app.core.rbac import authorize_api_request

from app.routers import (
    auth,
    public,
    leads,
    customers,
    surveys,
    products,
    bom,
    quotations,
    orders,
    payments,
    inventory,
    serials,
    dispatches,
    technicians,
    installations,
    warranties,
    service,
    suppliers,
    finance,
    subsidies,
    reports,
    dashboard,
    uploads,
)

# Ensure database tables exist
Base.metadata.create_all(bind=engine)

# Ensure upload directory exists
os.makedirs("backend/uploads", exist_ok=True)

app = FastAPI(
    title="AARKA API",
    description="Solar Operations, Simplified — Enterprise Backend for Solar Installation Operations",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    dependencies=[Depends(authorize_api_request)],
)

# Enable CORS for Vite frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include all module routers
app.include_router(auth.router)
app.include_router(public.router)
app.include_router(leads.router)
app.include_router(customers.router)
app.include_router(surveys.router)
app.include_router(products.router)
app.include_router(bom.router)
app.include_router(quotations.router)
app.include_router(orders.router)
app.include_router(payments.router)
app.include_router(inventory.router)
app.include_router(serials.router)
app.include_router(dispatches.router)
app.include_router(technicians.router)
app.include_router(installations.router)
app.include_router(warranties.router)
app.include_router(service.router)
app.include_router(suppliers.router)
app.include_router(finance.router)
app.include_router(subsidies.router)
app.include_router(reports.router)
app.include_router(dashboard.router)
app.include_router(uploads.router)


@app.on_event("startup")
def on_startup():
    from app.database import SessionLocal
    from app.core.rbac import seed_rbac_catalog
    from app.core.subsidy_seed import seed_government_schemes_and_rules
    db = SessionLocal()
    try:
        seed_rbac_catalog(db)
        seed_government_schemes_and_rules(db)
    finally:
        db.close()


@app.get("/")
def home():
    return {
        "app": "AARKA",
        "tagline": "Solar Operations, Simplified.",
        "status": "operational",
        "docs": "/docs"
    }


@app.get("/health")
@app.get("/api/health")
def health_check():
    return {
        "status": "healthy",
        "database": "connected",
        "app": "AARKA",
        "version": "2.0.0"
    }
