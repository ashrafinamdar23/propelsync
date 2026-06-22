from typing import Any

import jwt
from fastapi import HTTPException, status
from jwt import PyJWKClient

from app.core.config import settings


class TokenVerificationError(Exception):
    pass


class KeycloakTokenVerifier:
    def __init__(self, jwks_url: str) -> None:
        self.jwks_client = PyJWKClient(jwks_url)

    def verify(self, token: str) -> dict[str, Any]:
        try:
            signing_key = self.jwks_client.get_signing_key_from_jwt(token)
            options = {"verify_aud": settings.keycloak_verify_audience}
            audience = settings.keycloak_api_client_id if settings.keycloak_verify_audience else None
            claims = jwt.decode(
                token,
                signing_key.key,
                algorithms=["RS256"],
                audience=audience,
                options={**options, "verify_iss": False},
            )
            if claims.get("iss") not in settings.keycloak_allowed_issuers:
                raise TokenVerificationError("Invalid token issuer.")
            return claims
        except jwt.PyJWTError as exc:
            raise TokenVerificationError("Invalid authentication token.") from exc


token_verifier = KeycloakTokenVerifier(settings.keycloak_jwks_url)


def verify_keycloak_token(token: str) -> dict[str, Any]:
    return token_verifier.verify(token)


def credentials_exception() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials.",
        headers={"WWW-Authenticate": "Bearer"},
    )
