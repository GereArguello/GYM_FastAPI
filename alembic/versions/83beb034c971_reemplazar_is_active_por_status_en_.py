"""reemplazar is_active por status en CustomerMembership

Revision ID: 83beb034c971
Revises: 13d982f9cbc4
Create Date: 2026-01-27 00:19:20.672202

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '83beb034c971'
down_revision: Union[str, Sequence[str], None] = '13d982f9cbc4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'customermembership',
        sa.Column(
            'status',
            sa.Enum(
                'ACTIVE',
                'PENDING',
                'INACTIVE',
                name='membershipstatusenum'
            ),
            nullable=True
        )
    )

    op.execute("""
        UPDATE customermembership
        SET status = CASE
            WHEN is_active = 1 THEN 'ACTIVE'
            ELSE 'INACTIVE'
        END
    """)

    op.drop_column('customermembership', 'is_active')


def downgrade() -> None:
    op.add_column(
        'customermembership',
        sa.Column('is_active', sa.BOOLEAN(), nullable=True)
    )

    op.execute("""
        UPDATE customermembership
        SET is_active = CASE
            WHEN status = 'ACTIVE' THEN true
            ELSE false
        END
    """)

    op.alter_column(
        'customermembership',
        'is_active',
        nullable=False
    )

    op.drop_column('customermembership', 'status')

