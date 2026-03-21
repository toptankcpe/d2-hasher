import io
import os
import textwrap

import pandas as pd
import pytest

from d2_hasher import hash_columns
from d2_hasher.core import multilayer_hash


SALTS = ["salt_a", "salt_b"]


# ---------------------------------------------------------------------------
# DataFrame path
# ---------------------------------------------------------------------------

class TestHashColumnsDataFrame:
    def _sample_df(self):
        return pd.DataFrame(
            {
                "name": ["Alice", "BOB", "  carol  "],
                "age": [30, 25, 40],
                "cid": ["1234567890123", "9876543210987", None],
            }
        )

    def test_returns_dataframe(self):
        df = self._sample_df()
        result = hash_columns(columns=["name"], secret_salts=SALTS, df=df)
        assert isinstance(result, pd.DataFrame)

    def test_does_not_mutate_original(self):
        df = self._sample_df()
        original_name = df["name"].tolist()
        hash_columns(columns=["name"], secret_salts=SALTS, df=df)
        assert df["name"].tolist() == original_name

    def test_hashed_column_matches_core(self):
        df = self._sample_df()
        result = hash_columns(columns=["name"], secret_salts=SALTS, df=df)
        for orig, hashed in zip(df["name"], result["name"]):
            assert hashed == multilayer_hash(orig, SALTS)

    def test_non_hashed_columns_unchanged(self):
        df = self._sample_df()
        result = hash_columns(columns=["name"], secret_salts=SALTS, df=df)
        pd.testing.assert_series_equal(result["age"], df["age"])

    def test_null_values_become_none(self):
        df = self._sample_df()
        result = hash_columns(columns=["cid"], secret_salts=SALTS, df=df)
        assert result["cid"].iloc[2] is None

    def test_multiple_columns(self):
        df = self._sample_df()
        result = hash_columns(columns=["name", "cid"], secret_salts=SALTS, df=df)
        assert result["name"].iloc[0] == multilayer_hash("Alice", SALTS)
        assert result["cid"].iloc[0] == multilayer_hash("1234567890123", SALTS)

    def test_missing_column_raises(self):
        df = self._sample_df()
        with pytest.raises(ValueError, match="not found in DataFrame"):
            hash_columns(columns=["nonexistent"], secret_salts=SALTS, df=df)

    def test_no_input_raises(self):
        with pytest.raises(ValueError):
            hash_columns(columns=["name"], secret_salts=SALTS)


# ---------------------------------------------------------------------------
# File path
# ---------------------------------------------------------------------------

class TestHashColumnsFile:
    def _write_csv(self, tmp_path, content: str, filename: str = "input.csv") -> str:
        path = tmp_path / filename
        path.write_text(textwrap.dedent(content), encoding="utf-8")
        return str(path)

    def test_creates_output_file(self, tmp_path):
        csv = self._write_csv(
            tmp_path,
            """\
            name,age
            Alice,30
            Bob,25
            """,
        )
        hash_columns(columns=["name"], secret_salts=SALTS, input_file=csv)
        assert os.path.isfile(str(tmp_path / "input_hashed.csv"))

    def test_hashed_values_match_core(self, tmp_path):
        csv = self._write_csv(
            tmp_path,
            """\
            name,age
            Alice,30
            BOB,25
            """,
        )
        out = str(tmp_path / "out.csv")
        hash_columns(
            columns=["name"], secret_salts=SALTS, input_file=csv, output=out
        )
        result = pd.read_csv(out)
        assert result["name"].iloc[0] == multilayer_hash("Alice", SALTS)
        assert result["name"].iloc[1] == multilayer_hash("BOB", SALTS)

    def test_non_hashed_columns_preserved(self, tmp_path):
        csv = self._write_csv(
            tmp_path,
            """\
            name,age
            Alice,30
            """,
        )
        out = str(tmp_path / "out.csv")
        hash_columns(
            columns=["name"], secret_salts=SALTS, input_file=csv, output=out
        )
        result = pd.read_csv(out)
        assert result["age"].iloc[0] == 30

    def test_tab_delimiter(self, tmp_path):
        tsv = self._write_csv(
            tmp_path,
            "name\tage\nAlice\t30\n",
            filename="input.tsv",
        )
        out = str(tmp_path / "out.csv")
        hash_columns(
            columns=["name"],
            secret_salts=SALTS,
            input_file=tsv,
            output=out,
            delimiter="\t",
        )
        result = pd.read_csv(out)
        assert result["name"].iloc[0] == multilayer_hash("Alice", SALTS)

    def test_missing_file_raises(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            hash_columns(
                columns=["name"],
                secret_salts=SALTS,
                input_file=str(tmp_path / "nonexistent.csv"),
            )

    def test_missing_column_raises(self, tmp_path):
        csv = self._write_csv(tmp_path, "name,age\nAlice,30\n")
        with pytest.raises(ValueError, match="not found in file"):
            hash_columns(
                columns=["nonexistent"],
                secret_salts=SALTS,
                input_file=csv,
            )

    def test_chunksize_respected(self, tmp_path):
        rows = "\n".join(f"User{i},{i}" for i in range(50))
        csv = self._write_csv(tmp_path, f"name,age\n{rows}\n")
        out = str(tmp_path / "out.csv")
        hash_columns(
            columns=["name"],
            secret_salts=SALTS,
            input_file=csv,
            output=out,
            chunksize=10,
        )
        result = pd.read_csv(out)
        assert len(result) == 50
