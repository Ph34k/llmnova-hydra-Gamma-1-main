"""Minimal security helpers to match documentation expectations.

This module provides lightweight, in-memory implementations of
auth_service, authorization_service, Permission, Role and
tiered_rate_limiter so imports from `src.security` used in docs
will work within this repository.

These are simple stubs intended for development/demo only and are
NOT production-ready.
"""
from __future__ import annotations

import asyncio
import os
import hashlib
import uuid
from typing import Dict, Optional


class Permission:
    AGENT_EXECUTE = "agent_execute"
    ADMIN_PANEL = "admin_panel"


class Role:
    GUEST = "guest"
    USER = "user"
    POWER_USER = "power_user"
    ADMIN = "admin"
    SUPER_ADMIN = "super_admin"


class AuthService:
    def __init__(self) -> None:
        # simple in-memory user store: id -> {email, password_hash}
        self._users: Dict[str, Dict[str, str]] = {}
        self._salt = os.getenv("SECURITY_SALT", "dev-salt-do-not-use-in-prod")

    def _hash(self, password: str) -> str:
        salted = password + self._salt
        return hashlib.sha256(salted.encode("utf-8")).hexdigest()

    def register_user(self, email: str, password: str) -> Dict[str, str]:
        user_id = str(uuid.uuid4())
        self._users[user_id] = {"email": email, "password_hash": self._hash(password)}
        return {"id": user_id, "email": email}

    def login(self, email: str, password: str) -> Dict[str, str]:
        # naive lookup
        for uid, record in self._users.items():
            if record.get("email") == email and record.get("password_hash") == self._hash(password):
                access = str(uuid.uuid4())
                refresh = str(uuid.uuid4())
                return {"access_token": access, "refresh_token": refresh}
        raise ValueError("Invalid credentials")


class AuthorizationService:
    def __init__(self) -> None:
        # user_id -> role
        self.user_roles: Dict[str, str] = {}
        # role -> set of permissions
        self.role_permissions: Dict[str, set] = {
            Role.GUEST: set(),
            Role.USER: {Permission.AGENT_EXECUTE},
            Role.POWER_USER: {Permission.AGENT_EXECUTE},
            Role.ADMIN: {Permission.AGENT_EXECUTE, Permission.ADMIN_PANEL},
            Role.SUPER_ADMIN: {Permission.AGENT_EXECUTE, Permission.ADMIN_PANEL},
        }

    def assign_role(self, user_id: str, role: str) -> None:
        self.user_roles[user_id] = role

    def has_permission(self, user_id: str, permission: str) -> bool:
        role = self.user_roles.get(user_id, Role.GUEST)
        return permission in self.role_permissions.get(role, set())


class TieredRateLimiter:
    def __init__(self) -> None:
        # user_id -> tier string
        self._tiers: Dict[str, str] = {}

    def set_user_tier(self, user_id: str, tier: str) -> None:
        self._tiers[user_id] = tier

    async def check_rate_limit(self, user_id: str) -> None:
        # Simple placeholder: always passes. Real impl would raise on limit exceed.
        await asyncio.sleep(0)
        return


# module-level singletons used by docs
auth_service = AuthService()
authorization_service = AuthorizationService()
tiered_rate_limiter = TieredRateLimiter()
