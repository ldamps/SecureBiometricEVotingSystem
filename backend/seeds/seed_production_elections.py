"""Seed production elections, parties, candidates, and referendums.

Creates realistic UK elections with major parties and candidates, plus
referendums, ready for the live system.

Usage:
    cd backend
    python -m seeds.seed_production_elections

Prerequisites:
    - Database is running and migrated.
    - Constituencies are seeded (python -m seeds.seed_constituencies).
"""

import sys
import os
from uuid import uuid4

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from app.db import engine

# ---------------------------------------------------------------------------
# Parties (UK major parties)
# ---------------------------------------------------------------------------

PARTIES = [
    {"id": str(uuid4()), "name": "Conservative Party", "abbr": "CON"},
    {"id": str(uuid4()), "name": "Labour Party", "abbr": "LAB"},
    {"id": str(uuid4()), "name": "Liberal Democrats", "abbr": "LD"},
    {"id": str(uuid4()), "name": "Scottish National Party", "abbr": "SNP"},
    {"id": str(uuid4()), "name": "Green Party", "abbr": "GRN"},
    {"id": str(uuid4()), "name": "Reform UK", "abbr": "REF"},
    {"id": str(uuid4()), "name": "Plaid Cymru", "abbr": "PC"},
    {"id": str(uuid4()), "name": "Sinn Féin", "abbr": "SF"},
    {"id": str(uuid4()), "name": "Democratic Unionist Party", "abbr": "DUP"},
    {"id": str(uuid4()), "name": "Alliance Party", "abbr": "ALL"},
]

# ---------------------------------------------------------------------------
# Elections
# ---------------------------------------------------------------------------

ELECTIONS = [
    {
        "id": str(uuid4()),
        "title": "2026 UK General Election",
        "election_type": "GENERAL",
        "scope": "NATIONAL",
        "allocation_method": "FPTP",
        "constituency_country": "England",
        "constituency_limit": 10,
    },
    {
        "id": str(uuid4()),
        "title": "2026 Scottish Parliament Election",
        "election_type": "SCOTTISH_PARLIAMENT",
        "scope": "REGIONAL",
        "allocation_method": "AMS",
        "constituency_country": "Scotland",
        "constituency_limit": 6,
    },
    {
        "id": str(uuid4()),
        "title": "2026 Northern Ireland Assembly Election",
        "election_type": "NORTHERN_IRELAND_ASSEMBLY",
        "scope": "REGIONAL",
        "allocation_method": "STV",
        "constituency_country": "Northern Ireland",
        "constituency_limit": 5,
    },
    {
        "id": str(uuid4()),
        "title": "2026 London Assembly Election",
        "election_type": "LONDON_ASSEMBLY",
        "scope": "REGIONAL",
        "allocation_method": "AMS",
        "constituency_country": "England",
        "constituency_limit": 4,
    },
    {
        "id": str(uuid4()),
        "title": "2026 Local Council Elections (England & Wales)",
        "election_type": "LOCAL_ENGLAND_WALES",
        "scope": "LOCAL",
        "allocation_method": "FPTP",
        "constituency_country": "Wales",
        "constituency_limit": 4,
    },
]

# ---------------------------------------------------------------------------
# Referendums
# ---------------------------------------------------------------------------

REFERENDUMS = [
    {
        "id": str(uuid4()),
        "title": "National Voting Age Referendum",
        "question": "Should the minimum voting age in the United Kingdom be lowered from 18 to 16 for all elections and referendums?",
        "description": "This referendum seeks to determine public opinion on whether 16 and 17 year olds should be granted the right to vote in all UK-wide elections and referendums.",
        "scope": "NATIONAL",
        "constituency_country": None,
    },
    {
        "id": str(uuid4()),
        "title": "Scottish Independence Referendum",
        "question": "Should Scotland be an independent country?",
        "description": "A consultative referendum on whether Scotland should become an independent sovereign state, separate from the United Kingdom.",
        "scope": "REGIONAL",
        "constituency_country": "Scotland",
        "constituency_limit": 5,
    },
    {
        "id": str(uuid4()),
        "title": "Welsh Language in Schools Referendum",
        "question": "Should Welsh language education be mandatory in all primary and secondary schools in Wales?",
        "description": "This referendum asks whether the Welsh Government should mandate Welsh language instruction as a core subject across all schools in Wales.",
        "scope": "REGIONAL",
        "constituency_country": "Wales",
        "constituency_limit": 4,
    },
]

# ---------------------------------------------------------------------------
# Candidate name pools per party index
# ---------------------------------------------------------------------------

CANDIDATE_POOLS = [
    # CON
    [("James", "Hartley"), ("Sarah", "Pemberton"), ("William", "Ashworth"), ("Charlotte", "Forsyth"),
     ("Edward", "Blackwood"), ("Victoria", "Langton"), ("George", "Whitfield"), ("Eleanor", "Prescott"),
     ("Richard", "Ainsworth"), ("Margaret", "Thornton")],
    # LAB
    [("Michael", "Brennan"), ("Angela", "Whitmore"), ("David", "O'Sullivan"), ("Catherine", "Redmond"),
     ("Stephen", "Gallagher"), ("Rachel", "Houghton"), ("Thomas", "Kavanagh"), ("Helen", "Patel"),
     ("Andrew", "McDonnell"), ("Jennifer", "Okonkwo")],
    # LD
    [("Simon", "Cartwright"), ("Fiona", "Dalrymple"), ("Robert", "Wainwright"), ("Diana", "Ellison"),
     ("Timothy", "Greenhalgh"), ("Susan", "Ashby"), ("Mark", "Townsend"), ("Alison", "Fairbanks"),
     ("Jonathan", "Hurst"), ("Chloe", "Barrington")],
    # SNP
    [("Hamish", "MacLeod"), ("Catriona", "Fraser"), ("Douglas", "Campbell"), ("Moira", "Henderson"),
     ("Ewan", "Robertson"), ("Fiona", "Stewart"), ("Callum", "MacDonald"), ("Isla", "Murray"),
     ("Rory", "Thomson"), ("Eilidh", "Davidson")],
    # GRN
    [("Oliver", "Greenfield"), ("Zara", "Thornberry"), ("Ethan", "Rivers"), ("Megan", "Ashford"),
     ("Lucas", "Birchwood"), ("Amira", "Khoury"), ("Felix", "Hawthorn"), ("Priya", "Sharma"),
     ("Nathaniel", "Oakley"), ("Sophia", "Park")],
    # REF
    [("Patrick", "Stanton"), ("Louise", "Kingsley"), ("Brian", "Warburton"), ("Deborah", "Cromwell"),
     ("Kevin", "Hardcastle"), ("Sandra", "Bainbridge"), ("Martin", "Drayton"), ("Carol", "Metcalfe"),
     ("Gary", "Fielding"), ("Janet", "Rycroft")],
    # PC
    [("Rhys", "ap Gruffydd"), ("Cerys", "Morgan"), ("Gareth", "Llewellyn"), ("Bronwen", "Pritchard"),
     ("Owain", "Davies"), ("Sian", "Griffiths"), ("Iwan", "Jones"), ("Nia", "Williams"),
     ("Dafydd", "Evans"), ("Mair", "Rees")],
    # SF
    [("Sean", "O'Brien"), ("Mairead", "Ni Dhomhnaill"), ("Ciaran", "Murphy"), ("Siobhan", "Kelly"),
     ("Padraig", "Quinn"), ("Aisling", "Doherty"), ("Declan", "Maguire"), ("Grainne", "Byrne"),
     ("Eoin", "Gallagher"), ("Niamh", "Flanagan")],
    # DUP
    [("William", "Johnston"), ("Ruth", "Crawford"), ("Samuel", "McAllister"), ("Elizabeth", "Hamilton"),
     ("Robert", "Baxter"), ("Dorothy", "Caldwell"), ("Thomas", "McIlroy"), ("Anne", "Patterson"),
     ("John", "Cummings"), ("Patricia", "Bell")],
    # ALL
    [("Daniel", "Carson"), ("Emma", "Reilly"), ("Stephen", "Neeson"), ("Claire", "Armstrong"),
     ("Peter", "McKenna"), ("Hannah", "Boyd"), ("David", "Wallace"), ("Laura", "Dillon"),
     ("Mark", "Kirk"), ("Sarah", "Reid")],
]

# Which parties stand in which elections (by index into PARTIES)
ELECTION_PARTY_MAP = {
    "GENERAL": [0, 1, 2, 4, 5],             # CON, LAB, LD, GRN, REF
    "SCOTTISH_PARLIAMENT": [0, 1, 2, 3, 4],  # CON, LAB, LD, SNP, GRN
    "NORTHERN_IRELAND_ASSEMBLY": [7, 8, 9, 1, 4],  # SF, DUP, ALL, LAB, GRN
    "LONDON_ASSEMBLY": [0, 1, 2, 4, 5],      # CON, LAB, LD, GRN, REF
    "LOCAL_ENGLAND_WALES": [0, 1, 2, 4, 6],  # CON, LAB, LD, GRN, PC
}


def seed() -> None:
    insert_party = text("""
        INSERT INTO party (id, party_name, abbreviation, is_active, created_at, updated_at)
        VALUES (:id, :party_name, :abbreviation, TRUE, NOW(), NOW())
        ON CONFLICT (party_name) DO NOTHING
    """)

    insert_election = text("""
        INSERT INTO election (id, title, election_type, scope, allocation_method, status,
                              voting_opens, voting_closes, created_at, updated_at)
        VALUES (:id, :title, :election_type, :scope, :allocation_method, 'OPEN',
                NOW(), NOW() + INTERVAL '30 days', NOW(), NOW())
        ON CONFLICT DO NOTHING
    """)

    insert_election_constituency = text("""
        INSERT INTO election_constituency (election_id, constituency_id)
        VALUES (:election_id, :constituency_id)
        ON CONFLICT DO NOTHING
    """)

    insert_candidate = text("""
        INSERT INTO candidate (id, election_id, constituency_id, first_name, last_name, party_id, is_active)
        VALUES (:id, :election_id, :constituency_id, :first_name, :last_name, :party_id, TRUE)
        ON CONFLICT DO NOTHING
    """)

    insert_referendum = text("""
        INSERT INTO referendum (id, title, question, description, scope, status,
                                voting_opens, voting_closes, is_active, created_at, updated_at)
        VALUES (:id, :title, :question, :description, :scope, 'OPEN',
                NOW(), NOW() + INTERVAL '30 days', TRUE, NOW(), NOW())
        ON CONFLICT DO NOTHING
    """)

    insert_referendum_constituency = text("""
        INSERT INTO referendum_constituency (referendum_id, constituency_id)
        VALUES (:referendum_id, :constituency_id)
        ON CONFLICT DO NOTHING
    """)

    with engine.begin() as conn:
        # ── 1. Seed parties ──
        party_count = 0
        for p in PARTIES:
            r = conn.execute(insert_party, {
                "id": p["id"],
                "party_name": p["name"],
                "abbreviation": p["abbr"],
            })
            party_count += r.rowcount

        # Resolve actual IDs (in case parties already existed)
        for p in PARTIES:
            row = conn.execute(
                text("SELECT id FROM party WHERE party_name = :name"),
                {"name": p["name"]},
            ).fetchone()
            if row:
                p["id"] = str(row[0])

        print(f"Parties: {party_count} inserted ({len(PARTIES)} total)")

        # ── 2. Seed elections ──
        election_count = 0
        for e in ELECTIONS:
            r = conn.execute(insert_election, {
                "id": e["id"],
                "title": e["title"],
                "election_type": e["election_type"],
                "scope": e["scope"],
                "allocation_method": e["allocation_method"],
            })
            election_count += r.rowcount

            # Resolve actual ID
            row = conn.execute(
                text("SELECT id FROM election WHERE title = :title"),
                {"title": e["title"]},
            ).fetchone()
            if row:
                e["id"] = str(row[0])

        print(f"Elections: {election_count} inserted ({len(ELECTIONS)} total)")

        # ── 3. Link constituencies to elections and seed candidates ──
        cand_count = 0
        for e in ELECTIONS:
            rows = conn.execute(
                text("SELECT id, name FROM constituency WHERE country = :country AND is_active = TRUE LIMIT :lim"),
                {"country": e["constituency_country"], "lim": e["constituency_limit"]},
            ).fetchall()

            if not rows:
                print(f"  WARNING: No constituencies for {e['constituency_country']}. "
                      "Run: python -m seeds.seed_constituencies")
                continue

            # Link constituencies
            for r in rows:
                conn.execute(insert_election_constituency, {
                    "election_id": e["id"],
                    "constituency_id": str(r[0]),
                })

            party_indices = ELECTION_PARTY_MAP.get(e["election_type"], [0, 1, 2])

            # Seed candidates: one per party per constituency
            for ci, const_row in enumerate(rows):
                const_id = str(const_row[0])
                for pi in party_indices:
                    party = PARTIES[pi]
                    names = CANDIDATE_POOLS[pi][ci % len(CANDIDATE_POOLS[pi])]
                    r = conn.execute(insert_candidate, {
                        "id": str(uuid4()),
                        "election_id": e["id"],
                        "constituency_id": const_id,
                        "first_name": names[0],
                        "last_name": names[1],
                        "party_id": party["id"],
                    })
                    cand_count += r.rowcount

            print(f"  {e['title']}: {len(rows)} constituencies linked")

        print(f"Candidates: {cand_count} inserted")

        # ── 4. Seed referendums ──
        ref_count = 0
        for ref in REFERENDUMS:
            r = conn.execute(insert_referendum, {
                "id": ref["id"],
                "title": ref["title"],
                "question": ref["question"],
                "description": ref["description"],
                "scope": ref["scope"],
            })
            ref_count += r.rowcount

            # Resolve actual ID
            row = conn.execute(
                text("SELECT id FROM referendum WHERE title = :title"),
                {"title": ref["title"]},
            ).fetchone()
            if row:
                ref["id"] = str(row[0])

            # Link constituencies for regional/local referendums
            if ref.get("constituency_country"):
                const_rows = conn.execute(
                    text("SELECT id FROM constituency WHERE country = :country AND is_active = TRUE LIMIT :lim"),
                    {"country": ref["constituency_country"], "lim": ref.get("constituency_limit", 5)},
                ).fetchall()
                for cr in const_rows:
                    conn.execute(insert_referendum_constituency, {
                        "referendum_id": ref["id"],
                        "constituency_id": str(cr[0]),
                    })

        print(f"Referendums: {ref_count} inserted ({len(REFERENDUMS)} total)")

    # ── Summary ──
    print("\n" + "=" * 70)
    print("SEED COMPLETE")
    print("=" * 70)

    print("\n--- PARTIES ---")
    for p in PARTIES:
        print(f"  {p['abbr']:5s}  {p['id']}  {p['name']}")

    print("\n--- ELECTIONS ---")
    for e in ELECTIONS:
        print(f"  {e['allocation_method']:18s}  {e['id']}  {e['title']}")

    print("\n--- REFERENDUMS ---")
    for ref in REFERENDUMS:
        print(f"  {ref['scope']:10s}  {ref['id']}  {ref['title']}")

    print("\n" + "=" * 70)


if __name__ == "__main__":
    seed()
