# CI/CD Setup

This project uses GitHub Actions to build, publish, and deploy Propelsync container images.

## Workflows

```text
.github/workflows/ci.yml
.github/workflows/release-deploy.yml
```

`CI` runs on push and pull request:

```text
Backend tests in the API Docker image
Frontend TypeScript/Vite build
```

`Release And Deploy` runs manually from GitHub Actions. It:

```text
Builds ghcr.io/<owner>/propelsync-api:<version>
Builds ghcr.io/<owner>/propelsync-gateway:<version>
Pushes both images to GHCR
Optionally SSHes into the VM and deploys the version
```

## Required GitHub Secrets

Add these in GitHub:

```text
Settings -> Secrets and variables -> Actions -> New repository secret
```

Required for VM deployment:

```text
VM_HOST=app.primabonito.com
VM_PORT=18022
VM_USER=mscoe
VM_SSH_KEY=<private SSH key allowed to log in as mscoe>
VM_APP_DIR=/opt/propelsync
GHCR_USER=ashrafinamdar23
GHCR_READ_TOKEN=<GitHub token with read:packages>
```

`GITHUB_TOKEN` is provided automatically by GitHub Actions and is used to push images to GHCR.

## VM SSH Key

Create a deploy key on your machine:

```bash
ssh-keygen -t ed25519 -C "propelsync-github-actions" -f propelsync_github_actions
```

Add the public key to the VM:

```bash
ssh-copy-id -p 18022 -i propelsync_github_actions.pub mscoe@app.primabonito.com
```

Add the private key content as `VM_SSH_KEY`.

Verify the key from your laptop before adding it to GitHub:

```bash
ssh -p 18022 -i propelsync_github_actions mscoe@app.primabonito.com
```

## GHCR Pull Token

Create a GitHub Personal Access Token for the VM with:

```text
read:packages
```

If the package is private and GitHub requires repository access, also grant the minimum repo access
needed for this repository.

Store it as:

```text
GHCR_READ_TOKEN
```

## Run A Release

In GitHub:

```text
Actions -> Release And Deploy -> Run workflow
```

Inputs:

```text
version: 0.1.3
vm_host: app.primabonito.com
deploy: true
```

The workflow updates the VM `.env`:

```text
PROPELSYNC_API_IMAGE=ghcr.io/<owner>/propelsync-api:<version>
PROPELSYNC_GATEWAY_IMAGE=ghcr.io/<owner>/propelsync-gateway:<version>
```

Then it runs:

```bash
docker compose -f docker-compose.prod.yml pull
docker compose -f docker-compose.prod.yml up -d --force-recreate api worker nginx
docker compose -f docker-compose.prod.yml exec -T api alembic upgrade head
```

Bootstrap is not run automatically because it changes identity provider configuration. Run it
manually only when public URL, Keycloak client, or bootstrap admin settings change:

```bash
docker compose -f docker-compose.prod.yml exec api python -m app.scripts.bootstrap_identity
```
