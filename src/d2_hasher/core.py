import hashlib
from typing import Any, List, Optional

_THAI_DIGIT_TABLE = str.maketrans("๐๑๒๓๔๕๖๗๘๙", "0123456789")


def normalize_cid(value: str) -> Optional[str]:
    """
    Normalize a Thai national ID (CID) string.

    - Translates Thai digits (๐-๙) to Arabic digits.
    - Removes dashes, slashes, spaces, and dots.
    - Only applies full normalization when exactly 13 digits are present;
      otherwise returns the raw stripped value as-is.

    Args:
        value: Raw CID string.

    Returns:
        Normalized string, or None if value is None.
    """
    if value is None:
        return None

    raw = str(value).strip()

    digit_count = sum(
        1 for ch in raw
        if ch.isdigit() or ch in "๐๑๒๓๔๕๖๗๘๙"
    )

    if digit_count != 13:
        return raw

    return (
        raw.translate(_THAI_DIGIT_TABLE)
           .replace("-", "")
           .replace("/", "")
           .replace(" ", "")
           .replace(".", "")
    )


def multilayer_hash(value: Any, secret_salts: List[str]) -> Optional[str]:
    """
    Multilayer SHA-512 hashing with secret salts.

    Normalizes the input value, then iteratively hashes it with each
    secret salt using SHA-512, producing a 128-character hex string.

    Args:
        value: Input value. Returns None if null/NaN.
        secret_salts: List of secret salt strings, applied in order.

    Returns:
        128-character lowercase hex string, or None if value is null/NaN.
    """
    if value is None:
        return None

    # Handle NaN (float('nan') or pandas NA)
    try:
        import math
        if isinstance(value, float) and math.isnan(value):
            return None
    except (TypeError, ValueError):
        pass

    v = normalize_cid(str(value))

    for salt in secret_salts:
        h = hashlib.sha512()
        h.update((v + salt).encode("utf-8"))
        v = h.hexdigest()

    return v
