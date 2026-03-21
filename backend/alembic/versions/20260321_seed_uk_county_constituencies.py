"""Seed all UK county constituencies.

Populates the constituency table with all ceremonial counties of England,
council areas of Scotland, principal areas of Wales, and the counties of
Northern Ireland.  Also adds a ``region`` column and removes the old
placeholder 'Default' constituency created in an earlier migration.

Revision ID: 20260321_seed
Revises: c84653e7a320
Create Date: 2026-03-21

"""
from typing import Sequence, Union
from uuid import uuid4

import sqlalchemy as sa
from alembic import op

revision: str = "20260321_seed"
down_revision: Union[str, None] = "c84653e7a320"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# ---------------------------------------------------------------------------
# Complete list of UK counties / council areas organised by country.
# Each entry: (name, country, region)
# ---------------------------------------------------------------------------

ENGLAND_COUNTIES: list[tuple[str, str]] = [
    # East Midlands
    ("Derbyshire", "East Midlands"),
    ("Leicestershire", "East Midlands"),
    ("Lincolnshire", "East Midlands"),
    ("Northamptonshire", "East Midlands"),
    ("Nottinghamshire", "East Midlands"),
    ("Rutland", "East Midlands"),
    # East of England
    ("Bedfordshire", "East of England"),
    ("Cambridgeshire", "East of England"),
    ("Essex", "East of England"),
    ("Hertfordshire", "East of England"),
    ("Norfolk", "East of England"),
    ("Suffolk", "East of England"),
    # London
    ("Greater London", "London"),
    # North East
    ("County Durham", "North East"),
    ("Northumberland", "North East"),
    ("Tyne and Wear", "North East"),
    # North West
    ("Cheshire", "North West"),
    ("Cumbria", "North West"),
    ("Greater Manchester", "North West"),
    ("Lancashire", "North West"),
    ("Merseyside", "North West"),
    # South East
    ("Berkshire", "South East"),
    ("Buckinghamshire", "South East"),
    ("East Sussex", "South East"),
    ("Hampshire", "South East"),
    ("Isle of Wight", "South East"),
    ("Kent", "South East"),
    ("Oxfordshire", "South East"),
    ("Surrey", "South East"),
    ("West Sussex", "South East"),
    # South West
    ("Bristol", "South West"),
    ("Cornwall", "South West"),
    ("Devon", "South West"),
    ("Dorset", "South West"),
    ("Gloucestershire", "South West"),
    ("Somerset", "South West"),
    ("Wiltshire", "South West"),
    # West Midlands
    ("Herefordshire", "West Midlands"),
    ("Shropshire", "West Midlands"),
    ("Staffordshire", "West Midlands"),
    ("Warwickshire", "West Midlands"),
    ("West Midlands", "West Midlands"),
    ("Worcestershire", "West Midlands"),
    # Yorkshire and the Humber
    ("East Riding of Yorkshire", "Yorkshire and the Humber"),
    ("North Yorkshire", "Yorkshire and the Humber"),
    ("South Yorkshire", "Yorkshire and the Humber"),
    ("West Yorkshire", "Yorkshire and the Humber"),
]

SCOTLAND_COUNCIL_AREAS: list[str] = [
    "Aberdeen City",
    "Aberdeenshire",
    "Angus",
    "Argyll and Bute",
    "City of Edinburgh",
    "Clackmannanshire",
    "Dumfries and Galloway",
    "Dundee City",
    "East Ayrshire",
    "East Dunbartonshire",
    "East Lothian",
    "East Renfrewshire",
    "Falkirk",
    "Fife",
    "Glasgow City",
    "Highland",
    "Inverclyde",
    "Midlothian",
    "Moray",
    "Na h-Eileanan Siar",
    "North Ayrshire",
    "North Lanarkshire",
    "Orkney Islands",
    "Perth and Kinross",
    "Renfrewshire",
    "Scottish Borders",
    "Shetland Islands",
    "South Ayrshire",
    "South Lanarkshire",
    "Stirling",
    "West Dunbartonshire",
    "West Lothian",
]

WALES_PRINCIPAL_AREAS: list[str] = [
    "Blaenau Gwent",
    "Bridgend",
    "Caerphilly",
    "Cardiff",
    "Carmarthenshire",
    "Ceredigion",
    "Conwy",
    "Denbighshire",
    "Flintshire",
    "Gwynedd",
    "Isle of Anglesey",
    "Merthyr Tydfil",
    "Monmouthshire",
    "Neath Port Talbot",
    "Newport",
    "Pembrokeshire",
    "Powys",
    "Rhondda Cynon Taf",
    "Swansea",
    "Torfaen",
    "Vale of Glamorgan",
    "Wrexham",
]

NI_COUNTIES: list[str] = [
    "Antrim",
    "Armagh",
    "Down",
    "Fermanagh",
    "Londonderry",
    "Tyrone",
]


def _build_rows() -> list[dict]:
    """Return a flat list of row dicts ready for bulk insert."""
    rows: list[dict] = []

    for name, region in ENGLAND_COUNTIES:
        rows.append({
            "id": str(uuid4()),
            "name": name,
            "country": "England",
            "county": name,
            "region": region,
            "is_active": True,
        })

    for name in SCOTLAND_COUNCIL_AREAS:
        rows.append({
            "id": str(uuid4()),
            "name": name,
            "country": "Scotland",
            "county": name,
            "region": None,
            "is_active": True,
        })

    for name in WALES_PRINCIPAL_AREAS:
        rows.append({
            "id": str(uuid4()),
            "name": name,
            "country": "Wales",
            "county": name,
            "region": None,
            "is_active": True,
        })

    for name in NI_COUNTIES:
        rows.append({
            "id": str(uuid4()),
            "name": name,
            "country": "Northern Ireland",
            "county": name,
            "region": None,
            "is_active": True,
        })

    return rows


def upgrade() -> None:
    # Add the region column
    op.add_column("constituency", sa.Column("region", sa.String(255), nullable=True))
    op.create_index(op.f("ix_constituency_region"), "constituency", ["region"])

    # Make country NOT NULL (update any existing NULL values first)
    conn = op.get_bind()
    conn.execute(
        sa.text("UPDATE constituency SET country = 'England' WHERE country IS NULL")
    )
    op.alter_column("constituency", "country", existing_type=sa.String(255), nullable=False)

    # Remove the old placeholder 'Default' constituency if it exists
    conn.execute(sa.text("DELETE FROM constituency WHERE name = 'Default'"))

    # Seed all UK county constituencies
    rows = _build_rows()
    for row in rows:
        conn.execute(
            sa.text("""
                INSERT INTO constituency (id, name, country, county, region, is_active)
                VALUES (:id, :name, :country, :county, :region, :is_active)
                ON CONFLICT (name) DO NOTHING
            """),
            row,
        )


def downgrade() -> None:
    conn = op.get_bind()

    # Remove all seeded constituencies
    countries = ("England", "Scotland", "Wales", "Northern Ireland")
    for country in countries:
        conn.execute(
            sa.text("DELETE FROM constituency WHERE country = :country"),
            {"country": country},
        )

    # Re-insert the placeholder default constituency
    conn.execute(
        sa.text("""
            INSERT INTO constituency (id, name, country, county, is_active)
            VALUES (:id, 'Default', 'UK', NULL, true)
            ON CONFLICT (name) DO NOTHING
        """),
        {"id": "00000000-0000-0000-0000-000000000001"},
    )

    # Make country nullable again
    op.alter_column("constituency", "country", existing_type=sa.String(255), nullable=True)

    # Drop the region column and its index
    op.drop_index(op.f("ix_constituency_region"), table_name="constituency")
    op.drop_column("constituency", "region")
