"""Request validation for auth routes, aligned with the V1 auth DTOs."""

import re

from pydantic import BaseModel, ConfigDict, field_validator

_EMAIL = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")
_PASSWORD_RULES = (
    (re.compile(r"[a-z]"), "lowercase"),
    (re.compile(r"[A-Z]"), "uppercase"),
    (re.compile(r"[0-9]"), "digit"),
    (re.compile(r"[^A-Za-z0-9]"), "symbol"),
)


class AuthRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")


def validate_email(value: str) -> str:
    if not _EMAIL.fullmatch(value):
        raise ValueError("A valid email address is required.")
    return value


def validate_password(value: str, *, require_symbol: bool = True) -> str:
    if len(value) < 12:
        raise ValueError("Password must contain at least 12 characters.")
    for pattern, label in _PASSWORD_RULES:
        if label == "symbol" and not require_symbol:
            continue
        if not pattern.search(value):
            raise ValueError(f"Password must contain a {label} character.")
    return value


class RegisterRequest(AuthRequest):
    email: str
    pseudo: str
    motDePasse: str
    accepteReglement: bool

    @field_validator("email")
    @classmethod
    def valid_email(cls, value: str) -> str:
        return validate_email(value)

    @field_validator("pseudo")
    @classmethod
    def valid_pseudo(cls, value: str) -> str:
        if len(value) < 2:
            raise ValueError("Pseudo must contain at least 2 characters.")
        return value

    @field_validator("motDePasse")
    @classmethod
    def valid_password(cls, value: str) -> str:
        return validate_password(value)


class LoginRequest(AuthRequest):
    email: str
    motDePasse: str

    @field_validator("email")
    @classmethod
    def valid_email(cls, value: str) -> str:
        return validate_email(value)


class ChangePasswordRequest(AuthRequest):
    ancienMotDePasse: str
    nouveauMotDePasse: str

    @field_validator("nouveauMotDePasse")
    @classmethod
    def valid_password(cls, value: str) -> str:
        # V1's change-password DTO requires lower/upper/digit and 12 chars;
        # unlike registration, it does not require a symbol.
        return validate_password(value, require_symbol=False)
