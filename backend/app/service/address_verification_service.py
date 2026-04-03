"""Address verification via OCR.

Extracts text from an uploaded proof-of-address document (PDF, JPG, PNG)
using Tesseract OCR, then checks whether the voter's registered address
appears in the extracted text.

The uploaded file is held in memory only for the duration of the request
and is **never persisted** to disk or database.
"""

from __future__ import annotations

import io
import re
import structlog
from PIL import Image
from pdf2image import convert_from_bytes
import pytesseract

logger = structlog.get_logger()


def _normalise(text: str) -> str:
    """Lower-case, collapse whitespace, strip punctuation."""
    text = text.lower()
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def extract_text_from_image(image_bytes: bytes, content_type: str) -> str:
    """Run Tesseract OCR on an image buffer and return the raw text."""
    image = Image.open(io.BytesIO(image_bytes))
    return pytesseract.image_to_string(image)


def extract_text_from_pdf(pdf_bytes: bytes) -> str:
    """Convert each PDF page to an image, OCR it, and concatenate."""
    pages = convert_from_bytes(pdf_bytes, dpi=200)
    texts: list[str] = []
    for page in pages:
        texts.append(pytesseract.image_to_string(page))
    return "\n".join(texts)


def extract_text(file_bytes: bytes, content_type: str) -> str:
    """Dispatch to the appropriate extractor based on MIME type."""
    if content_type == "application/pdf":
        return extract_text_from_pdf(file_bytes)
    return extract_text_from_image(file_bytes, content_type)


def verify_address_in_text(
    extracted_text: str,
    address_line1: str,
    city: str,
    postcode: str,
) -> dict:
    """Check whether the key address components appear in the OCR text.

    Returns a dict with per-field match results and an overall verdict.
    """
    norm_text = _normalise(extracted_text)

    results: dict[str, bool] = {}

    if address_line1:
        results["address_line1"] = _normalise(address_line1) in norm_text

    if postcode:
        # Postcodes: strip spaces for a looser match
        norm_postcode = _normalise(postcode).replace(" ", "")
        norm_text_no_spaces = norm_text.replace(" ", "")
        results["postcode"] = norm_postcode in norm_text_no_spaces

    if city:
        results["city"] = _normalise(city) in norm_text

    matched = sum(1 for v in results.values() if v)
    total = len(results) or 1

    # Require at least 2 out of 3 fields to match (or all if fewer fields).
    passed = matched >= min(2, total)

    logger.info(
        "address_verification_result",
        results=results,
        matched=matched,
        total=total,
        passed=passed,
    )

    return {
        "passed": passed,
        "matched_fields": matched,
        "total_fields": total,
        "details": results,
    }
