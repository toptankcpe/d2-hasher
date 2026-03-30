from __future__ import annotations

import os
from pathlib import Path
from typing import List, Optional

import pandas as pd
from charset_normalizer import from_bytes

from .core import multilayer_hash, mask_value


def _detect_encoding(file_path: str) -> str:
    with open(file_path, "rb") as f:
        raw = f.read(65536)
    result = from_bytes(raw).best()
    if result is None:
        return "utf-8"
    return str(result.encoding)


def _detect_delimiter(file_path: str, encoding: str) -> str:
    """Sniff delimiter from the first line of the file."""
    import csv

    with open(file_path, "r", encoding=encoding, errors="replace") as f:
        sample = f.readline()
    try:
        dialect = csv.Sniffer().sniff(sample, delimiters=",\t|;")
        return dialect.delimiter
    except csv.Error:
        return ","


def hash_columns(
    columns: List[str],
    secret_salts: List[str],
    input_file: Optional[str] = None,
    df: Optional[pd.DataFrame] = None,
    output: Optional[str] = None,
    chunksize: int = 10_000,
    delimiter: Optional[str] = None,
    output_sep: Optional[str] = None,
    on_chunk=None,
    mask_columns: Optional[List[str]] = None,
    mask_char: str = "*",
    mask_length: int = 4,
) -> Optional[pd.DataFrame]:
    """
    Hash specified columns of a CSV/TXT file or a DataFrame using
    Multilayer SHA-512 hashing.

    Args:
        columns: Column names to hash.
        secret_salts: Secret salts applied in order for each hash round.
        input_file: Path to a delimiter-separated input file (CSV or TXT).
        df: A pandas DataFrame to hash in-memory. Mutually exclusive approach
            with input_file — if both are given, df takes precedence.
        output: Output file path. Defaults to ``<input_stem>_hashed.csv``.
            Ignored when df is supplied without input_file.
        chunksize: Rows per chunk when reading large files. Default 10 000.
        delimiter: Column delimiter for input_file. Auto-detected when None.
        mask_columns: Column names to mask with fixed characters instead of hashing.
        mask_char: Character to use for masking (default: "*").
        mask_length: Number of masking characters (default: 4).

    Returns:
        When *df* is provided (and no input_file): returns the hashed
        DataFrame (the original object is not mutated).
        When input_file is provided: writes the output file and returns None.

    Raises:
        ValueError: If neither input_file nor df is provided, or if specified
            columns are missing.
    """
    if len(secret_salts) != 3:
        raise ValueError("secret_salts must contain exactly 3 elements.")

    if input_file is None and df is None:
        raise ValueError("Provide either 'input_file' or 'df'.")

    if mask_columns is None:
        mask_columns = []

    # --- In-memory DataFrame path ---
    if df is not None and input_file is None:
        all_cols = columns + mask_columns
        missing = [c for c in all_cols if c not in df.columns]
        if missing:
            raise ValueError(f"Columns not found in DataFrame: {missing}")
        result = df.copy()
        for col in columns:
            result[col] = result[col].apply(
                lambda v: multilayer_hash(v, secret_salts)
            )
        for col in mask_columns:
            result[col] = result[col].apply(
                lambda v: mask_value(v, mask_char, mask_length)
            )
        return result

    # --- File path ---
    input_file = str(input_file)
    if not os.path.isfile(input_file):
        raise FileNotFoundError(f"Input file not found: {input_file}")

    encoding = _detect_encoding(input_file)
    sep = delimiter if delimiter is not None else _detect_delimiter(input_file, encoding)

    # Count total rows for progress reporting (only if callback given)
    total_rows = None
    if on_chunk is not None:
        with open(input_file, "r", encoding=encoding, errors="replace") as _f:
            total_rows = sum(1 for _ in _f) - 1  # subtract header
        total_rows = max(total_rows, 1)

    if output is None:
        p = Path(input_file)
        output = str(p.parent / f"{p.stem}_hashed.csv")

    first_chunk = True
    rows_done = 0
    for chunk in pd.read_csv(
        input_file,
        sep=sep,
        encoding=encoding,
        chunksize=chunksize,
        dtype=str,
        keep_default_na=False,
    ):
        all_cols = columns + mask_columns
        missing = [c for c in all_cols if c not in chunk.columns]
        if missing:
            raise ValueError(f"Columns not found in file: {missing}")

        for col in columns:
            # Replace empty strings / "nan" strings that came from dtype=str
            chunk[col] = chunk[col].apply(
                lambda v: multilayer_hash(
                    None if v in ("", "nan", "NaN", "NULL", "null") else v,
                    secret_salts,
                )
            )

        for col in mask_columns:
            chunk[col] = chunk[col].apply(
                lambda v: mask_value(
                    None if v in ("", "nan", "NaN", "NULL", "null") else v,
                    mask_char,
                    mask_length,
                )
            )

        chunk.to_csv(
            output,
            index=False,
            sep=output_sep if output_sep is not None else sep,
            mode="w" if first_chunk else "a",
            header=first_chunk,
        )
        first_chunk = False

        if on_chunk is not None and total_rows is not None:
            rows_done = min(rows_done + len(chunk), total_rows)
            on_chunk(rows_done, total_rows)

    return None
