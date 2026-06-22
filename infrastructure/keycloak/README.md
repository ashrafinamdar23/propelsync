# Keycloak

Keycloak is the identity provider for Propelsync.

Keycloak handles:

- Login
- Password policy
- Sessions
- MFA
- Future SSO and identity brokering

Propelsync handles:

- Tenants
- Societies
- Platform superuser flag
- Tenant and society memberships
- Business authorization

## Start

```powershell
docker compose up -d keycloak
```

## Admin Console

Open:

```text
http://localhost:8080
```

Local development credentials are read from `.env`:

```text
KEYCLOAK_ADMIN
KEYCLOAK_ADMIN_PASSWORD
```

## Internal URL

Other Docker services should use:

```text
http://keycloak:8080
```

Data is stored in the Docker volume `propelsync_keycloak_postgres_data`.

## Local Realm Bootstrap

Run from the API container:

```powershell
docker compose exec api python -m app.scripts.bootstrap_identity
```

This creates or updates:

- Realm: `propelsync`
- API client: `propelsync-api`
- Web client: `propelsync-web`
- Smoke-test client: `propelsync-smoke-test`
- Web client audience mapper for `propelsync-api`
- Smoke-test client audience mapper for `propelsync-api`
- One-day local SSO and client session lifespans
- Platform admin user from `.env`

Normal users should be onboarded through Propelsync APIs, not manually through the Keycloak admin console.
