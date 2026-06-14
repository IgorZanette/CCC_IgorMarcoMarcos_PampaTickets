from typing import BinaryIO

from supabase import Client, create_client

from app.core.config import settings


def _to_bytes(file: BinaryIO | bytes) -> bytes:
    """
    Normaliza o conteúdo para bytes. O SDK `storage3` aceita bytes/BufferedReader,
    mas não BytesIO (que o ReportLab retorna).
    """
    if isinstance(file, (bytes, bytearray)):
        return bytes(file)
    if hasattr(file, "getvalue"):
        return file.getvalue()
    return file.read()


class SupabaseStorage:
    """Cliente para upload de arquivos no Supabase Storage."""

    def __init__(self):
        if not settings.SUPABASE_URL or not settings.SUPABASE_KEY:
            raise ValueError(
                "SUPABASE_URL e SUPABASE_KEY são necessários para usar Supabase Storage"
            )

        self.client: Client = create_client(
            supabase_url=settings.SUPABASE_URL,
            supabase_key=settings.SUPABASE_KEY,
        )

    async def upload_ingresso_pdf(
        self, file: BinaryIO, filename: str, ingresso_id: str
    ) -> str:
        """Faz upload de PDF de ingresso e retorna a URL pública."""
        bucket_name = settings.SUPABASE_BUCKET_INGRESSOS
        file_path = f"{ingresso_id}/{filename}"

        self.client.storage.from_(bucket_name).upload(
            path=file_path,
            file=_to_bytes(file),
            file_options={"content-type": "application/pdf", "upsert": "true"},
        )

        return self.client.storage.from_(bucket_name).get_public_url(file_path)

    async def upload_certificado_pdf(
        self, file: BinaryIO, filename: str, ingresso_id: str
    ) -> str:
        """Faz upload de PDF de certificado e retorna a URL pública."""
        bucket_name = settings.SUPABASE_BUCKET_CERTIFICADOS
        file_path = f"{ingresso_id}/{filename}"

        self.client.storage.from_(bucket_name).upload(
            path=file_path,
            file=_to_bytes(file),
            file_options={"content-type": "application/pdf", "upsert": "true"},
        )

        return self.client.storage.from_(bucket_name).get_public_url(file_path)

    async def upload_relatorio_pdf(
        self, file: BinaryIO, filename: str, evento_id: str
    ) -> str:
        """Faz upload de PDF de relatório e retorna a URL pública."""
        bucket_name = settings.SUPABASE_BUCKET_RELATORIOS
        file_path = f"{evento_id}/{filename}"

        self.client.storage.from_(bucket_name).upload(
            path=file_path,
            file=_to_bytes(file),
            file_options={"content-type": "application/pdf", "upsert": "true"},
        )

        return self.client.storage.from_(bucket_name).get_public_url(file_path)

    async def upload_foto_evento(
        self, file: BinaryIO | bytes, file_path: str, content_type: str
    ) -> str:
        """Faz upload de uma foto da galeria (UC08) e retorna o *path* do objeto.

        Diferente dos PDFs: o bucket de fotos é privado, então não devolvemos URL
        pública — o acesso é via URL assinada (`criar_signed_url`). O `file_path`
        já vem montado (`{evento_id}/{uuid}.{ext}`).
        """
        bucket_name = settings.SUPABASE_BUCKET_FOTOS

        self.client.storage.from_(bucket_name).upload(
            path=file_path,
            file=_to_bytes(file),
            file_options={"content-type": content_type, "upsert": "true"},
        )

        return file_path

    def criar_signed_url(self, file_path: str, expires_in: int = 3600) -> str:
        """Gera uma URL assinada temporária para um objeto do bucket de fotos."""
        bucket_name = settings.SUPABASE_BUCKET_FOTOS
        resposta = self.client.storage.from_(bucket_name).create_signed_url(
            file_path, expires_in
        )
        # O SDK devolve {"signedURL": "...", ...} (chaves variam entre versões).
        return resposta.get("signedURL") or resposta.get("signedUrl") or ""

    def remover_foto(self, file_path: str) -> None:
        """Remove um objeto do bucket de fotos (best-effort — erros são ignorados)."""
        bucket_name = settings.SUPABASE_BUCKET_FOTOS
        self.client.storage.from_(bucket_name).remove([file_path])


# Instância global (criada apenas se configurado)
supabase_storage = None
try:
    supabase_storage = SupabaseStorage()
except ValueError:
    # Supabase não configurado — funcionalidades degradam graciosamente
    pass
