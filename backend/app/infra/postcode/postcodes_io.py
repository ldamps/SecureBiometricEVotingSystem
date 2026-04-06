"""Postcode lookup via the free postcodes.io API."""

import httpx
import structlog
from dataclasses import dataclass
from typing import Optional

logger = structlog.get_logger()

POSTCODES_IO_BASE = "https://api.postcodes.io"


@dataclass
class PostcodeLookupResult:
    """Result of a postcode lookup."""
    postcode: str
    constituency: Optional[str]
    country: Optional[str]


async def lookup_postcode(postcode: str) -> Optional[PostcodeLookupResult]:
    """Look up a UK postcode and return its parliamentary constituency.

    Uses the postcodes.io API (free, no auth required).
    Returns None if the postcode is invalid or the API is unreachable.
    """
    normalised = postcode.strip().upper().replace(" ", "")
    if not normalised:
        return None

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(f"{POSTCODES_IO_BASE}/postcodes/{normalised}")

        if resp.status_code != 200:
            logger.warning(
                "Postcode lookup failed",
                postcode=normalised,
                status=resp.status_code,
            )
            return None

        data = resp.json()
        if data.get("status") != 200 or not data.get("result"):
            return None

        result = data["result"]
        # 2024 boundary constituencies use parliamentary_constituency_2025
        constituency = (
            result.get("parliamentary_constituency_2025")
            or result.get("parliamentary_constituency")
        )
        country = result.get("country")

        return PostcodeLookupResult(
            postcode=normalised,
            constituency=constituency,
            country=country,
        )

    except Exception:
        logger.exception("Postcode lookup error", postcode=normalised)
        return None
