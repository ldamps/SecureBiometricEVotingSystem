"""Standalone seed script for UK county constituencies.

Usage:
    python -m seeds.seed_constituencies

Inserts all UK ceremonial counties, Scottish council areas, Welsh principal
areas, and Northern Ireland counties into the constituency table.  Skips
rows that already exist (matched by name).

This script is idempotent — safe to run multiple times.
"""

import sys
import os
from uuid import uuid4

# Ensure the backend package is importable when running from the backend/ dir
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from app.db import engine

# ---------------------------------------------------------------------------
# UK Counties / Council Areas
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


def seed() -> None:
    """Insert all UK county constituencies into the database."""
    insert_sql = text("""
        INSERT INTO constituency (id, name, country, county, region, is_active)
        VALUES (:id, :name, :country, :county, :region, :is_active)
        ON CONFLICT (name) DO NOTHING
    """)

    rows_inserted = 0

    with engine.begin() as conn:
        # England
        for name, region in ENGLAND_COUNTIES:
            result = conn.execute(insert_sql, {
                "id": str(uuid4()),
                "name": name,
                "country": "England",
                "county": name,
                "region": region,
                "is_active": True,
            })
            rows_inserted += result.rowcount

        # Scotland
        for name in SCOTLAND_COUNCIL_AREAS:
            result = conn.execute(insert_sql, {
                "id": str(uuid4()),
                "name": name,
                "country": "Scotland",
                "county": name,
                "region": None,
                "is_active": True,
            })
            rows_inserted += result.rowcount

        # Wales
        for name in WALES_PRINCIPAL_AREAS:
            result = conn.execute(insert_sql, {
                "id": str(uuid4()),
                "name": name,
                "country": "Wales",
                "county": name,
                "region": None,
                "is_active": True,
            })
            rows_inserted += result.rowcount

        # Northern Ireland
        for name in NI_COUNTIES:
            result = conn.execute(insert_sql, {
                "id": str(uuid4()),
                "name": name,
                "country": "Northern Ireland",
                "county": name,
                "region": None,
                "is_active": True,
            })
            rows_inserted += result.rowcount

    print(f"Seeding complete: {rows_inserted} constituencies inserted.")


if __name__ == "__main__":
    seed()
