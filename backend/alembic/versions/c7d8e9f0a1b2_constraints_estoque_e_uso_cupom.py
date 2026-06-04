"""constraints de estoque do lote e uso do cupom

Revision ID: c7d8e9f0a1b2
Revises: be566b79592c
Create Date: 2026-06-02 00:00:00.000000

Rede de segurança no banco contra contadores inválidos (oversell / underflow):
- lotes_ingresso: quantidade_vendida entre 0 e quantidade_total
- cupons: quantidade_usada >= 0
A prevenção principal de corrida é o SELECT ... FOR UPDATE nos services; estas
constraints garantem a integridade mesmo diante de qualquer caminho inesperado.
"""

from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "c7d8e9f0a1b2"
down_revision: Union[str, Sequence[str], None] = "be566b79592c"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_check_constraint(
        "ck_lote_vendida_nao_negativa",
        "lotes_ingresso",
        "quantidade_vendida >= 0",
    )
    op.create_check_constraint(
        "ck_lote_vendida_ate_total",
        "lotes_ingresso",
        "quantidade_vendida <= quantidade_total",
    )
    op.create_check_constraint(
        "ck_cupom_usada_nao_negativa",
        "cupons",
        "quantidade_usada >= 0",
    )


def downgrade() -> None:
    op.drop_constraint("ck_cupom_usada_nao_negativa", "cupons", type_="check")
    op.drop_constraint("ck_lote_vendida_ate_total", "lotes_ingresso", type_="check")
    op.drop_constraint(
        "ck_lote_vendida_nao_negativa", "lotes_ingresso", type_="check"
    )
