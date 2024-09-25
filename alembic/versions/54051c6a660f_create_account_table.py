"""create account table

Revision ID: 54051c6a660f
Revises: d32b8887b413
Create Date: 2024-09-25 21:18:54.939373

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '54051c6a660f'
down_revision: Union[str, None] = 'd32b8887b413'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
