"""create account table

Revision ID: bbe89026b789
Revises: 9e0478cc38b4
Create Date: 2024-09-25 22:11:21.230456

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'bbe89026b789'
down_revision: Union[str, None] = '9e0478cc38b4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
