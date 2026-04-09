# auth_route.py - Authentication routes (login, refresh, change password, me).

from uuid import UUID

import structlog
from fastapi import APIRouter, Body, Depends, status

from app.application.api.dependencies import get_auth_service, get_current_user
from app.models.dto.auth import TokenPayload
from app.models.schemas.auth import (
    AuthenticatedUser,
    ChangePasswordRequest,
    ChangePasswordResponse,
    LoginRequest,
    RefreshTokenRequest,
    TokenResponse,
)
from app.service.auth_service import AuthService

logger = structlog.get_logger()

### ROUTES ###
router = APIRouter(
    prefix="/auth",
    tags=["auth"],
)


# Temporary diagnostic + seed endpoint
@router.get("/debug-db")
async def debug_db(service: AuthService = Depends(get_auth_service)) -> dict:
    """Temporary: show which DB and officials exist."""
    from app.config import DATABASE_URL
    from sqlalchemy import text
    result = await service.session.execute(text("SELECT username, role FROM election_official ORDER BY username"))
    officials = [{"username": r[0], "role": r[1]} for r in result]
    return {"database_url": DATABASE_URL[:50] + "...", "officials": officials}


@router.get("/seed-officials")
async def seed_officials(service: AuthService = Depends(get_auth_service)) -> dict:
    """Temporary: seed officials into whatever DB the app connects to."""
    from argon2 import PasswordHasher
    from uuid import uuid4
    from sqlalchemy import text

    ph = PasswordHasher(time_cost=3, memory_cost=65536, parallelism=4)
    officials = [
        ("admin1", "ADMIN", "Password1"),
        ("admin2", "ADMIN", "Password1"),
        ("officer1", "OFFICER", "Password1"),
        ("officer2", "OFFICER", "Password1"),
        ("officer3", "OFFICER", "Password1"),
    ]
    created = []
    for username, role, password in officials:
        pwd_hash = ph.hash(password)
        await service.session.execute(
            text("""INSERT INTO election_official
                    (id, username, password_hash, role, is_active, must_reset_password, failed_login_attempts, created_at, updated_at)
                    VALUES (:id, :u, :p, :r, TRUE, FALSE, 0, NOW(), NOW())
                    ON CONFLICT (username) DO UPDATE SET password_hash = EXCLUDED.password_hash, failed_login_attempts = 0, locked_until = NULL"""),
            {"id": str(uuid4()), "u": username, "p": pwd_hash, "r": role},
        )
        created.append(username)
    return {"seeded": created, "message": "Officials seeded. Try admin1/Password1"}


@router.get("/seed-all")
async def seed_all(service: AuthService = Depends(get_auth_service)) -> dict:
    """Temporary: seed constituencies, parties, elections, candidates, referendums,
    votes, tally results, seat allocations into the production database."""
    import hashlib, hmac, os, json
    from uuid import uuid4
    from datetime import datetime, timezone, timedelta
    from sqlalchemy import text

    db = service.session
    summary = {}

    # ── helpers ────────────────────────────────────────────────────────
    def uid() -> str:
        return str(uuid4())

    fake_enc = json.dumps({"ciphertext": "seed", "nonce": "n", "tag": "t", "dek_version": 1})

    def fake_search_token() -> str:
        return hashlib.sha256(os.urandom(32)).hexdigest()

    # ── 1. Constituencies ─────────────────────────────────────────────
    CONSTITUENCIES = [
        # England
        ("Cities of London and Westminster", "England", "London", "London"),
        ("Manchester Central", "England", "Greater Manchester", "North West"),
        ("Birmingham Ladywood", "England", "West Midlands", "West Midlands"),
        ("Leeds Central and Headingley", "England", "West Yorkshire", "Yorkshire and The Humber"),
        ("Bristol Central", "England", "Bristol", "South West"),
        ("Cambridge", "England", "Cambridgeshire", "East of England"),
        ("Sheffield Central", "England", "South Yorkshire", "Yorkshire and The Humber"),
        ("Liverpool Riverside", "England", "Merseyside", "North West"),
        ("Islington North", "England", "London", "London"),
        ("Oxford East", "England", "Oxfordshire", "South East"),
        ("Brighton Pavilion", "England", "East Sussex", "South East"),
        ("Hackney North and Stoke Newington", "England", "London", "London"),
        # Scotland
        ("Edinburgh Central", "Scotland", "Edinburgh", "Lothian"),
        ("Glasgow Central", "Scotland", "Glasgow", "Glasgow"),
        ("Aberdeen North", "Scotland", "Aberdeenshire", "North East Scotland"),
        ("Dundee Central", "Scotland", "Dundee", "Mid Scotland and Fife"),
        ("Inverness and Nairn", "Scotland", "Highland", "Highlands and Islands"),
        ("Stirling and Strathallan", "Scotland", "Stirling", "Mid Scotland and Fife"),
        # Wales
        ("Cardiff South and Penarth", "Wales", "South Glamorgan", "South Wales Central"),
        ("Swansea West", "Wales", "West Glamorgan", "South Wales West"),
        ("Newport East", "Wales", "Gwent", "South Wales East"),
        ("Wrexham", "Wales", "Clwyd", "North Wales"),
        # Northern Ireland
        ("Belfast South and Mid Down", "Northern Ireland", "Antrim", ""),
        ("Foyle", "Northern Ireland", "Londonderry", ""),
        ("Newry and Armagh", "Northern Ireland", "Armagh", ""),
        ("North Antrim", "Northern Ireland", "Antrim", ""),
        ("Strangford", "Northern Ireland", "Down", ""),
    ]
    const_ids = {}
    for name, country, county, region in CONSTITUENCIES:
        cid = uid()
        await db.execute(text(
            "INSERT INTO constituency (id, name, country, county, region, is_active) "
            "VALUES (:id, :n, :co, :cu, :r, TRUE) ON CONFLICT (name) DO NOTHING"
        ), {"id": cid, "n": name, "co": country, "cu": county, "r": region})
        row = await db.execute(text("SELECT id FROM constituency WHERE name = :n"), {"n": name})
        const_ids[name] = str(row.scalar())
    summary["constituencies"] = len(const_ids)

    # ── 2. Parties ────────────────────────────────────────────────────
    PARTIES = [
        ("Conservative Party", "CON"), ("Labour Party", "LAB"),
        ("Liberal Democrats", "LD"), ("Scottish National Party", "SNP"),
        ("Green Party", "GRN"), ("Reform UK", "REF"),
        ("Plaid Cymru", "PC"), ("Sinn Féin", "SF"),
        ("Democratic Unionist Party", "DUP"), ("Alliance Party", "ALL"),
    ]
    party_ids = {}
    for pname, abbr in PARTIES:
        pid = uid()
        await db.execute(text(
            "INSERT INTO party (id, party_name, abbreviation, is_active, created_at, updated_at) "
            "VALUES (:id, :n, :a, TRUE, NOW(), NOW()) ON CONFLICT (party_name) DO NOTHING"
        ), {"id": pid, "n": pname, "a": abbr})
        row = await db.execute(text("SELECT id FROM party WHERE party_name = :n"), {"n": pname})
        party_ids[abbr] = str(row.scalar())
    summary["parties"] = len(party_ids)

    # ── 3. Elections ──────────────────────────────────────────────────
    now = datetime.now(timezone.utc)
    ELECTIONS = [
        {
            "title": "2026 UK General Election",
            "type": "GENERAL", "scope": "NATIONAL", "method": "FPTP", "status": "CLOSED",
            "opens": now - timedelta(days=14), "closes": now - timedelta(days=7),
            "country": "England", "limit": 12,
            "parties": ["CON", "LAB", "LD", "GRN", "REF"],
        },
        {
            "title": "2026 Scottish Parliament Election",
            "type": "SCOTTISH_PARLIAMENT", "scope": "REGIONAL", "method": "AMS", "status": "CLOSED",
            "opens": now - timedelta(days=14), "closes": now - timedelta(days=7),
            "country": "Scotland", "limit": 6,
            "parties": ["CON", "LAB", "LD", "SNP", "GRN"],
        },
        {
            "title": "2026 Northern Ireland Assembly Election",
            "type": "NORTHERN_IRELAND_ASSEMBLY", "scope": "REGIONAL", "method": "STV", "status": "CLOSED",
            "opens": now - timedelta(days=14), "closes": now - timedelta(days=7),
            "country": "Northern Ireland", "limit": 5,
            "parties": ["SF", "DUP", "ALL", "LAB", "GRN"],
        },
        {
            "title": "2026 London Assembly Election",
            "type": "LONDON_ASSEMBLY", "scope": "REGIONAL", "method": "AMS", "status": "OPEN",
            "opens": now - timedelta(days=1), "closes": now + timedelta(days=30),
            "country": "England", "limit": 3,
            "parties": ["CON", "LAB", "LD", "GRN", "REF"],
        },
        {
            "title": "2026 Local Council Elections (England & Wales)",
            "type": "LOCAL_ENGLAND_WALES", "scope": "LOCAL", "method": "FPTP", "status": "OPEN",
            "opens": now - timedelta(days=1), "closes": now + timedelta(days=30),
            "country": "Wales", "limit": 4,
            "parties": ["CON", "LAB", "LD", "GRN", "PC"],
        },
    ]

    CANDIDATE_NAMES = [
        [("James", "Hartley"), ("Sarah", "Pemberton"), ("William", "Ashworth"), ("Charlotte", "Forsyth"), ("Edward", "Blackwood")],
        [("Michael", "Brennan"), ("Angela", "Whitmore"), ("David", "O'Sullivan"), ("Catherine", "Redmond"), ("Stephen", "Gallagher")],
        [("Simon", "Cartwright"), ("Fiona", "Dalrymple"), ("Robert", "Wainwright"), ("Diana", "Ellison"), ("Timothy", "Greenhalgh")],
        [("Hamish", "MacLeod"), ("Catriona", "Fraser"), ("Douglas", "Campbell"), ("Moira", "Henderson"), ("Ewan", "Robertson")],
        [("Oliver", "Greenfield"), ("Zara", "Thornberry"), ("Ethan", "Rivers"), ("Megan", "Ashford"), ("Lucas", "Birchwood")],
        [("Patrick", "Stanton"), ("Louise", "Kingsley"), ("Brian", "Warburton"), ("Deborah", "Cromwell"), ("Kevin", "Hardcastle")],
        [("Rhys", "ap Gruffydd"), ("Cerys", "Morgan"), ("Gareth", "Llewellyn"), ("Bronwen", "Pritchard"), ("Owain", "Davies")],
        [("Sean", "O'Brien"), ("Mairead", "Ni Dhomhnaill"), ("Ciaran", "Murphy"), ("Siobhan", "Kelly"), ("Padraig", "Quinn")],
        [("William", "Johnston"), ("Ruth", "Crawford"), ("Samuel", "McAllister"), ("Elizabeth", "Hamilton"), ("Robert", "Baxter")],
        [("Daniel", "Carson"), ("Emma", "Reilly"), ("Stephen", "Neeson"), ("Claire", "Armstrong"), ("Peter", "McKenna")],
    ]
    party_abbr_list = [a for _, a in PARTIES]

    election_ids = {}
    candidate_count = 0
    vote_count = 0
    tally_count = 0
    seat_count = 0

    import random
    random.seed(42)

    for elec in ELECTIONS:
        eid = uid()
        await db.execute(text(
            "INSERT INTO election (id, title, election_type, scope, allocation_method, status, "
            "voting_opens, voting_closes, created_at, updated_at) "
            "VALUES (:id, :t, :et, :s, :am, :st, :vo, :vc, NOW(), NOW()) ON CONFLICT DO NOTHING"
        ), {"id": eid, "t": elec["title"], "et": elec["type"], "s": elec["scope"],
            "am": elec["method"], "st": elec["status"], "vo": elec["opens"], "vc": elec["closes"]})
        row = await db.execute(text("SELECT id FROM election WHERE title = :t"), {"t": elec["title"]})
        r = row.scalar()
        if r:
            eid = str(r)
        election_ids[elec["title"]] = eid

        # Get constituencies for this election
        const_rows = await db.execute(text(
            "SELECT id, name FROM constituency WHERE country = :c AND is_active = TRUE LIMIT :l"
        ), {"c": elec["country"], "l": elec["limit"]})
        consts = [(str(r[0]), r[1]) for r in const_rows]

        # Link constituencies
        for cid, _ in consts:
            await db.execute(text(
                "INSERT INTO election_constituency (election_id, constituency_id) "
                "VALUES (:e, :c) ON CONFLICT DO NOTHING"
            ), {"e": eid, "c": cid})

        # Seed candidates
        candidates_by_const = {}
        for ci, (cid, cname) in enumerate(consts):
            candidates_by_const[cid] = []
            for pi_idx, pabbr in enumerate(elec["parties"]):
                p_global_idx = party_abbr_list.index(pabbr)
                names = CANDIDATE_NAMES[p_global_idx][ci % len(CANDIDATE_NAMES[p_global_idx])]
                await db.execute(text(
                    "INSERT INTO candidate (id, election_id, constituency_id, first_name, last_name, party_id, is_active) "
                    "VALUES (:id, :e, :c, :fn, :ln, :p, TRUE) ON CONFLICT DO NOTHING"
                ), {"id": uid(), "e": eid, "c": cid, "fn": names[0], "ln": names[1], "p": party_ids[pabbr]})
                # Resolve actual ID (may differ if row already existed)
                row = await db.execute(text(
                    "SELECT id FROM candidate WHERE election_id = :e AND constituency_id = :c AND party_id = :p"
                ), {"e": eid, "c": cid, "p": party_ids[pabbr]})
                real_id = str(row.scalar())
                candidates_by_const[cid].append({"id": real_id, "party": pabbr, "pid": party_ids[pabbr]})
                candidate_count += 1

        # Seed votes, tallies, seat allocations for CLOSED elections
        if elec["status"] == "CLOSED":
            for cid, cname in consts:
                cands = candidates_by_const.get(cid, [])
                if not cands:
                    continue

                # Generate realistic vote counts
                total_votes = random.randint(25000, 55000)
                raw_shares = [random.random() for _ in cands]
                # Make first two parties stronger
                raw_shares[0] *= 2.5
                raw_shares[1] *= 2.0
                share_sum = sum(raw_shares)
                vote_counts_list = [max(1, int(total_votes * s / share_sum)) for s in raw_shares]

                # Seed votes (sample, not one per voter — just enough to demonstrate)
                for idx, cand in enumerate(cands):
                    num_votes = vote_counts_list[idx]
                    # Insert a representative sample of 20 actual vote rows per candidate
                    sample = min(20, num_votes)
                    for _ in range(sample):
                        await db.execute(text(
                            "INSERT INTO vote (id, election_id, constituency_id, candidate_id, party_id, "
                            "blind_token_hash, blind_token_hash_search_token, "
                            "receipt_code, receipt_code_search_token, email_sent, cast_at) "
                            "VALUES (:id, :e, :c, :cand, :p, :bth, :bts, :rc, :rcs, FALSE, :ca)"
                        ), {
                            "id": uid(), "e": eid, "c": cid, "cand": cand["id"], "p": cand["pid"],
                            "bth": fake_enc, "bts": fake_search_token(),
                            "rc": fake_enc, "rcs": fake_search_token(),
                            "ca": elec["closes"] - timedelta(hours=random.randint(1, 168)),
                        })
                        vote_count += 1

                    # Tally result per candidate per constituency
                    await db.execute(text(
                        "INSERT INTO tally_result (id, election_id, constituency_id, candidate_id, party_id, "
                        "vote_count, tallied_at) VALUES (:id, :e, :c, :cand, :p, :vc, :ta)"
                    ), {
                        "id": uid(), "e": eid, "c": cid, "cand": cand["id"], "p": cand["pid"],
                        "vc": num_votes, "ta": elec["closes"] + timedelta(hours=4),
                    })
                    tally_count += 1

                # Seat allocation — winner
                winner_idx = vote_counts_list.index(max(vote_counts_list))
                winner = cands[winner_idx]
                runner_up = sorted(vote_counts_list, reverse=True)[1] if len(vote_counts_list) > 1 else 0
                await db.execute(text(
                    "INSERT INTO seat_allocation (id, election_id, constituency_id, candidate_id, party_id, "
                    "allocation_type, seats_won, vote_share_pct, majority, counts_verified, status, verified_at) "
                    "VALUES (:id, :e, :c, :cand, :p, 'CONSTITUENCY', 1, :vsp, :maj, TRUE, 'VERIFIED', :va)"
                ), {
                    "id": uid(), "e": eid, "c": cid, "cand": winner["id"], "p": winner["pid"],
                    "vsp": round(max(vote_counts_list) / sum(vote_counts_list) * 100, 1),
                    "maj": max(vote_counts_list) - runner_up,
                    "va": elec["closes"] + timedelta(hours=8),
                })
                seat_count += 1

    summary["elections"] = len(election_ids)
    summary["candidates"] = candidate_count
    summary["votes"] = vote_count
    summary["tally_results"] = tally_count
    summary["seat_allocations"] = seat_count

    # ── 4. Referendums ────────────────────────────────────────────────
    REFERENDUMS = [
        {
            "title": "National Voting Age Referendum",
            "question": "Should the minimum voting age in the United Kingdom be lowered from 18 to 16 for all elections and referendums?",
            "description": "This referendum seeks to determine public opinion on whether 16 and 17 year olds should be granted the right to vote.",
            "scope": "NATIONAL", "status": "CLOSED",
            "opens": now - timedelta(days=14), "closes": now - timedelta(days=7),
            "country": None,
        },
        {
            "title": "Scottish Independence Referendum",
            "question": "Should Scotland be an independent country?",
            "description": "A consultative referendum on whether Scotland should become an independent sovereign state.",
            "scope": "REGIONAL", "status": "OPEN",
            "opens": now - timedelta(days=1), "closes": now + timedelta(days=30),
            "country": "Scotland", "limit": 6,
        },
        {
            "title": "Welsh Language in Schools Referendum",
            "question": "Should Welsh language education be mandatory in all primary and secondary schools in Wales?",
            "description": "This referendum asks whether the Welsh Government should mandate Welsh language instruction as a core subject.",
            "scope": "REGIONAL", "status": "OPEN",
            "opens": now - timedelta(days=1), "closes": now + timedelta(days=30),
            "country": "Wales", "limit": 4,
        },
    ]
    ref_count = 0
    ref_vote_count = 0
    ref_tally_count = 0

    for ref in REFERENDUMS:
        rid = uid()
        await db.execute(text(
            "INSERT INTO referendum (id, title, question, description, scope, status, "
            "voting_opens, voting_closes, is_active, created_at, updated_at) "
            "VALUES (:id, :t, :q, :d, :s, :st, :vo, :vc, TRUE, NOW(), NOW()) ON CONFLICT DO NOTHING"
        ), {"id": rid, "t": ref["title"], "q": ref["question"], "d": ref["description"],
            "s": ref["scope"], "st": ref["status"], "vo": ref["opens"], "vc": ref["closes"]})
        row = await db.execute(text("SELECT id FROM referendum WHERE title = :t"), {"t": ref["title"]})
        r = row.scalar()
        if r:
            rid = str(r)
        ref_count += 1

        # Link constituencies for regional referendums
        if ref.get("country"):
            crows = await db.execute(text(
                "SELECT id FROM constituency WHERE country = :c AND is_active = TRUE LIMIT :l"
            ), {"c": ref["country"], "l": ref.get("limit", 5)})
            for cr in crows:
                await db.execute(text(
                    "INSERT INTO referendum_constituency (referendum_id, constituency_id) "
                    "VALUES (:r, :c) ON CONFLICT DO NOTHING"
                ), {"r": rid, "c": str(cr[0])})

        # Seed referendum votes and tallies for CLOSED referendums
        if ref["status"] == "CLOSED":
            yes_total = random.randint(800000, 1200000)
            no_total = random.randint(600000, 1100000)
            # Sample vote rows
            for choice, count in [("YES", yes_total), ("NO", no_total)]:
                sample = min(50, count)
                for _ in range(sample):
                    await db.execute(text(
                        "INSERT INTO referendum_vote (id, referendum_id, choice, "
                        "blind_token_hash, blind_token_hash_search_token, "
                        "receipt_code, receipt_code_search_token, email_sent, cast_at) "
                        "VALUES (:id, :r, :ch, :bth, :bts, :rc, :rcs, FALSE, :ca)"
                    ), {
                        "id": uid(), "r": rid, "ch": choice,
                        "bth": fake_enc, "bts": fake_search_token(),
                        "rc": fake_enc, "rcs": fake_search_token(),
                        "ca": ref["closes"] - timedelta(hours=random.randint(1, 168)),
                    })
                    ref_vote_count += 1

                # Tally
                await db.execute(text(
                    "INSERT INTO tally_result (id, referendum_id, choice, vote_count, tallied_at) "
                    "VALUES (:id, :r, :ch, :vc, :ta)"
                ), {"id": uid(), "r": rid, "ch": choice, "vc": count,
                    "ta": ref["closes"] + timedelta(hours=4)})
                ref_tally_count += 1

    summary["referendums"] = ref_count
    summary["referendum_votes"] = ref_vote_count
    summary["referendum_tallies"] = ref_tally_count

    return {"status": "success", "summary": summary}


@router.get("/clear-voters")
async def clear_voters(service: AuthService = Depends(get_auth_service)) -> dict:
    """Temporary: remove all registered voters and cascading records
    (addresses, passports, device credentials, voter ledger, biometric challenges)."""
    from sqlalchemy import text

    db = service.session
    result = await db.execute(text("SELECT COUNT(*) FROM voter"))
    count = result.scalar()
    await db.execute(text("TRUNCATE voter CASCADE"))
    return {"status": "success", "voters_removed": count}


# Login — public (no token required)
@router.post(
    "/login",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
)
async def login(
    body: LoginRequest = Body(..., description="Login credentials."),
    service: AuthService = Depends(get_auth_service),
) -> TokenResponse:
    """Authenticate with username and password.

    Returns a JWT access token and refresh token.
    Failed attempts are tracked; the account locks after repeated failures.
    """
    return await service.login(body.username, body.password)


# Refresh — public (uses refresh token in body, not bearer)
@router.post(
    "/refresh",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
)
async def refresh_token(
    body: RefreshTokenRequest = Body(..., description="Refresh token."),
    service: AuthService = Depends(get_auth_service),
) -> TokenResponse:
    """Exchange a valid refresh token for a new access + refresh token pair."""
    return await service.refresh_token(body.refresh_token)


# Get current user profile — protected
@router.get(
    "/me",
    response_model=AuthenticatedUser,
    status_code=status.HTTP_200_OK,
)
async def get_me(
    current_user: TokenPayload = Depends(get_current_user),
) -> AuthenticatedUser:
    """Return the currently authenticated user's profile from the JWT."""
    return AuthenticatedUser(
        id=current_user.sub,
        username=current_user.username,
        role=current_user.role,
        must_reset_password=False,
    )


# Change password — protected
@router.post(
    "/change-password",
    response_model=ChangePasswordResponse,
    status_code=status.HTTP_200_OK,
)
async def change_password(
    body: ChangePasswordRequest = Body(..., description="Password change request."),
    current_user: TokenPayload = Depends(get_current_user),
    service: AuthService = Depends(get_auth_service),
) -> ChangePasswordResponse:
    """Change the currently authenticated user's password."""
    await service.change_password(
        official_id=UUID(current_user.sub),
        current_password=body.current_password,
        new_password=body.new_password,
    )
    return ChangePasswordResponse(detail="Password changed successfully")
