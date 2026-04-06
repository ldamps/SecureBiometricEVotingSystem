"""Close elections and referendums whose voting_opens has passed.

Sets voting_closes = voting_opens + 3 days for any election/referendum
that has voting_opens in the past but no voting_closes, then marks them
as CLOSED.

Also closes any item where voting_closes is already set and in the past
but status is still OPEN.

Usage:
    cd backend
    python -m seeds.close_past_elections
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from app.db import engine


def close_past():
    with engine.begin() as conn:
        # 1. Elections with voting_opens in the past but no voting_closes
        r1 = conn.execute(text("""
            UPDATE election
            SET voting_closes = voting_opens + INTERVAL '3 days',
                status = 'CLOSED'
            WHERE voting_opens IS NOT NULL
              AND voting_opens < NOW()
              AND voting_closes IS NULL
              AND status != 'CANCELLED'
            RETURNING id, title
        """))
        for row in r1:
            print(f"  Closed election (no closing date): {row[1]} ({row[0]})")

        # 2. Elections with voting_closes in the past but still OPEN
        r2 = conn.execute(text("""
            UPDATE election
            SET status = 'CLOSED'
            WHERE voting_closes IS NOT NULL
              AND voting_closes < NOW()
              AND status = 'OPEN'
            RETURNING id, title
        """))
        for row in r2:
            print(f"  Closed election (past closing date): {row[1]} ({row[0]})")

        # 3. Referendums with voting_opens in the past but no voting_closes
        r3 = conn.execute(text("""
            UPDATE referendum
            SET voting_closes = voting_opens + INTERVAL '3 days',
                status = 'CLOSED'
            WHERE voting_opens IS NOT NULL
              AND voting_opens < NOW()
              AND voting_closes IS NULL
              AND status != 'CANCELLED'
            RETURNING id, title
        """))
        for row in r3:
            print(f"  Closed referendum (no closing date): {row[1]} ({row[0]})")

        # 4. Referendums with voting_closes in the past but still OPEN
        r4 = conn.execute(text("""
            UPDATE referendum
            SET status = 'CLOSED'
            WHERE voting_closes IS NOT NULL
              AND voting_closes < NOW()
              AND status = 'OPEN'
            RETURNING id, title
        """))
        for row in r4:
            print(f"  Closed referendum (past closing date): {row[1]} ({row[0]})")

        total = r1.rowcount + r2.rowcount + r3.rowcount + r4.rowcount
        if total == 0:
            print("  No elections or referendums needed closing.")
        else:
            print(f"\n  Total updated: {total}")


if __name__ == "__main__":
    print("Closing past elections and referendums...\n")
    close_past()
    print("\nDone.")
