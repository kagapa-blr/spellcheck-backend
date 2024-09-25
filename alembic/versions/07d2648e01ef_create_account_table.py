"""create account table

Revision ID: 07d2648e01ef
Revises: a961c8dcb837
Create Date: 2024-09-25 23:04:27.921609

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '07d2648e01ef'
down_revision: Union[str, None] = 'a961c8dcb837'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
