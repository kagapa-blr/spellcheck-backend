"""create account table

Revision ID: 74be96106057
Revises: 07d2648e01ef
Create Date: 2024-09-27 20:16:17.647284

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '74be96106057'
down_revision: Union[str, None] = '07d2648e01ef'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
