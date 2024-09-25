"""create account table

Revision ID: db837f4d5767
Revises: bbe89026b789
Create Date: 2024-09-25 22:12:33.062797

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'db837f4d5767'
down_revision: Union[str, None] = 'bbe89026b789'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
