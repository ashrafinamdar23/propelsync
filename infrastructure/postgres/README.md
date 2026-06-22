# Propelsync PostgreSQL

This PostgreSQL service stores Propelsync business and accounting data.

## Start

```powershell
docker compose up -d postgres
```

## Readiness

```powershell
docker compose exec postgres pg_isready -U propelsync -d propelsync_dev
```

## Connect

```powershell
docker compose exec postgres psql -U propelsync -d propelsync_dev
```

Data is stored in the Docker volume `propelsync_postgres_data`.

Do not store Keycloak identity-provider tables in this database.
