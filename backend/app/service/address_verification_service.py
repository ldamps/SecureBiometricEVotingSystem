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

    At least address_line1 or postcode must be provided.
    Postcode matching uses word-boundary matching to prevent partial matches.
    Requires at least 2 out of 3 fields to match (or all if fewer provided).
    """
    norm_text = _normalise(extracted_text)

    fields_provided = []
    if address_line1 and address_line1.strip():
        fields_provided.append("address_line1")
    if postcode and postcode.strip():
        fields_provided.append("postcode")
    if city and city.strip():
        fields_provided.append("city")

    if not fields_provided:
        logger.warning("address_verification_rejected: no address fields provided")
        return {
            "passed": False,
            "matched_fields": 0,
            "total_fields": 0,
            "details": {},
        }

    results: dict[str, bool] = {}

    if "address_line1" in fields_provided:
        results["address_line1"] = _normalise(address_line1) in norm_text

    if "postcode" in fields_provided:
        # Match the postcode as a word-bounded token.
        # Try both the spaced form (e.g. "sw1a 1aa") and compact form ("sw1a1aa").
        norm_postcode = _normalise(postcode).replace(" ", "")
        if len(norm_postcode) >= 4:
            spaced = f"{norm_postcode[:-3]} {norm_postcode[-3:]}"
        else:
            spaced = norm_postcode
        spaced_pat = re.escape(spaced)
        compact_pat = re.escape(norm_postcode)
        results["postcode"] = bool(
            re.search(rf"\b{spaced_pat}\b", norm_text)
            or re.search(rf"\b{compact_pat}\b", norm_text)
        )

    if "city" in fields_provided:
        results["city"] = _normalise(city) in norm_text

    matched = sum(1 for v in results.values() if v)
    total = len(results)

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
