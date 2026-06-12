"""endurece_recuperacao_senha

Código de recuperação passa a ser armazenado como HMAC-SHA256 (codigo_hash)
e ganha contador de tentativas erradas (anti-brute-force).

Revision ID: b2c3d4e5f6a7
Revises: d1a2b3c4e5f6
Create Date: 2026-06-11 21:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "b2c3d4e5f6a7"
down_revision: Union[str, Sequence[str], None] = "d1a2b3c4e5f6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Registros antigos guardam o código em claro e não têm hash. São efêmeros
    # (15 minutos de validade), então é seguro descartá-los na migração.
    op.execute("DELETE FROM recuperacao_senhas")
    op.drop_column("recuperacao_senhas", "codigo")
    op.add_column(
        "recuperacao_senhas",
        sa.Column("codigo_hash", sa.String(length=64), nullable=False),
    )
    op.add_column(
        "recuperacao_senhas",
        sa.Column("tentativas", sa.Integer(), nullable=False, server_default="0"),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.execute("DELETE FROM recuperacao_senhas")
    op.drop_column("recuperacao_senhas", "tentativas")
    op.drop_column("recuperacao_senhas", "codigo_hash")
    op.add_column(
        "recuperacao_senhas",
        sa.Column("codigo", sa.String(length=6), nullable=False),
    )
