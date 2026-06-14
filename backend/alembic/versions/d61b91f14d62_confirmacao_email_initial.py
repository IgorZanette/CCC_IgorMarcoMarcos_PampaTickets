"""confirmacao_email_initial

Revision ID: d61b91f14d62
Revises: b2c3d4e5f6a7
Create Date: 2026-06-13 00:00:00.000000

Placeholder para migração aplicada no banco mas não commitada.
Criou a tabela confirmacoes_email e colunas de confirmação legadas em usuarios.
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "d61b91f14d62"
down_revision: Union[str, Sequence[str], None] = "d1a2b3c4e5f6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "confirmacoes_email",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("usuario_id", sa.Uuid(), nullable=False),
        sa.Column("codigo_hash", sa.String(length=64), nullable=False),
        sa.Column("tentativas", sa.Integer(), nullable=False),
        sa.Column("token", sa.String(length=255), nullable=False),
        sa.Column(
            "status",
            sa.Enum("PENDENTE", "UTILIZADO", "EXPIRADO", name="statusconfirmacaoemail"),
            nullable=False,
        ),
        sa.Column(
            "criado_em",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("expira_em", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["usuario_id"], ["usuarios.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("token"),
    )
    op.add_column("usuarios", sa.Column("confirmacao_token", sa.String(length=255), nullable=True))
    op.add_column("usuarios", sa.Column("confirmacao_expira_em", sa.DateTime(timezone=True), nullable=True))
    op.create_unique_constraint("usuarios_confirmacao_token_key", "usuarios", ["confirmacao_token"])


def downgrade() -> None:
    op.drop_constraint("usuarios_confirmacao_token_key", "usuarios", type_="unique")
    op.drop_column("usuarios", "confirmacao_expira_em")
    op.drop_column("usuarios", "confirmacao_token")
    op.drop_table("confirmacoes_email")
    op.execute("DROP TYPE IF EXISTS statusconfirmacaoemail")
