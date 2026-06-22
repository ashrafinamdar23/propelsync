# Build And Release Images

This guide builds Propelsync container images and publishes them to GitHub Container Registry
(`ghcr.io`) for VM deployment.

Use this when the VM should not contain application source code.

## Image Strategy

Propelsync uses two application images:

```text
ghcr.io/<owner>/propelsync-api:<version>
ghcr.io/<owner>/propelsync-web:<version>
```

The worker uses the same image as the API:

```text
worker image = ghcr.io/<owner>/propelsync-api:<version>
```

Infrastructure images are pulled directly:

```text
nginx:1.27-alpine
postgres:16-alpine
redis:7-alpine
quay.io/keycloak/keycloak:26.6.3
```

## 1. Choose Version And Registry

Set these in your shell:

```bash
export GHCR_OWNER=<github-org-or-username>
export VERSION=0.1.0
export VM_HOST=<vm-domain-or-ip>
```

Example:

```bash
export GHCR_OWNER=ashrafinamdar
export VERSION=0.1.0
export VM_HOST=erp.example.com
```

Image names:

```bash
export API_IMAGE=ghcr.io/$GHCR_OWNER/propelsync-api:$VERSION
export WEB_IMAGE=ghcr.io/$GHCR_OWNER/propelsync-web:$VERSION
```

## 2. Login To GHCR

Create a GitHub personal access token with package write permission.

Then login:

```bash
echo <github-token> | docker login ghcr.io -u <github-username> --password-stdin
```

For GitHub Actions, use `${{ secrets.GITHUB_TOKEN }}` or a PAT with package permissions.

## 3. Build Images

Build API image:

```bash
docker build -t "$API_IMAGE" .
```

Build web image:

```bash
docker build \
  -f frontend/Dockerfile.prod \
  --build-arg VITE_BASE_PATH=/propelsync/ \
  --build-arg VITE_API_BASE_URL=/propelsync/api/v1 \
  --build-arg VITE_KEYCLOAK_URL=https://$VM_HOST \
  --build-arg VITE_KEYCLOAK_REALM=propelsync \
  --build-arg VITE_KEYCLOAK_CLIENT_ID=propelsync-web \
  -t "$WEB_IMAGE" \
  ./frontend
```

Important: Vite values are baked into the web image at build time. Build the web image for the
target VM hostname or domain.

## 4. Test Images Locally

Optional quick checks:

```bash
docker run --rm "$API_IMAGE" python -m compileall app
docker run --rm "$WEB_IMAGE" nginx -t
```

## 5. Push Images

```bash
docker push "$API_IMAGE"
docker push "$WEB_IMAGE"
```

In GitHub, confirm the packages exist under:

```text
https://github.com/users/<owner>/packages
https://github.com/orgs/<owner>/packages
```

Set package visibility to private or public as appropriate.

## 6. Create Deployment Bundle

The VM does not need source code. Copy only the deployment files:

```bash
tar -czf propelsync-deploy-$VERSION.tar.gz \
  docker-compose.prod.yml \
  .env.example \
  infrastructure/nginx/nginx.prod.conf \
  infrastructure/postgres/init
```

Copy the bundle to the VM:

```bash
scp propelsync-deploy-$VERSION.tar.gz user@<vm-host>:/opt/propelsync/
```

On the VM:

```bash
cd /opt/propelsync
tar -xzf propelsync-deploy-$VERSION.tar.gz
cp .env.example .env
```

Then edit `.env` with VM secrets and the image tags.

## 7. VM Pull Test

On the VM, login to GHCR:

```bash
echo <github-token> | docker login ghcr.io -u <github-username> --password-stdin
```

Pull:

```bash
docker pull "ghcr.io/<owner>/propelsync-api:<version>"
docker pull "ghcr.io/<owner>/propelsync-web:<version>"
```

## 8. Configure VM Env

In VM `.env`:

```text
PROPELSYNC_API_IMAGE=ghcr.io/<owner>/propelsync-api:<version>
PROPELSYNC_WEB_IMAGE=ghcr.io/<owner>/propelsync-web:<version>
PUBLIC_APP_HTTPS_ORIGIN=https://<vm-host>
PUBLIC_KEYCLOAK_ORIGIN=https://<vm-host>
KEYCLOAK_EXTRA_ISSUERS=https://<vm-host>/realms/propelsync
```

Then deploy with:

```bash
docker compose -f docker-compose.prod.yml pull
docker compose -f docker-compose.prod.yml up -d
docker compose -f docker-compose.prod.yml exec api alembic upgrade head
docker compose -f docker-compose.prod.yml exec api python -m app.scripts.bootstrap_identity
```

## 9. Release Upgrade

For each release:

```bash
export VERSION=0.1.1
export API_IMAGE=ghcr.io/$GHCR_OWNER/propelsync-api:$VERSION
export WEB_IMAGE=ghcr.io/$GHCR_OWNER/propelsync-web:$VERSION

docker build -t "$API_IMAGE" .
docker build \
  -f frontend/Dockerfile.prod \
  --build-arg VITE_BASE_PATH=/propelsync/ \
  --build-arg VITE_API_BASE_URL=/propelsync/api/v1 \
  --build-arg VITE_KEYCLOAK_URL=https://$VM_HOST \
  --build-arg VITE_KEYCLOAK_REALM=propelsync \
  --build-arg VITE_KEYCLOAK_CLIENT_ID=propelsync-web \
  -t "$WEB_IMAGE" \
  ./frontend

docker push "$API_IMAGE"
docker push "$WEB_IMAGE"
```

Update VM `.env` image tags:

```text
PROPELSYNC_API_IMAGE=ghcr.io/<owner>/propelsync-api:0.1.1
PROPELSYNC_WEB_IMAGE=ghcr.io/<owner>/propelsync-web:0.1.1
```

Apply:

```bash
docker compose -f docker-compose.prod.yml pull
docker compose -f docker-compose.prod.yml up -d
docker compose -f docker-compose.prod.yml exec api alembic upgrade head
docker compose -f docker-compose.prod.yml exec api python -m app.scripts.bootstrap_identity
```

## 10. Tarball Alternative

Use this only when the VM cannot access GHCR.

On build machine:

```bash
docker save "$API_IMAGE" -o propelsync-api-$VERSION.tar
docker save "$WEB_IMAGE" -o propelsync-web-$VERSION.tar
```

Copy to VM:

```bash
scp propelsync-api-$VERSION.tar propelsync-web-$VERSION.tar user@<vm-host>:/opt/propelsync/
```

On VM:

```bash
cd /opt/propelsync
docker load -i propelsync-api-$VERSION.tar
docker load -i propelsync-web-$VERSION.tar
docker compose -f docker-compose.prod.yml up -d
```

Registry deployment is still recommended because upgrades become pull-and-restart instead of manual
file transfer.
