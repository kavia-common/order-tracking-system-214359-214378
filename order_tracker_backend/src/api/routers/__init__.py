from src.api.routers.auth import router as auth_router
from src.api.routers.notifications import router as notifications_router
from src.api.routers.orders import router as orders_router

__all__ = ["auth_router", "orders_router", "notifications_router"]
