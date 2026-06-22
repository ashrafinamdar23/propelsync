# Propelsync

SaaS ERP for housing society accounting.

## Local Development

Propelsync runs locally through Docker Compose.

```powershell
docker compose up -d
```

Services:

- Nginx gateway: http://localhost:8088/propelsync/
- Nginx HTTPS gateway: https://localhost:8443/propelsync/
- FastAPI: http://localhost:8000
- Web: http://localhost:5173
- API docs: http://localhost:8000/docs
- PostgreSQL: localhost:5432
- Keycloak: http://localhost:8080
- Redis: localhost:6379
- Celery worker: `propelsync-worker`

Run tests inside the API container:

```powershell
docker compose exec api python -m pytest
```

Check the background worker:

```powershell
docker compose exec api celery -A app.worker.celery_app inspect ping
```

Run database migrations inside the API container:

```powershell
docker compose exec api alembic upgrade head
```

Bootstrap local identity:

```powershell
docker compose exec api python -m app.scripts.bootstrap_identity
```

The Nginx gateway is the preferred local entry point. It routes `/propelsync/` to the web app and
`/propelsync/api/v1/` to the API so additional apps can be added under other paths later.

For VM deployment with Nginx HTTPS, generate or place certificates at:

```text
infrastructure/nginx/certs/propelsync-selfsigned.crt
infrastructure/nginx/certs/propelsync-selfsigned.key
```

Then set these values in `.env` for a standard HTTPS port:

```text
NGINX_HTTPS_PORT=443
PUBLIC_APP_HTTPS_ORIGIN=https://your-vm-hostname-or-ip
PUBLIC_KEYCLOAK_ORIGIN=https://your-vm-hostname-or-ip
```

Run `docker compose exec api python -m app.scripts.bootstrap_identity` after changing the public
origin so Keycloak accepts the `/propelsync/` redirect URL.

See component operation notes:

- [CI/CD](CICD.md)
- [Build And Release Images](BUILD_AND_RELEASE.md)
- [VM Deployment](DEPLOYMENT.md)
- [API](app/README.md)
- [Web](frontend/README.md)
- [PostgreSQL](infrastructure/postgres/README.md)
- [Keycloak](infrastructure/keycloak/README.md)
