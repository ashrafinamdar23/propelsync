from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Propelsync"
    app_version: str = "0.1.0"
    app_env: str = "local"
    api_v1_prefix: str = "/api/v1"
    cors_origins: str = "http://localhost:5173,http://localhost:3000"
    public_app_origin: str = "http://localhost:8088"
    public_app_https_origin: str = "https://localhost:8443"

    postgres_db: str = "propelsync_dev"
    postgres_user: str = "propelsync"
    postgres_password: str = "propelsync_dev_password"
    postgres_host: str = "localhost"
    postgres_port: int = 5432

    database_url: str | None = Field(default=None)
    redis_url: str = "redis://redis:6379/0"
    celery_broker_url: str | None = None
    celery_result_backend: str | None = None

    keycloak_internal_url: str = "http://keycloak:8080"
    keycloak_external_url: str = "http://localhost:8080"
    keycloak_realm: str = "propelsync"
    keycloak_admin_username: str = "admin"
    keycloak_admin_password: str = "admin"
    keycloak_api_client_id: str = "propelsync-api"
    keycloak_web_client_id: str = "propelsync-web"
    keycloak_verify_audience: bool = True
    keycloak_extra_issuers: str = "https://localhost/realms/propelsync"

    bootstrap_platform_admin_email: str = "admin@propelsync.local"
    bootstrap_platform_admin_mobile_number: str | None = None
    bootstrap_platform_admin_full_name: str = "Platform Admin"
    bootstrap_platform_admin_password: str = "Admin@12345"
    scheduled_jobs_system_actor_subject: str = "system:scheduled-jobs"
    scheduled_jobs_system_actor_email: str = "system.scheduled-jobs@propelsync.local"
    scheduled_jobs_system_actor_full_name: str = "Scheduled Jobs System"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def sqlalchemy_database_uri(self) -> str:
        if self.database_url:
            return self.database_url
        return (
            "postgresql+psycopg://"
            f"{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    @property
    def celery_broker_uri(self) -> str:
        return self.celery_broker_url or self.redis_url

    @property
    def celery_result_backend_uri(self) -> str:
        return self.celery_result_backend or self.redis_url

    @property
    def keycloak_issuer(self) -> str:
        return f"{self.keycloak_external_url.rstrip('/')}/realms/{self.keycloak_realm}"

    @property
    def keycloak_internal_issuer(self) -> str:
        return f"{self.keycloak_internal_url.rstrip('/')}/realms/{self.keycloak_realm}"

    @property
    def keycloak_jwks_url(self) -> str:
        return f"{self.keycloak_internal_issuer}/protocol/openid-connect/certs"

    @property
    def keycloak_allowed_issuers(self) -> set[str]:
        extra_issuers = {
            issuer.strip()
            for issuer in self.keycloak_extra_issuers.split(",")
            if issuer.strip()
        }
        return {
            self.keycloak_issuer,
            self.keycloak_internal_issuer,
            *extra_issuers,
        }

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
