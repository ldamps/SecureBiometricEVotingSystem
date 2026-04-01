"""Seed script that inserts test votes for all 4 electoral systems.

Populates vote and tally_result rows so you can immediately call
GET /election/{id}/results in Postman without casting votes manually.

Prerequisites:
    - Run seed_electoral_systems_test.py first (creates elections, candidates, parties).

Usage:
    cd backend
    python -m seeds.seed_votes_test
"""

import sys
import os
import secrets
from uuid import uuid4

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime, timezone
from sqlalchemy import text
from app.db import engine

NOW = datetime.now(timezone.utc)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def fetch_election(conn, title_prefix: str) -> dict | None:
    row = conn.execute(
        text("SELECT id, title, allocation_method FROM election WHERE title LIKE :prefix LIMIT 1"),
        {"prefix": f"TEST — %{title_prefix}%"},
    ).fetchone()
    if not row:
        return None
    return {"id": str(row[0]), "title": row[1], "allocation_method": row[2]}


def fetch_candidates(conn, election_id: str) -> list[dict]:
    rows = conn.execute(
        text("""
            SELECT c.id, c.constituency_id, c.party_id, c.first_name, c.last_name,
                   con.name AS constituency_name
            FROM candidate c
            JOIN constituency con ON con.id = c.constituency_id
            WHERE c.election_id = :eid
            ORDER BY con.name, c.last_name
        """),
        {"eid": election_id},
    ).fetchall()
    return [
        {
            "id": str(r[0]),
            "constituency_id": str(r[1]),
            "party_id": str(r[2]),
            "name": f"{r[3]} {r[4]}",
            "constituency_name": r[5],
        }
        for r in rows
    ]


def fetch_parties(conn) -> list[dict]:
    rows = conn.execute(
        text("SELECT id, party_name, abbreviation FROM party ORDER BY party_name")
    ).fetchall()
    return [{"id": str(r[0]), "name": r[1], "abbr": r[2]} for r in rows]


def insert_vote(conn, **kwargs):
    conn.execute(
        text("""
            INSERT INTO vote (id, election_id, constituency_id, candidate_id,
                              party_id, preference_rank, blind_token_hash,
                              receipt_code, email_sent, cast_at)
            VALUES (:id, :election_id, :constituency_id, :candidate_id,
                    :party_id, :preference_rank, :blind_token_hash,
                    :receipt_code, FALSE, :cast_at)
        """),
        {
            "id": str(uuid4()),
            "election_id": kwargs["election_id"],
            "constituency_id": kwargs.get("constituency_id"),
            "candidate_id": kwargs.get("candidate_id"),
            "party_id": kwargs.get("party_id"),
            "preference_rank": kwargs.get("preference_rank"),
            "blind_token_hash": kwargs.get("blind_token_hash", secrets.token_hex(16)),
            "receipt_code": kwargs.get("receipt_code", secrets.token_urlsafe(24)),
            "cast_at": NOW,
        },
    )


def insert_tally(conn, election_id: str, constituency_id: str | None,
                 candidate_id: str | None, party_id: str | None, vote_count: int):
    conn.execute(
        text("""
            INSERT INTO tally_result (id, election_id, constituency_id, candidate_id,
                                      party_id, vote_count, tallied_at)
            VALUES (:id, :eid, :cid, :cand_id, :pid, :count, :now)
        """),
        {
            "id": str(uuid4()),
            "eid": election_id,
            "cid": constituency_id,
            "cand_id": candidate_id,
            "pid": party_id,
            "count": vote_count,
            "now": NOW,
        },
    )


# ---------------------------------------------------------------------------
# FPTP votes
# ---------------------------------------------------------------------------

def seed_fptp(conn, election: dict, candidates: list[dict]):
    """Seed FPTP: simple vote counts per candidate per constituency.

    Simulates ~100 voters per constituency with a clear winner.
    """
    eid = election["id"]
    by_const: dict[str, list[dict]] = {}
    for c in candidates:
        by_const.setdefault(c["constituency_id"], []).append(c)

    # Vote distribution: 1st candidate gets 45, 2nd 30, 3rd 15, 4th 10
    vote_dist = [45, 30, 15, 10]
    total = 0

    for cid, cands in by_const.items():
        for i, cand in enumerate(cands):
            votes = vote_dist[i] if i < len(vote_dist) else 5
            insert_tally(conn, eid, cid, cand["id"], None, votes)
            total += votes

    print(f"  FPTP: {total} votes across {len(by_const)} constituencies")


# ---------------------------------------------------------------------------
# AMS votes
# ---------------------------------------------------------------------------

def seed_ams(conn, election: dict, candidates: list[dict], parties: list[dict]):
    """Seed AMS: constituency tallies (candidate) + regional tallies (party).

    Constituency votes use FPTP-style tallies.
    Regional list votes are party-level tallies (no constituency).
    """
    eid = election["id"]
    by_const: dict[str, list[dict]] = {}
    for c in candidates:
        by_const.setdefault(c["constituency_id"], []).append(c)

    # Constituency votes (FPTP style)
    const_dist = [40, 35, 15, 10]
    total = 0
    for cid, cands in by_const.items():
        for i, cand in enumerate(cands):
            votes = const_dist[i] if i < len(const_dist) else 5
            insert_tally(conn, eid, cid, cand["id"], None, votes)
            total += votes

    # Regional list votes (party-level, no constituency)
    # Distribute differently from constituency to show top-up effect
    regional_dist = [800, 600, 400, 200]
    for i, party in enumerate(parties[:4]):
        votes = regional_dist[i] if i < len(regional_dist) else 100
        insert_tally(conn, eid, None, None, party["id"], votes)
        total += votes

    print(f"  AMS: {total} votes ({len(by_const)} constituencies + regional list)")


# ---------------------------------------------------------------------------
# STV votes
# ---------------------------------------------------------------------------

def seed_stv(conn, election: dict, candidates: list[dict]):
    """Seed STV: ranked preference vote rows.

    Creates individual Vote rows with preference_rank for each ballot.
    Also creates first-preference tally rows.
    The result service reads raw Vote rows for STV counting.
    """
    eid = election["id"]
    by_const: dict[str, list[dict]] = {}
    for c in candidates:
        by_const.setdefault(c["constituency_id"], []).append(c)

    total_ballots = 0

    for cid, cands in by_const.items():
        # Simulate 80 ballots with varying preference orders
        # Each ballot ranks all 4 candidates in different orders
        ballot_patterns = [
            # pattern: list of candidate indices in preference order
            # 30 ballots: A > B > C > D
            ([0, 1, 2, 3], 30),
            # 20 ballots: B > C > A > D
            ([1, 2, 0, 3], 20),
            # 15 ballots: C > A > B > D
            ([2, 0, 1, 3], 15),
            # 15 ballots: D > C > B > A
            ([3, 2, 1, 0], 15),
        ]

        first_pref_counts: dict[str, int] = {}

        for pattern, count in ballot_patterns:
            for _ in range(count):
                base_token = secrets.token_hex(16)
                receipt = secrets.token_urlsafe(24)
                for rank, cand_idx in enumerate(pattern):
                    if cand_idx >= len(cands):
                        continue
                    cand = cands[cand_idx]
                    insert_vote(
                        conn,
                        election_id=eid,
                        constituency_id=cid,
                        candidate_id=cand["id"],
                        preference_rank=rank + 1,
                        blind_token_hash=f"{base_token}:rank{rank + 1}" if rank > 0 else base_token,
                        receipt_code=f"{receipt}:rank{rank + 1}" if rank > 0 else receipt,
                    )
                    if rank == 0:
                        first_pref_counts[cand["id"]] = first_pref_counts.get(cand["id"], 0) + 1

                total_ballots += 1

        # Insert first-preference tallies for display
        for cand_id, count in first_pref_counts.items():
            insert_tally(conn, eid, cid, cand_id, None, count)

    print(f"  STV: {total_ballots} ballots across {len(by_const)} constituencies")


# ---------------------------------------------------------------------------
# AV votes
# ---------------------------------------------------------------------------

def seed_av(conn, election: dict, candidates: list[dict]):
    """Seed AV: ranked preference vote rows (single-seat constituencies).

    Similar to STV but designed so no candidate wins on first preferences,
    forcing elimination rounds.
    """
    eid = election["id"]
    by_const: dict[str, list[dict]] = {}
    for c in candidates:
        by_const.setdefault(c["constituency_id"], []).append(c)

    total_ballots = 0

    for cid, cands in by_const.items():
        # No candidate has >50% on first preferences to force AV rounds
        ballot_patterns = [
            # 35 ballots: A > B > C > D
            ([0, 1, 2, 3], 35),
            # 30 ballots: B > A > C > D
            ([1, 0, 2, 3], 30),
            # 20 ballots: C > B > A > D
            ([2, 1, 0, 3], 20),
            # 15 ballots: D > C > B > A
            ([3, 2, 1, 0], 15),
        ]

        first_pref_counts: dict[str, int] = {}

        for pattern, count in ballot_patterns:
            for _ in range(count):
                base_token = secrets.token_hex(16)
                receipt = secrets.token_urlsafe(24)
                for rank, cand_idx in enumerate(pattern):
                    if cand_idx >= len(cands):
                        continue
                    cand = cands[cand_idx]
                    insert_vote(
                        conn,
                        election_id=eid,
                        constituency_id=cid,
                        candidate_id=cand["id"],
                        preference_rank=rank + 1,
                        blind_token_hash=f"{base_token}:rank{rank + 1}" if rank > 0 else base_token,
                        receipt_code=f"{receipt}:rank{rank + 1}" if rank > 0 else receipt,
                    )
                    if rank == 0:
                        first_pref_counts[cand["id"]] = first_pref_counts.get(cand["id"], 0) + 1

                total_ballots += 1

        # Insert first-preference tallies for display
        for cand_id, count in first_pref_counts.items():
            insert_tally(conn, eid, cid, cand_id, None, count)

    print(f"  AV: {total_ballots} ballots across {len(by_const)} constituencies")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def seed():
    elections_config = [
        ("General Election (FPTP)", "fptp"),
        ("Scottish Parliament (AMS)", "ams"),
        ("NI Assembly (STV)", "stv"),
        ("Hereditary Peers (AV)", "av"),
    ]

    with engine.begin() as conn:
        # Clear previous test votes/tallies
        for title_part, _ in elections_config:
            e = fetch_election(conn, title_part)
            if e:
                conn.execute(
                    text("DELETE FROM vote WHERE election_id = :eid"),
                    {"eid": e["id"]},
                )
                conn.execute(
                    text("DELETE FROM tally_result WHERE election_id = :eid"),
                    {"eid": e["id"]},
                )

        parties = fetch_parties(conn)
        if not parties:
            print("ERROR: No parties found. Run seed_electoral_systems_test.py first.")
            return

        print("Seeding test votes...\n")

        for title_part, method_key in elections_config:
            e = fetch_election(conn, title_part)
            if not e:
                print(f"  SKIP: No election found matching '{title_part}'")
                continue

            cands = fetch_candidates(conn, e["id"])
            if not cands:
                print(f"  SKIP: No candidates for '{e['title']}'")
                continue

            if method_key == "fptp":
                seed_fptp(conn, e, cands)
            elif method_key == "ams":
                seed_ams(conn, e, cands, parties)
            elif method_key == "stv":
                seed_stv(conn, e, cands)
            elif method_key == "av":
                seed_av(conn, e, cands)

            print(f"    -> GET /election/{e['id']}/results\n")

    print("Done! Call the GET /results endpoints above in Postman.")


if __name__ == "__main__":
    seed()
