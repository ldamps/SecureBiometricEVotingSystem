"""UK postcode validation.

Uses the standard UK government postcode regex pattern to validate
format. Covers all valid UK postcode formats including special cases
(GIR 0AA, BFPO).
"""

import re

# Standard UK postcode regex — matches the formats defined by Royal Mail.
# Area codes: A9, A99, A9A, AA9, AA99, AA9A
# Inward code: 9AA
# Also supports GIR 0AA and BFPO (British Forces Post Office) postcodes.
_UK_POSTCODE_RE = re.compile(
    r"^(GIR\s?0AA|"
    r"BFPO\s?\d{1,4}|"
    r"[A-Z]{1,2}\d[A-Z\d]?\s?\d[A-Z]{2}"
    r")$",
    re.IGNORECASE,
)


def is_valid_uk_postcode(postcode: str) -> bool:
    """Return True if *postcode* is a syntactically valid UK postcode.

    Normalises whitespace before checking so that inputs like
    ``"SW1A  1AA"`` (double space) are accepted.
    """
    cleaned = re.sub(r"\s+", " ", postcode.strip())
    return bool(_UK_POSTCODE_RE.match(cleaned))


def normalise_postcode(postcode: str) -> str:
    """Normalise a UK postcode to uppercase with a single space before the inward code.

    e.g. "sw1a  1aa" -> "SW1A 1AA"
    """
    cleaned = re.sub(r"\s+", "", postcode.strip().upper())
    if len(cleaned) < 4:
        return cleaned
    return f"{cleaned[:-3]} {cleaned[-3:]}"
