from .auth import router as auth_router
from .statements import router as statements_router
from .transactions import router as transactions_router
from .categories import router as categories_router
from .analytics import router as analytics_router
from .merchant_rules import router as merchant_rules_router

__all__ = [
    "auth_router",
    "statements_router",
    "transactions_router",
    "categories_router",
    "analytics_router",
    "merchant_rules_router",
]
