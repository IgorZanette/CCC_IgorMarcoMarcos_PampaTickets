from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Configurações da aplicação carregadas via variáveis de ambiente."""

    # Banco de dados
    ASYNC_DATABASE_URL: str

    # JWT
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    # Teto absoluto de sessão: o /auth/refresh desliza a expiração do access
    # token, mas nunca além deste limite desde o login (claim auth_time).
    SESSION_MAX_HOURS: int = 12

    # Supabase Storage
    SUPABASE_URL: str | None = None
    SUPABASE_KEY: str | None = None
    SUPABASE_BUCKET_INGRESSOS: str = "ingressos"
    SUPABASE_BUCKET_CERTIFICADOS: str = "certificados"
    SUPABASE_BUCKET_RELATORIOS: str = "relatorios"

    # Asaas (gateway de pagamento)
    ASAAS_API_KEY: str
    ASAAS_BASE_URL_UAT: str
    ASAAS_WEBHOOK_TOKEN: str

    # Email (recuperação de senha)
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: str = "pampatickets@gmail.com"
    SMTP_PASSWORD: str
    EMAIL_FROM: str = "pampatickets@gmail.com"
    EMAIL_FROM_NAME: str = "PampaTickets"
    PASSWORD_RESET_EXPIRE_MINUTES: int = 15

    model_config = SettingsConfigDict(
        env_file="../.env", env_file_encoding="utf-8", extra="ignore"
    )


settings = Settings()
