import uuid
from datetime import datetime

from pydantic import BaseModel

from app.models.foto import FotoEvento


class FotoResponse(BaseModel):
    id: uuid.UUID
    evento_id: uuid.UUID
    url_thumbnail: str
    url_original: str
    publicado_em: datetime

    model_config = {"from_attributes": True}

    @classmethod
    def from_foto(
        cls, foto: FotoEvento, *, url_thumbnail: str, url_original: str
    ) -> "FotoResponse":
        # As URLs assinadas são geradas no service (o bucket é privado); o que
        # está persistido em `foto.url_*` é apenas o path do objeto.
        return cls(
            id=foto.id,
            evento_id=foto.evento_id,
            url_thumbnail=url_thumbnail,
            url_original=url_original,
            publicado_em=foto.publicado_em,
        )
