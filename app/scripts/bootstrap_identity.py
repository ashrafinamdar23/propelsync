from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any

import httpx
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.session import SessionLocal
from app.models import User


@dataclass(frozen=True)
class BootstrapResult:
    realm_created: bool
    realm_session_settings_updated: bool
    api_client_created: bool
    web_client_created: bool
    smoke_test_client_created: bool
    web_audience_mapper_created: bool
    smoke_test_audience_mapper_created: bool
    keycloak_user_created: bool
    local_user_created: bool
    keycloak_user_id: str


class KeycloakAdminClient:
    def __init__(self, base_url: str, admin_username: str, admin_password: str) -> None:
        self.base_url = base_url.rstrip("/")
        self.admin_username = admin_username
        self.admin_password = admin_password
        self.client = httpx.Client(base_url=self.base_url, timeout=30)

    def close(self) -> None:
        self.client.close()

    def __enter__(self) -> KeycloakAdminClient:
        return self

    def __exit__(self, *_: object) -> None:
        self.close()

    def authenticate(self) -> str:
        response = self.client.post(
            "/realms/master/protocol/openid-connect/token",
            data={
                "grant_type": "password",
                "client_id": "admin-cli",
                "username": self.admin_username,
                "password": self.admin_password,
            },
        )
        response.raise_for_status()
        token = response.json()["access_token"]
        self.client.headers.update({"Authorization": f"Bearer {token}"})
        return token

    def authenticate_with_retry(self, attempts: int = 24, delay_seconds: int = 5) -> str:
        last_error: Exception | None = None
        for attempt in range(1, attempts + 1):
            try:
                return self.authenticate()
            except httpx.HTTPError as exc:
                last_error = exc
                if attempt == attempts:
                    break
                print(
                    "Waiting for Keycloak admin endpoint "
                    f"({attempt}/{attempts}) at {self.base_url}..."
                )
                time.sleep(delay_seconds)
        if last_error is not None:
            raise last_error
        raise RuntimeError("Unable to authenticate with Keycloak.")

    def ensure_realm(self, realm: str) -> bool:
        response = self.client.get(f"/admin/realms/{realm}")
        if response.status_code == 200:
            return False
        if response.status_code != 404:
            response.raise_for_status()

        create_response = self.client.post(
            "/admin/realms",
            json={
                "realm": realm,
                "enabled": True,
                "displayName": "Propelsync",
                "registrationAllowed": False,
                "resetPasswordAllowed": True,
                "loginWithEmailAllowed": True,
                "duplicateEmailsAllowed": False,
                "accessTokenLifespan": 300,
                "ssoSessionIdleTimeout": 86400,
                "ssoSessionMaxLifespan": 86400,
                "clientSessionIdleTimeout": 86400,
                "clientSessionMaxLifespan": 86400,
            },
        )
        create_response.raise_for_status()
        return True

    def ensure_realm_session_settings(self, realm: str) -> bool:
        response = self.client.get(f"/admin/realms/{realm}")
        response.raise_for_status()
        payload = response.json()
        desired_settings = {
            "accessTokenLifespan": 300,
            "ssoSessionIdleTimeout": 86400,
            "ssoSessionMaxLifespan": 86400,
            "clientSessionIdleTimeout": 86400,
            "clientSessionMaxLifespan": 86400,
        }
        if all(payload.get(key) == value for key, value in desired_settings.items()):
            return False

        payload.update(desired_settings)
        update_response = self.client.put(f"/admin/realms/{realm}", json=payload)
        update_response.raise_for_status()
        return True

    def ensure_client(self, realm: str, payload: dict[str, Any]) -> bool:
        client_id = payload["clientId"]
        response = self.client.get(
            f"/admin/realms/{realm}/clients",
            params={"clientId": client_id},
        )
        response.raise_for_status()
        clients = response.json()
        if clients:
            client = clients[0]
            changed = False
            for key in ("redirectUris", "webOrigins"):
                desired_values = payload.get(key)
                if not desired_values:
                    continue
                current_values = client.get(key) or []
                merged_values = list(dict.fromkeys([*current_values, *desired_values]))
                if merged_values != current_values:
                    client[key] = merged_values
                    changed = True
            if changed:
                update_response = self.client.put(
                    f"/admin/realms/{realm}/clients/{client['id']}",
                    json=client,
                )
                update_response.raise_for_status()
            return changed

        create_response = self.client.post(f"/admin/realms/{realm}/clients", json=payload)
        create_response.raise_for_status()
        return True

    def get_client_uuid(self, realm: str, client_id: str) -> str:
        response = self.client.get(
            f"/admin/realms/{realm}/clients",
            params={"clientId": client_id},
        )
        response.raise_for_status()
        clients = response.json()
        if not clients:
            raise RuntimeError(f"Keycloak client not found: {client_id}")
        return clients[0]["id"]

    def ensure_audience_mapper(self, realm: str, source_client_id: str, audience: str) -> bool:
        client_uuid = self.get_client_uuid(realm, source_client_id)
        mapper_name = f"audience-{audience}"
        response = self.client.get(
            f"/admin/realms/{realm}/clients/{client_uuid}/protocol-mappers/models",
        )
        response.raise_for_status()
        for mapper in response.json():
            if mapper.get("name") == mapper_name:
                return False

        create_response = self.client.post(
            f"/admin/realms/{realm}/clients/{client_uuid}/protocol-mappers/models",
            json={
                "name": mapper_name,
                "protocol": "openid-connect",
                "protocolMapper": "oidc-audience-mapper",
                "config": {
                    "included.client.audience": audience,
                    "id.token.claim": "false",
                    "access.token.claim": "true",
                },
            },
        )
        create_response.raise_for_status()
        return True

    def ensure_user(
        self,
        realm: str,
        *,
        username: str,
        email: str | None,
        mobile_number: str | None,
        full_name: str,
        password: str,
    ) -> tuple[str, bool]:
        existing_user_id = self.find_user_id(realm, username=username, email=email)
        if existing_user_id:
            self.set_user_password(realm, existing_user_id, password)
            return existing_user_id, False

        first_name, last_name = split_full_name(full_name)
        user_payload: dict[str, Any] = {
            "username": username,
            "enabled": True,
            "emailVerified": bool(email),
            "firstName": first_name,
            "lastName": last_name,
            "attributes": {},
        }
        if email:
            user_payload["email"] = email
        if mobile_number:
            user_payload["attributes"]["mobile_number"] = [mobile_number]

        create_response = self.client.post(f"/admin/realms/{realm}/users", json=user_payload)
        create_response.raise_for_status()

        user_id = create_response.headers["Location"].rstrip("/").split("/")[-1]
        self.set_user_password(realm, user_id, password)
        return user_id, True

    def find_user_id(self, realm: str, *, username: str, email: str | None) -> str | None:
        response = self.client.get(
            f"/admin/realms/{realm}/users",
            params={"username": username, "exact": "true"},
        )
        response.raise_for_status()
        users = response.json()
        if users:
            return users[0]["id"]

        if email:
            response = self.client.get(
                f"/admin/realms/{realm}/users",
                params={"email": email, "exact": "true"},
            )
            response.raise_for_status()
            users = response.json()
            if users:
                return users[0]["id"]

        return None

    def set_user_password(self, realm: str, user_id: str, password: str) -> None:
        response = self.client.put(
            f"/admin/realms/{realm}/users/{user_id}/reset-password",
            json={
                "type": "password",
                "value": password,
                "temporary": False,
            },
        )
        response.raise_for_status()


def api_client_payload() -> dict[str, Any]:
    return {
        "clientId": settings.keycloak_api_client_id,
        "name": "Propelsync API",
        "protocol": "openid-connect",
        "enabled": True,
        "publicClient": False,
        "standardFlowEnabled": False,
        "directAccessGrantsEnabled": False,
        "serviceAccountsEnabled": False,
    }


def web_client_payload() -> dict[str, Any]:
    public_origin = settings.public_app_origin.rstrip("/")
    public_https_origin = settings.public_app_https_origin.rstrip("/")
    return {
        "clientId": settings.keycloak_web_client_id,
        "name": "Propelsync Web",
        "protocol": "openid-connect",
        "enabled": True,
        "publicClient": True,
        "standardFlowEnabled": True,
        "directAccessGrantsEnabled": False,
        "redirectUris": [
            "http://localhost:3000/*",
            "http://localhost:5173/*",
            "http://localhost:8088/propelsync/*",
            f"{public_origin}/propelsync/*",
            f"{public_https_origin}/propelsync/*",
        ],
        "webOrigins": [
            "http://localhost:3000",
            "http://localhost:5173",
            "http://localhost:8088",
            public_origin,
            public_https_origin,
        ],
    }


def smoke_test_client_payload() -> dict[str, Any]:
    return {
        "clientId": "propelsync-smoke-test",
        "name": "Propelsync Smoke Test",
        "protocol": "openid-connect",
        "enabled": True,
        "publicClient": True,
        "standardFlowEnabled": False,
        "directAccessGrantsEnabled": True,
        "serviceAccountsEnabled": False,
    }


def split_full_name(full_name: str) -> tuple[str, str]:
    parts = full_name.strip().split(maxsplit=1)
    if not parts:
        return "Platform", "Admin"
    if len(parts) == 1:
        return parts[0], ""
    return parts[0], parts[1]


def get_bootstrap_username(email: str | None, mobile_number: str | None) -> str:
    if email:
        return email
    if mobile_number:
        return mobile_number
    raise ValueError("Bootstrap platform admin requires email or mobile number.")


def upsert_local_platform_admin(
    session: Session,
    *,
    keycloak_subject: str,
    email: str | None,
    mobile_number: str | None,
    full_name: str,
) -> bool:
    user = session.scalar(select(User).where(User.keycloak_subject == keycloak_subject))
    created = False

    if user is None and email:
        user = session.scalar(select(User).where(User.email == email))
    if user is None and mobile_number:
        user = session.scalar(select(User).where(User.mobile_number == mobile_number))

    if user is None:
        user = User(
            keycloak_subject=keycloak_subject,
            email=email,
            mobile_number=mobile_number,
            full_name=full_name,
            status="active",
            is_platform_superuser=True,
        )
        session.add(user)
        created = True
    else:
        user.keycloak_subject = keycloak_subject
        user.email = email
        user.mobile_number = mobile_number
        user.full_name = full_name
        user.status = "active"
        user.is_platform_superuser = True

    session.commit()
    return created


def bootstrap_identity() -> BootstrapResult:
    email = settings.bootstrap_platform_admin_email or None
    mobile_number = settings.bootstrap_platform_admin_mobile_number or None
    full_name = settings.bootstrap_platform_admin_full_name
    username = get_bootstrap_username(email, mobile_number)

    with KeycloakAdminClient(
        settings.keycloak_internal_url,
        settings.keycloak_admin_username,
        settings.keycloak_admin_password,
    ) as keycloak:
        keycloak.authenticate_with_retry()
        realm_created = keycloak.ensure_realm(settings.keycloak_realm)
        realm_session_settings_updated = keycloak.ensure_realm_session_settings(settings.keycloak_realm)
        api_client_created = keycloak.ensure_client(settings.keycloak_realm, api_client_payload())
        web_client_created = keycloak.ensure_client(settings.keycloak_realm, web_client_payload())
        smoke_test_client_created = keycloak.ensure_client(
            settings.keycloak_realm,
            smoke_test_client_payload(),
        )
        web_audience_mapper_created = keycloak.ensure_audience_mapper(
            settings.keycloak_realm,
            settings.keycloak_web_client_id,
            settings.keycloak_api_client_id,
        )
        smoke_test_audience_mapper_created = keycloak.ensure_audience_mapper(
            settings.keycloak_realm,
            "propelsync-smoke-test",
            settings.keycloak_api_client_id,
        )
        keycloak_user_id, keycloak_user_created = keycloak.ensure_user(
            settings.keycloak_realm,
            username=username,
            email=email,
            mobile_number=mobile_number,
            full_name=full_name,
            password=settings.bootstrap_platform_admin_password,
        )

    with SessionLocal() as session:
        local_user_created = upsert_local_platform_admin(
            session,
            keycloak_subject=keycloak_user_id,
            email=email,
            mobile_number=mobile_number,
            full_name=full_name,
        )

    return BootstrapResult(
        realm_created=realm_created,
        realm_session_settings_updated=realm_session_settings_updated,
        api_client_created=api_client_created,
        web_client_created=web_client_created,
        smoke_test_client_created=smoke_test_client_created,
        web_audience_mapper_created=web_audience_mapper_created,
        smoke_test_audience_mapper_created=smoke_test_audience_mapper_created,
        keycloak_user_created=keycloak_user_created,
        local_user_created=local_user_created,
        keycloak_user_id=keycloak_user_id,
    )


def main() -> None:
    result = bootstrap_identity()
    print("Identity bootstrap completed.")
    print(f"Realm created: {result.realm_created}")
    print(f"Realm session settings updated: {result.realm_session_settings_updated}")
    print(f"API client created: {result.api_client_created}")
    print(f"Web client created: {result.web_client_created}")
    print(f"Smoke test client created: {result.smoke_test_client_created}")
    print(f"Web audience mapper created: {result.web_audience_mapper_created}")
    print(f"Smoke test audience mapper created: {result.smoke_test_audience_mapper_created}")
    print(f"Keycloak user created: {result.keycloak_user_created}")
    print(f"Local platform user created: {result.local_user_created}")
    print(f"Keycloak user id: {result.keycloak_user_id}")


if __name__ == "__main__":
    main()
