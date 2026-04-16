"""Unit tests for VotingService — ballot validation and double-vote prevention."""

import uuid
from unittest.mock import MagicMock

import pytest

from app.application.core.exceptions import ValidationError
from app.models.schemas.vote import CastVoteRequest, RankedPreference
from app.service.voting_service import VotingService


# ---------------------------------------------------------------------------
# _validate_ballot_payload is a static method — test it directly
# ---------------------------------------------------------------------------

class TestValidateBallotPayload:
    """Tests for VotingService._validate_ballot_payload (static method)."""

    def _make_request(self, **overrides) -> CastVoteRequest:
        defaults = dict(
            voter_id=str(uuid.uuid4()),
            election_id=str(uuid.uuid4()),
            constituency_id=str(uuid.uuid4()),
            candidate_id=str(uuid.uuid4()),
            party_id=None,
            ranked_preferences=None,
            blind_token_hash="abc123",
            send_email_confirmation=False,
        )
        defaults.update(overrides)
        return CastVoteRequest(**defaults)

    # ── FPTP ──

    def test_fptp_valid_request_passes(self):
        req = self._make_request(candidate_id=str(uuid.uuid4()), constituency_id=str(uuid.uuid4()))
        VotingService._validate_ballot_payload("FPTP", req)

    def test_fptp_missing_candidate_raises(self):
        req = self._make_request(candidate_id=None)
        with pytest.raises(ValidationError, match="candidate_id"):
            VotingService._validate_ballot_payload("FPTP", req)

    def test_fptp_missing_constituency_raises(self):
        req = self._make_request(constituency_id=None)
        with pytest.raises(ValidationError, match="constituency_id"):
            VotingService._validate_ballot_payload("FPTP", req)

    # ── AMS ──

    def test_ams_candidate_only_passes(self):
        req = self._make_request(candidate_id=str(uuid.uuid4()), party_id=None)
        VotingService._validate_ballot_payload("AMS", req)

    def test_ams_party_only_passes(self):
        req = self._make_request(candidate_id=None, party_id=str(uuid.uuid4()))
        VotingService._validate_ballot_payload("AMS", req)

    def test_ams_both_candidate_and_party_passes(self):
        req = self._make_request(
            candidate_id=str(uuid.uuid4()), party_id=str(uuid.uuid4())
        )
        VotingService._validate_ballot_payload("AMS", req)

    def test_ams_neither_candidate_nor_party_raises(self):
        req = self._make_request(candidate_id=None, party_id=None)
        with pytest.raises(ValidationError, match="AMS"):
            VotingService._validate_ballot_payload("AMS", req)

    # ── STV ──

    def test_stv_valid_ranked_preferences_passes(self):
        prefs = [
            RankedPreference(candidate_id=str(uuid.uuid4()), preference_rank=1),
            RankedPreference(candidate_id=str(uuid.uuid4()), preference_rank=2),
            RankedPreference(candidate_id=str(uuid.uuid4()), preference_rank=3),
        ]
        req = self._make_request(candidate_id=None, ranked_preferences=prefs)
        VotingService._validate_ballot_payload("STV", req)

    def test_stv_missing_ranked_preferences_raises(self):
        req = self._make_request(candidate_id=None, ranked_preferences=None)
        with pytest.raises(ValidationError, match="ranked_preferences"):
            VotingService._validate_ballot_payload("STV", req)

    def test_stv_empty_ranked_preferences_raises(self):
        req = self._make_request(candidate_id=None, ranked_preferences=[])
        with pytest.raises(ValidationError, match="ranked_preferences"):
            VotingService._validate_ballot_payload("STV", req)

    def test_stv_non_consecutive_ranks_raises(self):
        prefs = [
            RankedPreference(candidate_id=str(uuid.uuid4()), preference_rank=1),
            RankedPreference(candidate_id=str(uuid.uuid4()), preference_rank=3),  # gap
        ]
        req = self._make_request(candidate_id=None, ranked_preferences=prefs)
        with pytest.raises(ValidationError, match="consecutive"):
            VotingService._validate_ballot_payload("STV", req)

    def test_stv_duplicate_ranks_raises(self):
        prefs = [
            RankedPreference(candidate_id=str(uuid.uuid4()), preference_rank=1),
            RankedPreference(candidate_id=str(uuid.uuid4()), preference_rank=1),  # dup
        ]
        req = self._make_request(candidate_id=None, ranked_preferences=prefs)
        with pytest.raises(ValidationError, match="consecutive"):
            VotingService._validate_ballot_payload("STV", req)

    def test_stv_ranks_not_starting_from_one_raises(self):
        prefs = [
            RankedPreference(candidate_id=str(uuid.uuid4()), preference_rank=2),
            RankedPreference(candidate_id=str(uuid.uuid4()), preference_rank=3),
        ]
        req = self._make_request(candidate_id=None, ranked_preferences=prefs)
        with pytest.raises(ValidationError, match="consecutive"):
            VotingService._validate_ballot_payload("STV", req)

    # ── Alternative Vote (same rules as STV) ──

    def test_av_valid_ranked_preferences_passes(self):
        prefs = [
            RankedPreference(candidate_id=str(uuid.uuid4()), preference_rank=1),
            RankedPreference(candidate_id=str(uuid.uuid4()), preference_rank=2),
        ]
        req = self._make_request(candidate_id=None, ranked_preferences=prefs)
        VotingService._validate_ballot_payload("ALTERNATIVE_VOTE", req)

    def test_av_missing_preferences_raises(self):
        req = self._make_request(candidate_id=None, ranked_preferences=None)
        with pytest.raises(ValidationError, match="ranked_preferences"):
            VotingService._validate_ballot_payload("ALTERNATIVE_VOTE", req)
