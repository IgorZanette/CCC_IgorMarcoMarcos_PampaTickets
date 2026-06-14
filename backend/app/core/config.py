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
    # Galeria de fotos (UC08). Bucket privado — acesso via URL assinada (login
    # obrigatório para ver). Os tipos/limite são defaults fixos (não vêm do .env).
    SUPABASE_BUCKET_FOTOS: str = "fotos"
    MAX_FOTO_SIZE_MB: int = 10
    ALLOWED_FOTO_TYPES: list[str] = ["image/jpeg", "image/png", "image/webp"]

    # Asaas (gateway de pagamento)
    ASAAS_API_KEY: str
    ASAAS_BASE_URL_UAT: str
    ASAAS_WEBHOOK_TOKEN: str
    # Dias até o vencimento do boleto. PIX é instantâneo (vence no mesmo dia);
    # o boleto precisa de uma janela futura, senão entra em OVERDUE cedo demais.
    BOLETO_DUE_DAYS: int = 3

    # Email (recuperação de senha)
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: str = "pampatickets@gmail.com"
    SMTP_PASSWORD: str
    EMAIL_FROM: str = "pampatickets@gmail.com"
    EMAIL_FROM_NAME: str = "PampaTickets"
    PASSWORD_RESET_EXPIRE_MINUTES: int = 15

    # Meta Cloud API — WhatsApp Business (UC15)
    # Sem token/phone_number_id, a integração degrada para no-op (não envia,
    # não quebra o fluxo). Os nomes de template precisam estar aprovados no
    # Meta Business Manager para envio fora da janela de 24h.
    META_WHATSAPP_TOKEN: str | None = None
    META_PHONE_NUMBER_ID: str | None = None
    META_API_VERSION: str = "v21.0"

    # Base do frontend, usada para montar links nas notificações.
    FRONTEND_URL: str = "http://localhost:5173"

    model_config = SettingsConfigDict(
        env_file="../.env", env_file_encoding="utf-8", extra="ignore"
    )


settings = Settings()
