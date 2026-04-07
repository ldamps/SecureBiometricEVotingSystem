"""replace county constituencies with 650 parliamentary constituencies

Revision ID: 72e1af3f04a4
Revises: 60364610e239
Create Date: 2026-04-03 20:05:50.208922

"""
from typing import Sequence, Union
from uuid import uuid4
import json
import os

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '72e1af3f04a4'
down_revision: Union[str, None] = '60364610e239'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()

    # Clear existing foreign key references so we can replace constituencies
    # Null out voter constituency_id (will be re-resolved from address postcode)
    conn.execute(sa.text("UPDATE voter SET constituency_id = NULL"))

    # Clear candidate constituency links
    conn.execute(sa.text("DELETE FROM candidate"))

    # Clear referendum_constituency links
    conn.execute(sa.text("DELETE FROM referendum_constituency"))

    # Delete all old county-based constituencies
    conn.execute(sa.text("DELETE FROM constituency"))

    # Load the 650 parliamentary constituencies + Overseas
    seed_path = os.path.join(
        os.path.dirname(__file__), "..", "..", "seeds", "uk_constituencies_2024.json"
    )
    with open(seed_path) as f:
        constituencies = json.load(f)

    # Insert all 650 constituencies
    for c in constituencies:
        conn.execute(
            sa.text(
                "INSERT INTO constituency (id, name, country, county, region, is_active) "
                "VALUES (:id, :name, :country, NULL, NULL, true) "
                "ON CONFLICT (name) DO NOTHING"
            ),
            {"id": str(uuid4()), "name": c["name"], "country": c["country"]},
        )

    # Add the Overseas constituency
    conn.execute(
        sa.text(
            "INSERT INTO constituency (id, name, country, county, region, is_active) "
            "VALUES (:id, 'Overseas', 'Overseas', NULL, NULL, true) "
            "ON CONFLICT (name) DO NOTHING"
        ),
        {"id": str(uuid4())},
    )


def downgrade() -> None:
    # Downgrade is destructive — just clear and let old seeds re-run
    conn = op.get_bind()
    conn.execute(sa.text("UPDATE voter SET constituency_id = NULL"))
    conn.execute(sa.text("DELETE FROM candidate"))
    conn.execute(sa.text("DELETE FROM referendum_constituency"))
    conn.execute(sa.text("DELETE FROM constituency"))
