"""unique em pagamento (pedido_id, charge_id) e reembolso (pagamento_id)

Revision ID: e1f2a3b4c5d6
Revises: c7d8e9f0a1b2
Create Date: 2026-06-02 00:30:00.000000

Garante 1 pagamento por pedido, charge_id único e 1 reembolso por pagamento —
evita pagamento/estorno duplicado e o MultipleResultsFound em get_by_pedido_id.
"""

from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "e1f2a3b4c5d6"
down_revision: Union[str, Sequence[str], None] = "c7d8e9f0a1b2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_unique_constraint("uq_pagamento_pedido", "pagamentos", ["pedido_id"])
    op.create_unique_constraint("uq_pagamento_charge", "pagamentos", ["charge_id"])
    op.create_unique_constraint(
        "uq_reembolso_pagamento", "reembolsos", ["pagamento_id"]
    )


def downgrade() -> None:
    op.drop_constraint("uq_reembolso_pagamento", "reembolsos", type_="unique")
    op.drop_constraint("uq_pagamento_charge", "pagamentos", type_="unique")
    op.drop_constraint("uq_pagamento_pedido", "pagamentos", type_="unique")
