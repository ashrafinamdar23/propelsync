# Propelsync VM Deployment

This guide deploys Propelsync on a single VM using Docker Compose.

The app is served behind Nginx at:

```text
https://<vm-host>/propelsync/
```

Nginx also proxies:

```text
/propelsync/api/v1/  -> FastAPI
/realms/             -> Keycloak public OIDC endpoints
/resources/          -> Keycloak public assets
```

## 1. VM Requirements

Install on the VM:

```bash
docker --version
docker compose version
git --version
```

Open firewall ports:

```text
80/tcp
443/tcp
```

Recommended VM baseline for MVP:

```text
CPU: 2 vCPU minimum
RAM: 4 GB minimum
Disk: 40 GB minimum
OS: Ubuntu LTS or equivalent Linux server
```

## 2. Prepare Deployment Directory

```bash
sudo mkdir -p /opt/propelsync
sudo chown "$USER":"$USER" /opt/propelsync
cd /opt/propelsync
```

The VM does not need application source code. It needs only deployment files:

```text
docker-compose.prod.yml
.env.example
.env
infrastructure/nginx/nginx.prod.conf
infrastructure/nginx/certs/
infrastructure/postgres/init/
```

Copy those files from your release bundle or repository checkout on your build machine.

The application itself is pulled as images:

```text
PROPELSYNC_API_IMAGE
PROPELSYNC_WEB_IMAGE
```

See [BUILD_AND_RELEASE.md](BUILD_AND_RELEASE.md) for GHCR build and push steps.

## 3. Create Production Env File

Start from the template included in the deployment bundle:

```bash
cp .env.example .env
```

Edit `.env`.

Required VM values:

```text
PROPELSYNC_API_IMAGE=ghcr.io/<owner>/propelsync-api:<version>
PROPELSYNC_WEB_IMAGE=ghcr.io/<owner>/propelsync-web:<version>

POSTGRES_DB=propelsync_prod
POSTGRES_USER=propelsync
POSTGRES_PASSWORD=<strong-postgres-password>
POSTGRES_PORT=5432
DATABASE_URL=postgresql+psycopg://propelsync:<strong-postgres-password>@postgres:5432/propelsync_prod

APP_ENV=production
API_COMMAND=uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 2

KEYCLOAK_DB=keycloak
KEYCLOAK_DB_USER=keycloak
KEYCLOAK_DB_PASSWORD=<strong-keycloak-db-password>
KEYCLOAK_ADMIN=admin
KEYCLOAK_ADMIN_PASSWORD=<strong-keycloak-admin-password>

NGINX_PORT=80
NGINX_HTTPS_PORT=443
PUBLIC_APP_ORIGIN=http://<vm-host>
PUBLIC_APP_HTTPS_ORIGIN=https://<vm-host>
PUBLIC_KEYCLOAK_ORIGIN=https://<vm-host>

CORS_ORIGINS=https://<vm-host>,http://<vm-host>
KEYCLOAK_EXTRA_ISSUERS=https://<vm-host>/realms/propelsync

BOOTSTRAP_PLATFORM_ADMIN_EMAIL=<platform-admin-email>
BOOTSTRAP_PLATFORM_ADMIN_FULL_NAME=Platform Admin
BOOTSTRAP_PLATFORM_ADMIN_PASSWORD=<temporary-strong-admin-password>
```

Keep internal Docker URLs unchanged:

```text
REDIS_URL=redis://redis:6379/0
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/0
```

Do not set `DATABASE_URL` to `localhost` for Docker deployment. The API and worker containers use
the compose service name:

```text
postgresql+psycopg://propelsync:<password>@postgres:5432/propelsync_prod
```

If `DATABASE_URL` exists in `.env`, make sure it uses `@postgres:5432`, not `@localhost:5432`.

For development, `API_COMMAND` may include `--reload`. For VM deployment, use workers and no reload:

```text
API_COMMAND=uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 2
```

## 4. Create Nginx TLS Certificate

For self-signed certificate on Linux VM:

```bash
mkdir -p infrastructure/nginx/certs
openssl req -x509 -nodes -newkey rsa:2048 -days 825 \
  -keyout infrastructure/nginx/certs/propelsync-selfsigned.key \
  -out infrastructure/nginx/certs/propelsync-selfsigned.crt \
  -subj "/CN=<vm-host>" \
  -addext "subjectAltName=DNS:<vm-host>,IP:<vm-ip>"
```

Examples:

```text
<vm-host> = erp.example.com
<vm-ip>   = 10.0.0.10
```

For a real certificate later, replace the same two files:

```text
infrastructure/nginx/certs/propelsync-selfsigned.crt
infrastructure/nginx/certs/propelsync-selfsigned.key
```

## 5. Pull And Start Services

```bash
docker login ghcr.io -u <github-username>
docker compose -f docker-compose.prod.yml pull
docker compose -f docker-compose.prod.yml up -d
```

Check containers:

```bash
docker compose -f docker-compose.prod.yml ps
```

Expected core services:

```text
propelsync-nginx
propelsync-api
propelsync-web
propelsync-worker
propelsync-postgres
propelsync-keycloak
propelsync-keycloak-postgres
propelsync-redis
```

## 6. Run Database Migrations

```bash
docker compose -f docker-compose.prod.yml exec api alembic upgrade head
```

Run this after every deployment that includes database changes.

## 7. Bootstrap Identity

Run once after services are up and after every change to public URL values:

```bash
docker compose -f docker-compose.prod.yml exec api python -m app.scripts.bootstrap_identity
```

This creates or updates:

```text
Keycloak realm
API client
Web client
Smoke-test client
Audience mappers
Platform admin user
Local Propelsync user row
Redirect URLs for /propelsync/
```

## 8. Validate Deployment

Gateway health:

```bash
curl -k https://<vm-host>/health
```

API health through Nginx:

```bash
curl -k https://<vm-host>/propelsync/api/v1/health
```

Keycloak public discovery through Nginx:

```bash
curl -k https://<vm-host>/realms/propelsync/.well-known/openid-configuration
```

Open the app:

```text
https://<vm-host>/propelsync/
```

Because this is self-signed, the browser will show a certificate warning until a trusted certificate
is installed.

## 9. Login

Use the bootstrap platform admin:

```text
BOOTSTRAP_PLATFORM_ADMIN_EMAIL
BOOTSTRAP_PLATFORM_ADMIN_PASSWORD
```

After first login, change the password from Keycloak admin or by adding a proper password-reset flow
later.

## 10. Component Operations

### Nginx

Routes public traffic.

Important files:

```text
infrastructure/nginx/nginx.prod.conf
infrastructure/nginx/certs/propelsync-selfsigned.crt
infrastructure/nginx/certs/propelsync-selfsigned.key
```

Restart:

```bash
docker compose -f docker-compose.prod.yml restart nginx
```

Validate config:

```bash
docker compose -f docker-compose.prod.yml exec nginx nginx -t
```

### FastAPI

Runs application APIs, migrations, and bootstrap scripts.

Important commands:

```bash
docker compose -f docker-compose.prod.yml logs -f api
docker compose -f docker-compose.prod.yml exec api alembic upgrade head
docker compose -f docker-compose.prod.yml exec api python -m app.scripts.bootstrap_identity
```

### Web

Runs the React/Vite frontend. It is served under:

```text
/propelsync/
```

Important environment:

```text
VITE_BASE_PATH=/propelsync/
VITE_API_BASE_URL=/propelsync/api/v1
VITE_KEYCLOAK_URL=${PUBLIC_KEYCLOAK_ORIGIN}
```

### PostgreSQL

Stores Propelsync business data.

Volume:

```text
propelsync_postgres_data
```

Backup:

```bash
docker compose -f docker-compose.prod.yml exec postgres pg_dump -U "$POSTGRES_USER" "$POSTGRES_DB" > propelsync-backup.sql
```

Restore into a fresh database:

```bash
cat propelsync-backup.sql | docker compose -f docker-compose.prod.yml exec -T postgres psql -U "$POSTGRES_USER" "$POSTGRES_DB"
```

### Keycloak

Stores identity and sessions.

Public OIDC endpoint through Nginx:

```text
https://<vm-host>/realms/propelsync
```

The production compose file does not publish the Keycloak admin port to the VM network. For admin
maintenance, prefer an SSH tunnel or add a temporary restricted port mapping only while needed.

Internal admin endpoint inside Docker:

```text
http://keycloak:8080
```

Volume:

```text
propelsync_keycloak_postgres_data
```

### Redis And Worker

Redis backs Celery. Worker runs scheduled billing/penalty jobs.

Check worker:

```bash
docker compose -f docker-compose.prod.yml exec api celery -A app.worker.celery_app inspect ping
```

Logs:

```bash
docker compose -f docker-compose.prod.yml logs -f worker
```

## 11. Updating The VM

```bash
docker compose -f docker-compose.prod.yml pull
docker compose -f docker-compose.prod.yml up -d
docker compose -f docker-compose.prod.yml exec api alembic upgrade head
docker compose -f docker-compose.prod.yml exec api python -m app.scripts.bootstrap_identity
docker compose -f docker-compose.prod.yml ps
```

If Keycloak public host changes, update these first:

```text
PUBLIC_APP_HTTPS_ORIGIN
PUBLIC_KEYCLOAK_ORIGIN
KEYCLOAK_EXTRA_ISSUERS
CORS_ORIGINS
```

Then rerun bootstrap.

## 12. Common Problems

### Browser Shows Certificate Warning

Expected with self-signed TLS. Replace with a trusted certificate when a domain is available.

### Login Redirect Fails

Check `.env`:

```text
PUBLIC_APP_HTTPS_ORIGIN=https://<vm-host>
PUBLIC_KEYCLOAK_ORIGIN=https://<vm-host>
```

Then run:

```bash
docker compose -f docker-compose.prod.yml exec api python -m app.scripts.bootstrap_identity
```

### API Says Invalid Token Issuer

Set:

```text
KEYCLOAK_EXTRA_ISSUERS=https://<vm-host>/realms/propelsync
```

Then recreate API:

```bash
docker compose -f docker-compose.prod.yml up -d --force-recreate api worker
```

### Nginx Returns 502

Check upstream services:

```bash
docker compose -f docker-compose.prod.yml ps
docker compose -f docker-compose.prod.yml logs --tail 100 api
docker compose -f docker-compose.prod.yml logs --tail 100 web
docker compose -f docker-compose.prod.yml logs --tail 100 keycloak
```

If API or Keycloak was recreated, restart Nginx:

```bash
docker compose -f docker-compose.prod.yml restart nginx
```

### Migrations Not Applied

Run:

```bash
docker compose -f docker-compose.prod.yml exec api alembic upgrade head
```

## 13. Minimum Production Hardening Before Real Use

Before using with real society data:

```text
Use strong unique passwords in .env
Restrict direct ports 8000, 5173, 5432, 6379, 9000 from public internet
Prefer a trusted TLS certificate
Schedule PostgreSQL and Keycloak database backups
Move secrets to a proper secret manager when available
Review firewall rules
Review Docker volume backup strategy
```
