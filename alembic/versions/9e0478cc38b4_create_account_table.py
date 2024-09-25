"""create account table

Revision ID: 9e0478cc38b4
Revises: d5b3247e5698
Create Date: 2024-09-25 22:10:40.340838

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '9e0478cc38b4'
down_revision: Union[str, None] = 'd5b3247e5698'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
