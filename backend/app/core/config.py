from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Configurações da aplicação carregadas via variáveis de ambiente."""

    # Banco de dados
    ASYNC_DATABASE_URL: str

    # JWT
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # Supabase Storage
    SUPABASE_URL: str | None = None
    SUPABASE_KEY: str | None = None
    SUPABASE_BUCKET_INGRESSOS: str = "ingressos"
    SUPABASE_BUCKET_CERTIFICADOS: str = "certificados"
    SUPABASE_BUCKET_RELATORIOS: str = "relatorios"

    # Asaas (gateway de pagamento)
    ASAAS_API_KEY: str
    ASAAS_BASE_URL_UAT: str
    ASAAS_WEBHOOK_TOKEN: str | None = None

    # # Meta Cloud API — WhatsApp Business
    # META_WHATSAPP_TOKEN: str
    # META_PHONE_NUMBER_ID: str
    # META_VERIFY_TOKEN: str

    model_config = SettingsConfigDict(
        env_file="../.env", env_file_encoding="utf-8", extra="ignore"
    )


settings = Settings()
