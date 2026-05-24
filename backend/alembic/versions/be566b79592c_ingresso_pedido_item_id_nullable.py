"""ingresso pedido_item_id nullable

Revision ID: be566b79592c
Revises: 2b9f6ccda677
Create Date: 2026-05-24 10:00:00.000000

Permite ingressos sem PedidoItem (cortesias — UC06).
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "be566b79592c"
down_revision: Union[str, Sequence[str], None] = "2b9f6ccda677"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column(
        "ingressos",
        "pedido_item_id",
        existing_type=sa.UUID(),
        nullable=True,
    )


def downgrade() -> None:
    # CUIDADO: se existirem cortesias (ingressos com pedido_item_id NULL),
    # este downgrade vai falhar. Limpar/migrar os dados antes.
    op.alter_column(
        "ingressos",
        "pedido_item_id",
        existing_type=sa.UUID(),
        nullable=False,
    )
