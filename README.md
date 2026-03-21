# d2-hasher

Multilayer SHA-512 hashing utility for PII columns in CSV/TXT files.

## Installation

```bash
pip install d2-hasher
```

## Quick Start

### Python API

```python
from d2_hasher import hash_columns

# Hash columns in a CSV file
hash_columns(
    input_file="data.csv",
    columns=["national_id", "name"],
    secret_salts=["your_secret_salt_1", "your_secret_salt_2"],
)
# Output written to data_hashed.csv

# Hash a DataFrame in-memory
import pandas as pd
df = pd.read_csv("data.csv")
result = hash_columns(
    df=df,
    columns=["national_id", "name"],
    secret_salts=["your_secret_salt_1", "your_secret_salt_2"],
)
```

### Command Line

```bash
d2-hasher \
  --input-file data.csv \
  --columns national_id name \
  --secret-salts "your_secret_salt_1" "your_secret_salt_2" \
  --output data_hashed.csv \
  --chunksize 50000
```

## `hash_columns()` Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `columns` | `list[str]` | Yes | — | Column names to hash |
| `secret_salts` | `list[str]` | Yes | — | Secret salts applied in order |
| `input_file` | `str` | No* | — | Path to CSV/TXT file |
| `df` | `DataFrame` | No* | — | In-memory DataFrame |
| `output` | `str` | No | `<stem>_hashed.csv` | Output file path |
| `chunksize` | `int` | No | `10000` | Rows per chunk |
| `delimiter` | `str` | No | auto-detect | Column delimiter |

\* At least one of `input_file` or `df` must be provided.

## Algorithm

For each value:

1. Normalize: CID must be exactly 13 consecutive Arabic digits with no hyphens (`-`), spaces, or any special characters
2. For each secret salt: `SHA-512(value + salt)` → 128-char hex string
3. Use the output of one round as input to the next

Null/NaN values are returned as `None` without hashing.

## CLI Reference

```
d2-hasher --input-file FILE --columns COL [COL ...] --secret-salts SALT [SALT ...]
          [--output FILE] [--chunksize N] [--delimiter CHAR]
```

## License

MIT
