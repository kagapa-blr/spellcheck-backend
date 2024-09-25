"""create account table

Revision ID: d5b3247e5698
Revises: 54051c6a660f
Create Date: 2024-09-25 22:07:40.381685

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd5b3247e5698'
down_revision: Union[str, None] = '54051c6a660f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
