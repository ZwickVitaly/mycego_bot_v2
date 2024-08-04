"""chat added

Revision ID: 4305734c1afc
Revises: addfbb7b2797
Create Date: 2024-08-04 15:10:07.839780

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "4305734c1afc"
down_revision: Union[str, None] = "addfbb7b2797"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table(
        "chats",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("admin", sa.Boolean(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )

    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###

    op.drop_table("chats")
    # ### end Alembic commands ###