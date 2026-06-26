"""
Aggregates all v1 endpoint routers into a single router.

As we add modules (auth, tickets, etc.), we register them here.
"""

from fastapi import APIRouter

from backend.api.v1.endpoints import health

api_router = APIRouter()

# Register sub-routers
api_router.include_router(health.router)

# Future routers (added in later milestones):
# api_router.include_router(auth.router, prefix="/auth", tags=["Auth"])
# api_router.include_router(tickets.router, prefix="/tickets", tags=["Tickets"])
# api_router.include_router(users.router, prefix="/users", tags=["Users"])
# api_router.include_router(ml.router, prefix="/ml", tags=["ML"])
# api_router.include_router(reports.router, prefix="/reports", tags=["Reports"])
