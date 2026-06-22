# Nginx Gateway

Nginx is the local gateway for Propelsync.

```powershell
docker compose up -d nginx
```

Routes:

```text
http://localhost:8088/health
http://localhost:8088/propelsync/
http://localhost:8088/propelsync/api/v1/
https://localhost:8443/health
https://localhost:8443/propelsync/
https://localhost:8443/propelsync/api/v1/
https://localhost:8443/realms/propelsync/.well-known/openid-configuration
```

`/propelsync/` proxies to the frontend dev server. `/propelsync/api/v1/` proxies to FastAPI.
`/realms/` and `/resources/` proxy public Keycloak endpoints so the HTTPS frontend can authenticate
without browser mixed-content issues. Keycloak admin remains directly available at
`http://localhost:8080` in local development.

## Self-Signed Certificate

Generate a local certificate and private key:

```powershell
powershell -ExecutionPolicy Bypass -File .\infrastructure\nginx\scripts\generate-self-signed-cert.ps1
```

The generated files are:

```text
infrastructure/nginx/certs/propelsync-selfsigned.crt
infrastructure/nginx/certs/propelsync-selfsigned.key
```

They are ignored by git. Replace them on the VM with a VM-specific self-signed certificate or a real
certificate later.

For VM deployment on standard HTTPS, set:

```text
NGINX_HTTPS_PORT=443
PUBLIC_APP_HTTPS_ORIGIN=https://your-vm-hostname-or-ip
PUBLIC_KEYCLOAK_ORIGIN=https://your-vm-hostname-or-ip
```

After changing `PUBLIC_APP_HTTPS_ORIGIN`, run:

```powershell
docker compose exec api python -m app.scripts.bootstrap_identity
```

This updates the Keycloak web client redirect URI for `/propelsync/`.
