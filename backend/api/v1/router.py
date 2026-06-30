"""
Aggregates all v1 endpoint routers into a single router.
"""

from fastapi import APIRouter

from backend.api.v1.endpoints import auth, health, tickets

api_router = APIRouter()

api_router.include_router(health.router)
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(tickets.router, prefix="/tickets", tags=["Tickets"])
