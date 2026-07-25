"""Authentication module - register, login, JWT, RBAC via integer role_id."""
"""Authentication module."""
from .models import User
from .role_models import Role

__all__ = ["User", "Role"]