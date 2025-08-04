"""Main application entry point for the FastAPI Expense Tracker application.

This file initializes the FastAPI app, sets up the lifespan context manager,
and configures the application with custom settings.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.dependencies.settings_dependencies import get_env_settings
from app.interfaces.api.v1.controllers.balance_controller import router as balance_router
from app.interfaces.api.v1.controllers.expense_controller import router as expense_router
from app.interfaces.api.v1.controllers.group_controller import router as group_router
from app.interfaces.api.v1.controllers.health_check_controller import router as health_routes
from app.interfaces.api.v1.controllers.user_controller import router as user_router

app = FastAPI(
    title=get_env_settings().app_name,
    description=get_env_settings().app_description,
    version=get_env_settings().app_version,
    docs_url="/docs",
    redoc_url="/redoc",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=get_env_settings().allowed_origins,
    allow_credentials=True,
    allow_methods=get_env_settings().allowed_methods,
    allow_headers=get_env_settings().allowed_headers,
)

app.include_router(health_routes, prefix="/api/v1")
app.include_router(user_router, prefix="/api/v1")
app.include_router(group_router, prefix="/api/v1")
app.include_router(expense_router, prefix="/api/v1")
app.include_router(balance_router, prefix="/api/v1")
