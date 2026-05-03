from typing import BinaryIO

from supabase import Client, create_client

from app.core.config import settings


class SupabaseStorage:
    """Cliente para upload de arquivos no Supabase Storage."""

    def __init__(self):
        if not settings.SUPABASE_URL or not settings.SUPABASE_KEY:
            raise ValueError("SUPABASE_URL e SUPABASE_KEY são necessários para usar Supabase Storage")

        self.client: Client = create_client(
            supabase_url=settings.SUPABASE_URL,
            supabase_key=settings.SUPABASE_KEY
        )

    async def upload_ingresso_pdf(
        self,
        file: BinaryIO,
        filename: str,
        ingresso_id: str
    ) -> str:
        """
        Faz upload de PDF de ingresso para o Supabase Storage.

        Args:
            file: Arquivo binário do PDF
            filename: Nome do arquivo (ex: "ingresso_123.pdf")
            ingresso_id: ID do ingresso para organização

        Returns:
            URL pública do arquivo no Supabase
        """
        bucket_name = settings.SUPABASE_BUCKET_INGRESSOS

        # Caminho no bucket: ingressos/{ingresso_id}/{filename}
        file_path = f"{ingresso_id}/{filename}"

        # Upload do arquivo
        response = self.client.storage.from_(bucket_name).upload(
            path=file_path,
            file=file,
            file_options={"content-type": "application/pdf"}
        )

        if response.status_code != 200:
            raise Exception(f"Erro no upload: {response.json()}")

        # Obter URL pública
        public_url = self.client.storage.from_(bucket_name).get_public_url(file_path)

        return public_url

    async def upload_certificado_pdf(
        self,
        file: BinaryIO,
        filename: str,
        ingresso_id: str
    ) -> str:
        """
        Faz upload de PDF de certificado para o Supabase Storage.

        Args:
            file: Arquivo binário do PDF
            filename: Nome do arquivo (ex: "certificado_123.pdf")
            ingresso_id: ID do ingresso para organização

        Returns:
            URL pública do arquivo no Supabase
        """
        bucket_name = settings.SUPABASE_BUCKET_CERTIFICADOS

        # Caminho no bucket: certificados/{ingresso_id}/{filename}
        file_path = f"{ingresso_id}/{filename}"

        # Upload do arquivo
        response = self.client.storage.from_(bucket_name).upload(
            path=file_path,
            file=file,
            file_options={"content-type": "application/pdf"}
        )

        if response.status_code != 200:
            raise Exception(f"Erro no upload: {response.json()}")

        # Obter URL pública
        public_url = self.client.storage.from_(bucket_name).get_public_url(file_path)

        return public_url

    async def upload_relatorio_pdf(
        self,
        file: BinaryIO,
        filename: str,
        evento_id: str
    ) -> str:
        """
        Faz upload de PDF de relatório para o Supabase Storage.

        Args:
            file: Arquivo binário do PDF
            filename: Nome do arquivo (ex: "relatorio_evento_123.pdf")
            evento_id: ID do evento para organização

        Returns:
            URL pública do arquivo no Supabase
        """
        bucket_name = settings.SUPABASE_BUCKET_RELATORIOS

        # Caminho no bucket: relatorios/{evento_id}/{filename}
        file_path = f"{evento_id}/{filename}"

        # Upload do arquivo
        response = self.client.storage.from_(bucket_name).upload(
            path=file_path,
            file=file,
            file_options={"content-type": "application/pdf"}
        )

        if response.status_code != 200:
            raise Exception(f"Erro no upload: {response.json()}")

        # Obter URL pública
        public_url = self.client.storage.from_(bucket_name).get_public_url(file_path)

        return public_url


# Instância global (criada apenas se configurado)
supabase_storage = None
try:
    supabase_storage = SupabaseStorage()
except ValueError:
    # Supabase não configurado, funcionalidades ficam desabilitadas
    pass