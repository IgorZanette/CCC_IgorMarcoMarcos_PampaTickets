"""unique codigo cupom por evento

Revision ID: 2b9f6ccda677
Revises: c4db6338c75c
Create Date: 2026-05-23 22:30:00.000000

"""

from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "2b9f6ccda677"
down_revision: Union[str, Sequence[str], None] = "c4db6338c75c"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_unique_constraint(
        "uq_cupom_codigo_evento",
        "cupons",
        ["codigo", "evento_id"],
    )


def downgrade() -> None:
    op.drop_constraint("uq_cupom_codigo_evento", "cupons", type_="unique")
