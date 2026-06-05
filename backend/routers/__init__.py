"""
路由模块
"""
from routers.auth import router as auth_router
from routers.cats import router as cats_router
from routers.weights import router as weights_router
from routers.feeding import router as feeding_router

__all__ = ["auth_router", "cats_router", "weights_router", "feeding_router"]
