"""adiciona_tabela_recuperacao_senhas

Revision ID: d1a2b3c4e5f6
Revises: e1f2a3b4c5d6
Create Date: 2026-06-07 10:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "d1a2b3c4e5f6"
down_revision: Union[str, Sequence[str], None] = "e1f2a3b4c5d6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "recuperacao_senhas",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("usuario_id", sa.Uuid(), nullable=False),
        sa.Column("codigo", sa.String(length=6), nullable=False),
        sa.Column("token", sa.String(length=255), nullable=False),
        sa.Column(
            "status",
            sa.Enum("PENDENTE", "VALIDADO", "UTILIZADO", "EXPIRADO", name="statusrecuperacao"),
            nullable=False,
        ),
        sa.Column(
            "criado_em",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("expira_em", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["usuario_id"],
            ["usuarios.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("token"),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table("recuperacao_senhas")
