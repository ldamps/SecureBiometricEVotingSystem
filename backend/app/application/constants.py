from enum import Enum

# Resource enums
class Resource(Enum):
    """Resources for the API."""
    HEALTH = "health"
    CONSTITUENCY = "constituency"
    ELECTION = "election"
    VOTER = "voter"
    ADDRESS = "address"
    BALLOT_TOKEN = "ballot_token"
    VOTE = "vote"
    SEAT_ALLOCATION = "seat_allocation"
    TALLY_RESULT = "tally_result"
    