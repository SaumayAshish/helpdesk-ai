"""
Aggregates all v1 endpoint routers into a single router.
"""

from fastapi import APIRouter

from backend.api.v1.endpoints import auth, dashboard, health, tickets, users

api_router = APIRouter()

api_router.include_router(health.router)
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(tickets.router, prefix="/tickets", tags=["Tickets"])
api_router.include_router(users.router, prefix="/users", tags=["Users"])

api_router.include_router(
    dashboard.router,
    prefix="/dashboard",
    tags=["Dashboard"],
)
