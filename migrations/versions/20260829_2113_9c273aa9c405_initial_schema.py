"""initial schema

The baseline: the items and jobs tables as the entities define them. Generated
against an empty database so that this revision is the whole schema rather than
a diff against whatever a particular developer's database happened to contain.

Revision ID: 9c273aa9c405
Revises:
Create Date: 2026-08-29 21:13:16.535747

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "9c273aa9c405"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "items",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("value_str", sa.String(length=255), nullable=True),
        sa.Column("value_int", sa.Integer(), nullable=True),
        sa.Column("value_float", sa.Float(), nullable=True),
        sa.Column("created_date", sa.DateTime(), nullable=False),
        sa.Column("modified_date", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "jobs",
        # Not autoincremented: the id is minted by JobService before the
        # command carrying it is published.
        sa.Column("id", sa.String(length=32), nullable=False),
        sa.Column("command", sa.String(length=100), nullable=False),
        sa.Column(
            "status",
            sa.Enum("PENDING", "RUNNING", "SUCCEEDED", "FAILED", name="jobstatus"),
            nullable=False,
        ),
        sa.Column("result", sa.String(length=255), nullable=True),
        sa.Column("error", sa.String(length=1000), nullable=True),
        sa.Column("created_date", sa.DateTime(), nullable=False),
        sa.Column("modified_date", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("jobs")
    op.drop_table("items")
