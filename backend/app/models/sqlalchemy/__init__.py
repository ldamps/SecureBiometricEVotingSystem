"""SQLAlchemy ORM models for the Secure Biometric E-Voting System.

Import order respects FK dependencies so relationship() names resolve.

How to use:
  - Create an engine and Session (sync or async) bound to your DB.
  - Import models from app.models.sqlalchemy; use Session to add/query/update/delete.
  - Use Base.metadata.create_all(engine) to create tables, or use Alembic for migrations.
"""

from app.models.sqlalchemy.constituency import Constituency
from app.models.sqlalchemy.encryption_key import EncryptionKey
from app.models.sqlalchemy.audit_log import AuditLog
from app.models.sqlalchemy.election_official import ElectionOfficial
from app.models.sqlalchemy.election import Election
from app.models.sqlalchemy.voter import Voter
from app.models.sqlalchemy.address import Address
from app.models.sqlalchemy.biometric_template import BiometricTemplate
from app.models.sqlalchemy.voter_ledger import VoterLedger
from app.models.sqlalchemy.ballot_token import BallotToken
from app.models.sqlalchemy.candidate import Candidate
from app.models.sqlalchemy.seat_allocation import SeatAllocation
from app.models.sqlalchemy.vote import Vote
from app.models.sqlalchemy.tally_result import TallyResult
from app.models.sqlalchemy.error_report import ErrorReport
from app.models.sqlalchemy.investigation import Investigation

__all__ = [
    "Address",
    "AuditLog",
    "BallotToken",
    "BiometricTemplate",
    "Candidate",
    "Constituency",
    "Election",
    "ElectionOfficial",
    "EncryptionKey",
    "ErrorReport",
    "Investigation",
    "SeatAllocation",
    "TallyResult",
    "Voter",
    "VoterLedger",
    "Vote",
]
