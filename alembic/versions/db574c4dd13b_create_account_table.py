"""create account table

Revision ID: db574c4dd13b
Revises: db837f4d5767
Create Date: 2024-09-25 22:41:00.218900

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'db574c4dd13b'
down_revision: Union[str, None] = 'db837f4d5767'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
