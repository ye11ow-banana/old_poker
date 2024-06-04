"""Update enum type for suit

Revision ID: 8c0669703298
Revises: 0552e4715206
Create Date: 2024-06-04 20:23:57.568827

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "8c0669703298"
down_revision = "0552e4715206"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Step 1: Create the new enum type
    op.execute("CREATE TYPE new_suit AS ENUM ('H', 'D', 'C', 'S')")

    # Step 2: Update the columns in the 'sets' table to use the new enum type
    op.execute(
        """
        ALTER TABLE sets 
        ALTER COLUMN trump_suit 
        TYPE new_suit 
        USING trump_suit::text::new_suit
    """
    )

    # Step 2: Update the columns in the 'cards' table to use the new enum type
    op.execute(
        """
        ALTER TABLE cards 
        ALTER COLUMN suit 
        TYPE new_suit 
        USING suit::text::new_suit
    """
    )

    # Step 3: Drop the old enum type
    op.execute("DROP TYPE suit")

    # Step 4: Rename the new enum type to the original name
    op.execute("ALTER TYPE new_suit RENAME TO suit")


def downgrade() -> None:
    # Reverse the above operations for downgrade
    # Step 1: Create the old enum type
    op.execute(
        "CREATE TYPE suit AS ENUM ('hearts', 'diamonds', 'clubs', 'spades')"
    )

    # Step 2: Update the columns in the 'sets' table to use the old enum type
    op.execute(
        """
        ALTER TABLE sets 
        ALTER COLUMN trump_suit 
        TYPE suit 
        USING trump_suit::text::suit
    """
    )

    # Step 2: Update the columns in the 'cards' table to use the old enum type
    op.execute(
        """
        ALTER TABLE cards 
        ALTER COLUMN suit 
        TYPE suit 
        USING suit::text::suit
    """
    )

    # Step 3: Drop the new enum type
    op.execute("DROP TYPE new_suit")
