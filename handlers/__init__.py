# handlers/__init__.py
"""
Экспорт роутеров
"""

from . import user_handlers
from . import admin_handlers
from . import subscription_handlers

__all__ = ["user_handlers", "admin_handlers", "subscription_handlers"]