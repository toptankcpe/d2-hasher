import hashlib
import pytest
from d2_hasher.core import multilayer_hash, normalize_cid


def _expected(value: str, salts: list[str]) -> str:
    """Mirror the exact normalization used by multilayer_hash."""
    v = normalize_cid(str(value))
    for salt in salts:
        h = hashlib.sha512()
        h.update((v + salt).encode("utf-8"))
        v = h.hexdigest()
    return v


SALTS = ["salt_a", "salt_b"]


class TestNullInputs:
    def test_none_returns_none(self):
        assert multilayer_hash(None, SALTS) is None

    def test_float_nan_returns_none(self):
        assert multilayer_hash(float("nan"), SALTS) is None


class TestNormalizeCid:
    def test_none_returns_none(self):
        assert normalize_cid(None) is None

    def test_strips_whitespace(self):
        assert normalize_cid("  1234567890123  ") == "1234567890123"

    def test_removes_dashes(self):
        assert normalize_cid("1-2345-67890-12-3") == "1234567890123"

    def test_removes_slashes(self):
        assert normalize_cid("1/2345/67890/12/3") == "1234567890123"

    def test_removes_spaces(self):
        assert normalize_cid("1 2345 67890 12 3") == "1234567890123"

    def test_removes_dots(self):
        assert normalize_cid("1.2345.67890.12.3") == "1234567890123"

    def test_thai_digits_converted(self):
        assert normalize_cid("๑๒๓๔๕๖๗๘๙๐๑๒๓") == "1234567890123"

    def test_mixed_thai_arabic_digits(self):
        assert normalize_cid("1234567890๑๒๓") == "1234567890123"

    def test_non_13_digit_returns_raw(self):
        raw = "  hello  "
        assert normalize_cid(raw) == "hello"

    def test_12_digit_cid_returns_raw(self):
        assert normalize_cid("123456789012") == "123456789012"


class TestNormalization:
    def test_strips_whitespace(self):
        assert multilayer_hash("  hello  ", SALTS) == multilayer_hash("hello", SALTS)

    def test_cid_with_dashes_normalized(self):
        assert multilayer_hash("1-2345-67890-12-3", SALTS) == multilayer_hash("1234567890123", SALTS)

    def test_thai_cid_normalized(self):
        assert multilayer_hash("๑๒๓๔๕๖๗๘๙๐๑๒๓", SALTS) == multilayer_hash("1234567890123", SALTS)


class TestOutput:
    def test_returns_128_hex_chars(self):
        result = multilayer_hash("test", SALTS)
        assert isinstance(result, str)
        assert len(result) == 128
        assert all(c in "0123456789abcdef" for c in result)

    def test_single_salt(self):
        salts = ["only_salt"]
        result = multilayer_hash("value", salts)
        assert result == _expected("value", salts)

    def test_multiple_salts(self):
        result = multilayer_hash("value", SALTS)
        assert result == _expected("value", SALTS)

    def test_deterministic(self):
        assert multilayer_hash("abc", SALTS) == multilayer_hash("abc", SALTS)

    def test_different_salts_different_output(self):
        r1 = multilayer_hash("abc", ["salt_x"])
        r2 = multilayer_hash("abc", ["salt_y"])
        assert r1 != r2

    def test_integer_input(self):
        result = multilayer_hash(123, SALTS)
        assert result == _expected("123", SALTS)

    def test_empty_salt_list(self):
        # No hashing rounds; normalize_cid returns the non-13-digit raw value
        result = multilayer_hash("hello", [])
        assert result == "hello"
