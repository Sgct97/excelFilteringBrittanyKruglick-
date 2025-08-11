"""Schema detection for variable-format input sheets.

This module detects canonical fields for names and addresses on the small input
sheet using documented header synonyms and minimal, deterministic heuristics.

Strict rules (from rules.yaml):
- Fail-fast on ambiguity or missing required fields when evaluating a match type
  (we will report which match types can run; integration decides to skip).
- No fallbacks or silent retries. Deterministic behavior only.

This module does NOT modify dataframes or run matching; it's standalone.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple, Set, Any
import re


# Canonical fields used downstream
CANONICAL_FIELDS: Set[str] = {
    "First_Name",
    "Last_Name",
    "FullName",
    "Address1",
    "Address2",
    "City",
    "State",
    "Zip",
    "FullAddress",
}


# Header synonyms (case-insensitive). Keep deterministic ordering via lists.
HEADER_SYNONYMS: Dict[str, List[str]] = {
    # Names
    "First_Name": ["First_Name", "FirstName", "First", "FName", "GivenName"],
    "Last_Name": ["Last_Name", "LastName", "Last", "LName", "Surname", "FamilyName"],
    "FullName": ["Full_Name", "FullName", "Name", "CustomerName", "ClientName", "ContactName"],
    # Addresses
    "Address1": [
        "Address1",
        "Address",
        "Addr1",
        "StreetAddress",
        "Street",
        "Address Line 1",
        "AddressLine1",
    ],
    "Address2": ["Address2", "Addr2", "Address Line 2", "AddressLine2"],
    "City": ["City", "Town", "Municipality", "Locality"],
    "State": ["State", "St", "Province", "Region"],
    "Zip": ["Zip", "Zip5", "ZipCode", "PostalCode", "Postcode"],
    "FullAddress": ["FullAddress", "MailingAddress", "Full Address"],
}


SUFFIX_TOKENS: Set[str] = {"JR", "SR", "II", "III", "IV"}


@dataclass(frozen=True)
class DetectedField:
    canonical: str
    source: Optional[str]  # actual header if present exactly
    derived: Optional[str]  # description of derivation rule


class SchemaError(RuntimeError):
    pass


def _normalize_header(header: str) -> str:
    """Normalize a header for case-insensitive, punctuation-insensitive comparison."""
    cleaned = re.sub(r"[^a-z0-9]", "", header.strip().lower())
    return cleaned


def _candidate_headers(df_columns: List[str], variants: List[str]) -> List[str]:
    target_norms = {_normalize_header(v) for v in variants}
    candidates: List[str] = []
    for col in df_columns:
        if _normalize_header(col) in target_norms:
            candidates.append(col)
    return candidates


def _pick_single_or_raise(canonical: str, candidates: List[str], file: str, sheet: str) -> Optional[str]:
    if len(candidates) > 1:
        detail = {
            "code": "SCHEMA_AMBIGUOUS_HEADER",
            "stage": "schema_detection",
            "file": file,
            "sheet": sheet,
            "columns": candidates,
            "detail": f"Multiple columns match canonical '{canonical}'",
            "repro": "Remove/rename duplicate-like headers so only one maps to the canonical field.",
        }
        raise SchemaError(str(detail))
    return candidates[0] if candidates else None


def split_full_name(full_name: str) -> Tuple[str, str]:
    """Split a full name into (first, last) using last space rule with suffix handling.

    If a suffix token is present at the end, treat it as part of the last name.
    """
    name = (full_name or "").strip()
    if not name:
        return "", ""
    parts = name.split()
    if len(parts) == 1:
        return parts[0], ""
    # Handle suffix
    if parts[-1].rstrip(".").upper() in SUFFIX_TOKENS and len(parts) >= 3:
        first = " ".join(parts[:-2])
        last = " ".join(parts[-2:])
        return first, last
    first = " ".join(parts[:-1])
    last = parts[-1]
    return first, last


def detect_schema(
    df_columns: List[str], *, file: str, sheet: str
) -> Dict[str, DetectedField]:
    """Detect schema for a dataframe's columns.

    Returns a mapping of canonical field -> DetectedField where source is the
    original header if present, or derived describes how it can be produced later.
    No data is transformed here; this is headers-only detection and validation.
    """
    mapping: Dict[str, DetectedField] = {}

    # First pass: direct header matches (exact one per canonical or none)
    for canonical, variants in HEADER_SYNONYMS.items():
        candidates = _candidate_headers(df_columns, variants)
        chosen = _pick_single_or_raise(canonical, candidates, file, sheet)
        if chosen:
            mapping[canonical] = DetectedField(canonical=canonical, source=chosen, derived=None)

    # Consider derivable fields for names and addresses
    # FullName derivable from First/Last
    if "FullName" not in mapping and ("First_Name" in mapping and "Last_Name" in mapping):
        mapping["FullName"] = DetectedField(canonical="FullName", source=None, derived="concat(First_Name, ' ', Last_Name)")

    # First/Last derivable from FullName
    if ("First_Name" not in mapping or "Last_Name" not in mapping) and ("FullName" in mapping):
        if "First_Name" not in mapping:
            mapping["First_Name"] = DetectedField(canonical="First_Name", source=None, derived="split(FullName).first")
        if "Last_Name" not in mapping:
            mapping["Last_Name"] = DetectedField(canonical="Last_Name", source=None, derived="split(FullName).last")

    # FullAddress derivable from parts
    addr_parts = ["Address1", "City", "State", "Zip"]
    if "FullAddress" not in mapping and all(p in mapping for p in addr_parts):
        mapping["FullAddress"] = DetectedField(
            canonical="FullAddress", source=None, derived="concat(Address1, ', ', City, ', ', State, ' ', Zip)"
        )

    return mapping


def evaluate_match_types(mapping: Dict[str, DetectedField]) -> Dict[str, Dict[str, Any]]:
    """Report which match types can run, and why if they cannot."""
    report: Dict[str, Dict[str, Any]] = {}

    # FullName requires first+last or fullname
    fullname_ok = ("First_Name" in mapping and "Last_Name" in mapping) or ("FullName" in mapping)
    report["FullName"] = {
        "enabled": bool(fullname_ok),
        "reason": None if fullname_ok else "Missing First/Last and FullName",
        "required": ["First_Name & Last_Name"],
    }

    # LastNameAddress requires Last_Name and FullAddress (or derivable parts)
    last_ok = "Last_Name" in mapping
    fulladdr_ok = "FullAddress" in mapping or (
        all(k in mapping for k in ("Address1", "City", "State", "Zip"))
    )
    report["LastNameAddress"] = {
        "enabled": bool(last_ok and fulladdr_ok),
        "reason": None if (last_ok and fulladdr_ok) else "Missing Last_Name or FullAddress/parts",
        "required": ["Last_Name", "FullAddress or Address1+City+State+Zip"],
    }

    # FullAddress requires FullAddress (or derivable parts)
    fa_ok = "FullAddress" in mapping or (
        all(k in mapping for k in ("Address1", "City", "State", "Zip"))
    )
    report["FullAddress"] = {
        "enabled": bool(fa_ok),
        "reason": None if fa_ok else "Missing FullAddress/parts",
        "required": ["FullAddress or Address1+City+State+Zip"],
    }

    return report


__all__ = [
    "DetectedField",
    "SchemaError",
    "detect_schema",
    "evaluate_match_types",
    "split_full_name",
]


