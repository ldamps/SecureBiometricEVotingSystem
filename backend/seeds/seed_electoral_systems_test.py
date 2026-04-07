"""Seed script for testing all 4 UK electoral systems.

Creates parties, elections, and candidates so you can test FPTP, AMS, STV,
and AV via Postman. After running, it prints ready-to-use JSON bodies.

Usage:
    cd backend
    python -m seeds.seed_electoral_systems_test

Prerequisites:
    - Database is running and migrated (including the electoral system migration).
    - Constituencies are seeded (python -m seeds.seed_constituencies).
    - At least one voter exists (registered via API).
"""

import json
import sys
import os
from uuid import uuid4

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from app.db import engine

# ---------------------------------------------------------------------------
# Test data
# ---------------------------------------------------------------------------

PARTIES = [
    {"id": str(uuid4()), "name": "Democratic Alliance", "abbr": "DA"},
    {"id": str(uuid4()), "name": "Progressive Union", "abbr": "PU"},
    {"id": str(uuid4()), "name": "National Reform Party", "abbr": "NRP"},
    {"id": str(uuid4()), "name": "Green Futures", "abbr": "GF"},
]

ELECTIONS = {
    "fptp": {
        "id": str(uuid4()),
        "title": "TEST — 2026 General Election (FPTP)",
        "election_type": "GENERAL",
        "scope": "NATIONAL",
        "allocation_method": "FPTP",
        "constituency_country": "England",
    },
    "ams": {
        "id": str(uuid4()),
        "title": "TEST — 2026 Scottish Parliament (AMS)",
        "election_type": "SCOTTISH_PARLIAMENT",
        "scope": "REGIONAL",
        "allocation_method": "AMS",
        "constituency_country": "Scotland",
    },
    "stv": {
        "id": str(uuid4()),
        "title": "TEST — 2026 NI Assembly (STV)",
        "election_type": "NORTHERN_IRELAND_ASSEMBLY",
        "scope": "REGIONAL",
        "allocation_method": "STV",
        "constituency_country": "Northern Ireland",
    },
    "av": {
        "id": str(uuid4()),
        "title": "TEST — 2026 Hereditary Peers (AV)",
        "election_type": "HOUSE_OF_LORDS_HEREDITARY",
        "scope": "NATIONAL",
        "allocation_method": "ALTERNATIVE_VOTE",
        "constituency_country": "England",
    },
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
                NOW(), NOW() + INTERVAL '7 days', NOW(), NOW())
        ON CONFLICT DO NOTHING
    """)

    insert_candidate = text("""
        INSERT INTO candidate (id, election_id, constituency_id, first_name, last_name, party_id, is_active)
        VALUES (:id, :election_id, :constituency_id, :first_name, :last_name, :party_id, TRUE)
        ON CONFLICT DO NOTHING
    """)

    # Candidate names per party (first, last)
    candidate_names = [
        [("Alice", "Morgan"), ("Ben", "Clarke"), ("Claire", "Davies"), ("David", "Evans")],
        [("Emma", "Wilson"), ("Frank", "Taylor"), ("Grace", "Brown"), ("Henry", "Jones")],
        [("Isla", "Thomas"), ("Jack", "Roberts"), ("Kate", "Williams"), ("Liam", "Hughes")],
        [("Mia", "Lewis"), ("Noah", "Walker"), ("Olivia", "Hall"), ("Peter", "Green")],
    ]

    candidates_by_election: dict[str, list[dict]] = {k: [] for k in ELECTIONS}
    constituencies_by_election: dict[str, list[dict]] = {}

    with engine.begin() as conn:
        # 1. Seed parties
        party_count = 0
        for p in PARTIES:
            r = conn.execute(insert_party, {
                "id": p["id"],
                "party_name": p["name"],
                "abbreviation": p["abbr"],
            })
            party_count += r.rowcount

        # If parties already existed, look up their IDs by name
        for p in PARTIES:
            row = conn.execute(
                text("SELECT id FROM party WHERE party_name = :name"),
                {"name": p["name"]},
            ).fetchone()
            if row:
                p["id"] = str(row[0])

        print(f"Parties: {party_count} inserted ({len(PARTIES)} total)")

        # 2. Seed elections
        election_count = 0
        for key, e in ELECTIONS.items():
            r = conn.execute(insert_election, {
                "id": e["id"],
                "title": e["title"],
                "election_type": e["election_type"],
                "scope": e["scope"],
                "allocation_method": e["allocation_method"],
            })
            election_count += r.rowcount

            # Look up actual ID (in case it already existed)
            row = conn.execute(
                text("SELECT id FROM election WHERE title = :title"),
                {"title": e["title"]},
            ).fetchone()
            if row:
                e["id"] = str(row[0])

        print(f"Elections: {election_count} inserted ({len(ELECTIONS)} total)")

        # 3. Fetch 2 constituencies per election (based on country)
        for key, e in ELECTIONS.items():
            rows = conn.execute(
                text("SELECT id, name FROM constituency WHERE country = :country AND is_active = TRUE LIMIT 2"),
                {"country": e["constituency_country"]},
            ).fetchall()
            if not rows:
                print(f"  WARNING: No constituencies found for {e['constituency_country']}. "
                      "Run: python -m seeds.seed_constituencies")
                continue
            constituencies_by_election[key] = [{"id": str(r[0]), "name": r[1]} for r in rows]

        # 4. Seed candidates: one per party per constituency per election
        cand_count = 0
        for key, e in ELECTIONS.items():
            for ci, const in enumerate(constituencies_by_election.get(key, [])):
                for pi, party in enumerate(PARTIES):
                    names = candidate_names[pi][ci % len(candidate_names[pi])]
                    cand_id = str(uuid4())
                    r = conn.execute(insert_candidate, {
                        "id": cand_id,
                        "election_id": e["id"],
                        "constituency_id": const["id"],
                        "first_name": names[0],
                        "last_name": names[1],
                        "party_id": party["id"],
                    })
                    if r.rowcount:
                        cand_count += 1
                        candidates_by_election[key].append({
                            "id": cand_id,
                            "name": f"{names[0]} {names[1]}",
                            "party": party["abbr"],
                            "constituency_id": const["id"],
                            "constituency_name": const["name"],
                        })
                    else:
                        # Already existed — look it up
                        row = conn.execute(
                            text("SELECT id FROM candidate WHERE election_id = :eid "
                                 "AND constituency_id = :cid AND party_id = :pid"),
                            {"eid": e["id"], "cid": const["id"], "pid": party["id"]},
                        ).fetchone()
                        if row:
                            candidates_by_election[key].append({
                                "id": str(row[0]),
                                "name": f"{names[0]} {names[1]}",
                                "party": party["abbr"],
                                "constituency_id": const["id"],
                                "constituency_name": const["name"],
                            })

        print(f"Candidates: {cand_count} inserted")

    # ---------------------------------------------------------------------------
    # Print Postman guide
    # ---------------------------------------------------------------------------
    print("\n" + "=" * 80)
    print("SEED COMPLETE — POSTMAN TESTING GUIDE")
    print("=" * 80)

    print("\n--- PARTIES ---")
    for p in PARTIES:
        print(f"  {p['abbr']:5s}  {p['id']}  {p['name']}")

    for key, e in ELECTIONS.items():
        method = e["allocation_method"]
        print(f"\n{'=' * 80}")
        print(f"  {method} — {e['title']}")
        print(f"  Election ID: {e['id']}")
        print(f"{'=' * 80}")

        consts = constituencies_by_election.get(key, [])
        cands = candidates_by_election.get(key, [])

        if consts:
            print(f"\n  Constituencies:")
            for c in consts:
                print(f"    {c['name']:30s}  {c['id']}")

        if cands:
            print(f"\n  Candidates:")
            for c in cands:
                print(f"    {c['name']:20s} ({c['party']})  {c['id']}  @ {c['constituency_name']}")

        # Ballot token issuance body
        if consts:
            const_id = consts[0]["id"]
            print(f"\n  Step 1 — Issue ballot tokens")
            print(f"  POST /election/{e['id']}/ballot-tokens")
            print(f"  Body:")
            print(json.dumps({
                "constituency_id": const_id,
                "count": 5,
            }, indent=4))

        # Cast vote body
        const_cands = [c for c in cands if c["constituency_id"] == consts[0]["id"]] if consts else []
        if const_cands:
            print(f"\n  Step 2 — Cast vote")
            print(f"  POST /voting/cast")
            print(f"  Body:")

            if method == "FPTP":
                body = {
                    "voter_id": "<VOTER_UUID>",
                    "election_id": e["id"],
                    "constituency_id": consts[0]["id"],
                    "candidate_id": const_cands[0]["id"],
                    "blind_token_hash": "<TOKEN_FROM_STEP_1>",
                    "send_email_confirmation": False,
                }
            elif method == "AMS":
                body = {
                    "voter_id": "<VOTER_UUID>",
                    "election_id": e["id"],
                    "constituency_id": consts[0]["id"],
                    "candidate_id": const_cands[0]["id"],
                    "party_id": PARTIES[1]["id"],
                    "blind_token_hash": "<TOKEN_FROM_STEP_1>",
                    "send_email_confirmation": False,
                }
            elif method == "STV":
                ranked = [
                    {"candidate_id": c["id"], "preference_rank": i + 1}
                    for i, c in enumerate(const_cands)
                ]
                body = {
                    "voter_id": "<VOTER_UUID>",
                    "election_id": e["id"],
                    "constituency_id": consts[0]["id"],
                    "ranked_preferences": ranked,
                    "blind_token_hash": "<TOKEN_FROM_STEP_1>",
                    "send_email_confirmation": False,
                }
            elif method == "ALTERNATIVE_VOTE":
                ranked = [
                    {"candidate_id": c["id"], "preference_rank": i + 1}
                    for i, c in enumerate(const_cands[:3])
                ]
                body = {
                    "voter_id": "<VOTER_UUID>",
                    "election_id": e["id"],
                    "constituency_id": consts[0]["id"],
                    "ranked_preferences": ranked,
                    "blind_token_hash": "<TOKEN_FROM_STEP_1>",
                    "send_email_confirmation": False,
                }
            else:
                body = {}

            print(json.dumps(body, indent=4))

        # Results
        print(f"\n  Step 3 — Check results")
        print(f"  GET /election/{e['id']}/results")

    print(f"\n{'=' * 80}")
    print("REMINDERS:")
    print("  1. Replace <VOTER_UUID> with an actual voter ID from your database.")
    print("  2. Replace <TOKEN_FROM_STEP_1> with a blind_token_hash from the")
    print("     ballot-token issuance response.")
    print("  3. All requests except /voting/cast require an admin auth token.")
    print("=" * 80)


if __name__ == "__main__":
    seed()
