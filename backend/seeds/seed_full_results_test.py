"""Seed full-scale election and referendum results for testing the officials dashboard.

Populates candidates across multiple constituencies and inserts realistic
tally_result rows for all 4 electoral systems plus referendums.
All seeded elections/referendums are set to CLOSED so results are visible.

Usage:
    cd backend
    python -m seeds.seed_full_results_test
"""

import sys
import os
import random
import secrets
from uuid import uuid4, UUID
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from app.db import engine

NOW = datetime.now(timezone.utc)

# ---------------------------------------------------------------------------
# Party IDs (looked up at runtime)
# ---------------------------------------------------------------------------
PARTIES: list[dict] = []

# Candidate first/last name pools
FIRST_NAMES = [
    "Alistair", "Morag", "Niamh", "Declan", "Siobhan", "Ruaridh", "Aoife",
    "Cormac", "Isla", "Fergus", "Maeve", "Callum", "Orla", "Euan", "Catriona",
    "Hamish", "Bronagh", "Finlay", "Saoirse", "Duncan", "Ciara", "Angus",
    "Roisin", "Gregor", "Aisling", "Struan", "Deirdre", "Blair", "Sinead",
    "Iain", "Grainne", "Murray", "Fionnuala", "Ross", "Mairead", "Craig",
    "Tara", "Stuart", "Clodagh", "Gavin", "Emer", "Keith", "Nuala", "Derek",
    "Sorcha", "Gordon", "Ailish", "Neil", "Brianna", "Malcolm",
]
LAST_NAMES = [
    "MacLeod", "O'Brien", "Campbell", "Walsh", "Stewart", "Murphy", "Douglas",
    "Kelly", "Murray", "O'Connor", "Robertson", "Brennan", "Anderson", "Quinn",
    "Fraser", "Gallagher", "Hamilton", "Doyle", "Henderson", "Byrne",
    "MacDonald", "Ryan", "Thomson", "O'Neill", "Mitchell", "Fitzgerald",
    "Crawford", "McCarthy", "Sinclair", "Kavanagh", "Graham", "O'Sullivan",
    "Patterson", "Doherty", "Morrison", "Healy", "Wallace", "Nolan",
    "Cunningham", "Power", "Kerr", "Maguire", "Hunter", "Sweeney",
    "Aitken", "Lynch", "Baxter", "Duffy", "Milne", "Hogan",
]

_used_names: set[str] = set()

def random_name() -> tuple[str, str]:
    for _ in range(500):
        first = random.choice(FIRST_NAMES)
        last = random.choice(LAST_NAMES)
        key = f"{first} {last}"
        if key not in _used_names:
            _used_names.add(key)
            return first, last
    return f"Candidate{random.randint(1000,9999)}", "Smith"


def seed():
    with engine.begin() as conn:
        # Load parties
        rows = conn.execute(text(
            "SELECT id, party_name, abbreviation FROM party ORDER BY party_name"
        )).fetchall()
        for r in rows:
            PARTIES.append({"id": str(r[0]), "name": r[1], "abbr": r[2]})

        if len(PARTIES) < 3:
            print("ERROR: Need at least 3 parties. Run seed_electoral_systems_test.py first.")
            return

        print(f"Found {len(PARTIES)} parties: {', '.join(p['abbr'] for p in PARTIES)}")

        # Load elections
        elections = {}
        rows = conn.execute(text(
            "SELECT id, title, allocation_method FROM election ORDER BY title"
        )).fetchall()
        for r in rows:
            elections[str(r[0])] = {"id": str(r[0]), "title": r[1], "method": r[2]}

        # Load referendums
        referendums = {}
        rows = conn.execute(text(
            "SELECT id, title FROM referendum ORDER BY title"
        )).fetchall()
        for r in rows:
            referendums[str(r[0])] = {"id": str(r[0]), "title": r[1]}

        # Load constituencies (pick a good spread across countries)
        constituencies = {}
        for country in ["England", "Scotland", "Wales", "Northern Ireland"]:
            rows = conn.execute(text(
                "SELECT id, name, country FROM constituency WHERE country = :c AND is_active = TRUE ORDER BY name LIMIT 20"
            ), {"c": country}).fetchall()
            for r in rows:
                constituencies[str(r[0])] = {"id": str(r[0]), "name": r[1], "country": r[2]}

        print(f"Found {len(constituencies)} constituencies across 4 countries")

        # Clear existing test data
        print("\nClearing existing tallies, votes, candidates, and constituency links...")
        for eid in elections:
            conn.execute(text("DELETE FROM vote WHERE election_id = :eid"), {"eid": eid})
            conn.execute(text("DELETE FROM tally_result WHERE election_id = :eid"), {"eid": eid})
            conn.execute(text("DELETE FROM candidate WHERE election_id = :eid"), {"eid": eid})
            conn.execute(text("DELETE FROM election_constituency WHERE election_id = :eid"), {"eid": eid})
        for rid in referendums:
            conn.execute(text("DELETE FROM tally_result WHERE referendum_id = :rid"), {"rid": rid})

        # ─────────────────────────────────────────────────────────
        # FPTP: UK General Election (nationwide, many constituencies)
        # ─────────────────────────────────────────────────────────
        fptp_election = next((e for e in elections.values() if e["method"] == "FPTP"), None)
        if fptp_election:
            print(f"\n{'='*70}")
            print(f"Seeding FPTP: {fptp_election['title']}")
            print(f"{'='*70}")

            # Pick 15 constituencies across all countries
            eng = [c for c in constituencies.values() if c["country"] == "England"][:6]
            sco = [c for c in constituencies.values() if c["country"] == "Scotland"][:4]
            wal = [c for c in constituencies.values() if c["country"] == "Wales"][:3]
            ni  = [c for c in constituencies.values() if c["country"] == "Northern Ireland"][:2]
            fptp_consts = eng + sco + wal + ni

            # Link constituencies to election
            for c in fptp_consts:
                conn.execute(text(
                    "INSERT INTO election_constituency (election_id, constituency_id) VALUES (:eid, :cid) ON CONFLICT DO NOTHING"
                ), {"eid": fptp_election["id"], "cid": c["id"]})

            # Create 4 candidates per constituency
            total_votes = 0
            for const in fptp_consts:
                cand_ids = []
                for pi in range(min(4, len(PARTIES))):
                    first, last = random_name()
                    cid = str(uuid4())
                    conn.execute(text(
                        "INSERT INTO candidate (id, election_id, constituency_id, first_name, last_name, party_id, is_active) "
                        "VALUES (:id, :eid, :cid, :fn, :ln, :pid, TRUE)"
                    ), {"id": cid, "eid": fptp_election["id"], "cid": const["id"],
                        "fn": first, "ln": last, "pid": PARTIES[pi]["id"]})
                    cand_ids.append((cid, PARTIES[pi]["id"]))

                # Tally: realistic vote counts with variation
                base_votes = [
                    random.randint(15000, 28000),
                    random.randint(8000, 18000),
                    random.randint(3000, 9000),
                    random.randint(1000, 4000),
                ]
                random.shuffle(base_votes)
                for i, (cand_id, party_id) in enumerate(cand_ids):
                    votes = base_votes[i]
                    conn.execute(text(
                        "INSERT INTO tally_result (id, election_id, constituency_id, candidate_id, party_id, vote_count, tallied_at) "
                        "VALUES (:id, :eid, :cid, :cand, :pid, :votes, :now)"
                    ), {"id": str(uuid4()), "eid": fptp_election["id"], "cid": const["id"],
                        "cand": cand_id, "pid": party_id, "votes": votes, "now": NOW})
                    total_votes += votes

            print(f"  {len(fptp_consts)} constituencies, {len(fptp_consts)*4} candidates, {total_votes:,} total votes")

        # ─────────────────────────────────────────────────────────
        # AMS: Scottish Parliament Election
        # ─────────────────────────────────────────────────────────
        ams_election = next((e for e in elections.values() if e["method"] == "AMS"), None)
        if ams_election:
            print(f"\n{'='*70}")
            print(f"Seeding AMS: {ams_election['title']}")
            print(f"{'='*70}")

            ams_consts = [c for c in constituencies.values() if c["country"] == "Scotland"][:8]

            for c in ams_consts:
                conn.execute(text(
                    "INSERT INTO election_constituency (election_id, constituency_id) VALUES (:eid, :cid) ON CONFLICT DO NOTHING"
                ), {"eid": ams_election["id"], "cid": c["id"]})

            total_votes = 0
            for const in ams_consts:
                cand_ids = []
                for pi in range(min(4, len(PARTIES))):
                    first, last = random_name()
                    cid = str(uuid4())
                    conn.execute(text(
                        "INSERT INTO candidate (id, election_id, constituency_id, first_name, last_name, party_id, is_active) "
                        "VALUES (:id, :eid, :cid, :fn, :ln, :pid, TRUE)"
                    ), {"id": cid, "eid": ams_election["id"], "cid": const["id"],
                        "fn": first, "ln": last, "pid": PARTIES[pi]["id"]})
                    cand_ids.append((cid, PARTIES[pi]["id"]))

                # Constituency vote tallies
                base_votes = [
                    random.randint(12000, 22000),
                    random.randint(6000, 15000),
                    random.randint(2000, 7000),
                    random.randint(800, 3000),
                ]
                random.shuffle(base_votes)
                for i, (cand_id, party_id) in enumerate(cand_ids):
                    votes = base_votes[i]
                    conn.execute(text(
                        "INSERT INTO tally_result (id, election_id, constituency_id, candidate_id, party_id, vote_count, tallied_at) "
                        "VALUES (:id, :eid, :cid, :cand, :pid, :votes, :now)"
                    ), {"id": str(uuid4()), "eid": ams_election["id"], "cid": const["id"],
                        "cand": cand_id, "pid": party_id, "votes": votes, "now": NOW})
                    total_votes += votes

            # Regional list votes (party-level, no constituency)
            regional_votes = [
                random.randint(350000, 500000),
                random.randint(250000, 400000),
                random.randint(100000, 200000),
                random.randint(50000, 120000),
            ]
            for i, party in enumerate(PARTIES[:4]):
                votes = regional_votes[i]
                conn.execute(text(
                    "INSERT INTO tally_result (id, election_id, candidate_id, party_id, vote_count, tallied_at) "
                    "VALUES (:id, :eid, NULL, :pid, :votes, :now)"
                ), {"id": str(uuid4()), "eid": ams_election["id"],
                    "pid": party["id"], "votes": votes, "now": NOW})
                total_votes += votes

            print(f"  {len(ams_consts)} constituencies, {len(ams_consts)*4} candidates + regional list, {total_votes:,} total votes")

        # ─────────────────────────────────────────────────────────
        # STV: Council Election (needs raw Vote rows for counting)
        # ─────────────────────────────────────────────────────────
        stv_election = next((e for e in elections.values() if e["method"] == "STV"), None)
        if stv_election:
            print(f"\n{'='*70}")
            print(f"Seeding STV: {stv_election['title']}")
            print(f"{'='*70}")

            stv_consts = [c for c in constituencies.values() if c["country"] in ("Scotland", "Northern Ireland")][:6]

            for c in stv_consts:
                conn.execute(text(
                    "INSERT INTO election_constituency (election_id, constituency_id) VALUES (:eid, :cid) ON CONFLICT DO NOTHING"
                ), {"eid": stv_election["id"], "cid": c["id"]})

            total_ballots = 0
            for const in stv_consts:
                cand_ids = []
                for pi in range(min(4, len(PARTIES))):
                    first, last = random_name()
                    cid = str(uuid4())
                    conn.execute(text(
                        "INSERT INTO candidate (id, election_id, constituency_id, first_name, last_name, party_id, is_active) "
                        "VALUES (:id, :eid, :cid, :fn, :ln, :pid, TRUE)"
                    ), {"id": cid, "eid": stv_election["id"], "cid": const["id"],
                        "fn": first, "ln": last, "pid": PARTIES[pi]["id"]})
                    cand_ids.append(cid)

                # Insert ranked Vote rows (STV needs raw ballots)
                ballot_patterns = [
                    ([0, 1, 2, 3], random.randint(80, 150)),
                    ([1, 2, 0, 3], random.randint(50, 120)),
                    ([2, 0, 1, 3], random.randint(40, 90)),
                    ([3, 2, 1, 0], random.randint(30, 70)),
                ]
                for pattern, count in ballot_patterns:
                    for _ in range(count):
                        base_token = secrets.token_hex(16)
                        receipt = secrets.token_urlsafe(24)
                        for rank, cand_idx in enumerate(pattern):
                            if cand_idx >= len(cand_ids):
                                continue
                            token = base_token if rank == 0 else f"{base_token}:rank{rank + 1}"
                            rc = receipt if rank == 0 else f"{receipt}:rank{rank + 1}"
                            conn.execute(text(
                                "INSERT INTO vote (id, election_id, constituency_id, candidate_id, "
                                "preference_rank, blind_token_hash, blind_token_hash_search_token, "
                                "receipt_code, receipt_code_search_token, email_sent, cast_at) "
                                "VALUES (:id, :eid, :cid, :cand, :rank, CAST(:token AS jsonb), :token_st, "
                                "CAST(:rc AS jsonb), :rc_st, FALSE, :now)"
                            ), {
                                "id": str(uuid4()), "eid": stv_election["id"], "cid": const["id"],
                                "cand": cand_ids[cand_idx], "rank": rank + 1,
                                "token": f'"{token}"', "token_st": secrets.token_hex(16),
                                "rc": f'"{rc}"', "rc_st": secrets.token_hex(16), "now": NOW,
                            })
                        total_ballots += 1

                # Also insert tally rows for the tallies endpoint
                first_pref = {cid: 0 for cid in cand_ids}
                for pattern, count in ballot_patterns:
                    if pattern[0] < len(cand_ids):
                        first_pref[cand_ids[pattern[0]]] += count
                for cand_id in cand_ids:
                    pi = cand_ids.index(cand_id)
                    conn.execute(text(
                        "INSERT INTO tally_result (id, election_id, constituency_id, candidate_id, party_id, vote_count, tallied_at) "
                        "VALUES (:id, :eid, :cid, :cand, :pid, :votes, :now)"
                    ), {"id": str(uuid4()), "eid": stv_election["id"], "cid": const["id"],
                        "cand": cand_id, "pid": PARTIES[pi]["id"], "votes": first_pref[cand_id], "now": NOW})

            print(f"  {len(stv_consts)} constituencies, {len(stv_consts)*4} candidates, {total_ballots:,} ballots")

        # ─────────────────────────────────────────────────────────
        # AV: Alternative Vote Election (needs raw Vote rows)
        # ─────────────────────────────────────────────────────────
        av_election = next((e for e in elections.values() if e["method"] == "ALTERNATIVE_VOTE"), None)
        if av_election:
            print(f"\n{'='*70}")
            print(f"Seeding AV: {av_election['title']}")
            print(f"{'='*70}")

            av_consts = [c for c in constituencies.values() if c["country"] == "England"][:5]

            for c in av_consts:
                conn.execute(text(
                    "INSERT INTO election_constituency (election_id, constituency_id) VALUES (:eid, :cid) ON CONFLICT DO NOTHING"
                ), {"eid": av_election["id"], "cid": c["id"]})

            total_ballots = 0
            for const in av_consts:
                cand_ids = []
                for pi in range(min(4, len(PARTIES))):
                    first, last = random_name()
                    cid = str(uuid4())
                    conn.execute(text(
                        "INSERT INTO candidate (id, election_id, constituency_id, first_name, last_name, party_id, is_active) "
                        "VALUES (:id, :eid, :cid, :fn, :ln, :pid, TRUE)"
                    ), {"id": cid, "eid": av_election["id"], "cid": const["id"],
                        "fn": first, "ln": last, "pid": PARTIES[pi]["id"]})
                    cand_ids.append(cid)

                # Insert ranked Vote rows (no candidate >50% to force AV rounds)
                ballot_patterns = [
                    ([0, 1, 2, 3], random.randint(100, 180)),
                    ([1, 0, 2, 3], random.randint(80, 160)),
                    ([2, 1, 0, 3], random.randint(50, 100)),
                    ([3, 2, 1, 0], random.randint(30, 70)),
                ]
                for pattern, count in ballot_patterns:
                    for _ in range(count):
                        base_token = secrets.token_hex(16)
                        receipt = secrets.token_urlsafe(24)
                        for rank, cand_idx in enumerate(pattern):
                            if cand_idx >= len(cand_ids):
                                continue
                            token = base_token if rank == 0 else f"{base_token}:rank{rank + 1}"
                            rc = receipt if rank == 0 else f"{receipt}:rank{rank + 1}"
                            conn.execute(text(
                                "INSERT INTO vote (id, election_id, constituency_id, candidate_id, "
                                "preference_rank, blind_token_hash, blind_token_hash_search_token, "
                                "receipt_code, receipt_code_search_token, email_sent, cast_at) "
                                "VALUES (:id, :eid, :cid, :cand, :rank, CAST(:token AS jsonb), :token_st, "
                                "CAST(:rc AS jsonb), :rc_st, FALSE, :now)"
                            ), {
                                "id": str(uuid4()), "eid": av_election["id"], "cid": const["id"],
                                "cand": cand_ids[cand_idx], "rank": rank + 1,
                                "token": f'"{token}"', "token_st": secrets.token_hex(16),
                                "rc": f'"{rc}"', "rc_st": secrets.token_hex(16), "now": NOW,
                            })
                        total_ballots += 1

                # Also insert tally rows for the tallies endpoint
                first_pref = {cid: 0 for cid in cand_ids}
                for pattern, count in ballot_patterns:
                    if pattern[0] < len(cand_ids):
                        first_pref[cand_ids[pattern[0]]] += count
                for cand_id in cand_ids:
                    pi = cand_ids.index(cand_id)
                    conn.execute(text(
                        "INSERT INTO tally_result (id, election_id, constituency_id, candidate_id, party_id, vote_count, tallied_at) "
                        "VALUES (:id, :eid, :cid, :cand, :pid, :votes, :now)"
                    ), {"id": str(uuid4()), "eid": av_election["id"], "cid": const["id"],
                        "cand": cand_id, "pid": PARTIES[pi]["id"], "votes": first_pref[cand_id], "now": NOW})

            print(f"  {len(av_consts)} constituencies, {len(av_consts)*4} candidates, {total_ballots:,} ballots")

        # ─────────────────────────────────────────────────────────
        # REFERENDUMS
        # ─────────────────────────────────────────────────────────
        for ref in referendums.values():
            print(f"\n{'='*70}")
            print(f"Seeding Referendum: {ref['title']}")
            print(f"{'='*70}")

            yes_votes = random.randint(800000, 1500000)
            no_votes = random.randint(600000, 1400000)

            conn.execute(text(
                "INSERT INTO tally_result (id, referendum_id, choice, vote_count, tallied_at) "
                "VALUES (:id, :rid, 'YES', :votes, :now)"
            ), {"id": str(uuid4()), "rid": ref["id"], "votes": yes_votes, "now": NOW})
            conn.execute(text(
                "INSERT INTO tally_result (id, referendum_id, choice, vote_count, tallied_at) "
                "VALUES (:id, :rid, 'NO', :votes, :now)"
            ), {"id": str(uuid4()), "rid": ref["id"], "votes": no_votes, "now": NOW})

            print(f"  YES: {yes_votes:,}  NO: {no_votes:,}  Total: {yes_votes+no_votes:,}")

        # ─────────────────────────────────────────────────────────
        # Close all elections and referendums
        # ─────────────────────────────────────────────────────────
        print(f"\n{'='*70}")
        print("Closing all elections and referendums...")
        print(f"{'='*70}")

        conn.execute(text(
            "UPDATE election SET status = 'CLOSED', voting_closes = :closes "
            "WHERE status != 'CANCELLED'"
        ), {"closes": "2026-04-05T23:00:00+01:00"})

        conn.execute(text(
            "UPDATE referendum SET status = 'CLOSED', voting_closes = :closes "
            "WHERE status != 'CANCELLED'"
        ), {"closes": "2026-04-05T23:00:00+01:00"})

        print("  All elections and referendums set to CLOSED.")

    # ─────────────────────────────────────────────────────────
    # Summary
    # ─────────────────────────────────────────────────────────
    print(f"\n{'='*70}")
    print("SEED COMPLETE")
    print(f"{'='*70}")
    print("\nAll elections and referendums are now CLOSED with full tally data.")
    print("Refresh the Election Verification Dashboard to see results.\n")
    print("Endpoints to test:")
    for e in elections.values():
        print(f"  GET /election/{e['id']}/results  ({e['title']})")
    for r in referendums.values():
        print(f"  GET /referendum/{r['id']}/results  ({r['title']})")


if __name__ == "__main__":
    random.seed(42)  # Reproducible results
    print("Seeding full-scale election results test data...\n")
    seed()
