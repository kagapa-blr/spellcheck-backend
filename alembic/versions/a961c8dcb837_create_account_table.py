"""create account table

Revision ID: a961c8dcb837
Revises: db574c4dd13b
Create Date: 2024-09-25 23:03:31.977437

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a961c8dcb837'
down_revision: Union[str, None] = 'db574c4dd13b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
