"""Add big field

Revision ID: 75703d76f893
Revises: 9ba56420afb2
Create Date: 2025-06-13 16:54:14.399193

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '75703d76f893'
down_revision = '9ba56420afb2'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('dealings', sa.Column('bid', sa.Integer(), nullable=True))
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('dealings', 'bid')
    # ### end Alembic commands ###
