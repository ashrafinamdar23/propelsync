# Nginx Certificates

Place the Nginx TLS certificate and key here:

```text
propelsync-selfsigned.crt
propelsync-selfsigned.key
```

These files are intentionally ignored by git.

For local development, generate them with:

```powershell
.\infrastructure\nginx\scripts\generate-self-signed-cert.ps1
```

For a VM with OpenSSL:

```bash
mkdir -p infrastructure/nginx/certs
openssl req -x509 -nodes -newkey rsa:2048 -days 825 \
  -keyout infrastructure/nginx/certs/propelsync-selfsigned.key \
  -out infrastructure/nginx/certs/propelsync-selfsigned.crt \
  -subj "/CN=localhost" \
  -addext "subjectAltName=DNS:localhost,IP:127.0.0.1"
```
