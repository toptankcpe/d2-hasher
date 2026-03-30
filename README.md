# d2-hasher

Multilayer SHA-512 hashing and masking utility for PII columns in CSV/TXT files.

## Installation

```bash
pip install d2-hasher
```

## Quick Start

### Python API

**Hash columns:**
```python
from d2_hasher import hash_columns

# Hash columns in a CSV file
hash_columns(
    input_file="data.csv",
    columns=["national_id", "passport"],
    secret_salts=["salt1", "salt2", "salt3"],
)
# Output written to data_hashed.csv

# Hash a DataFrame in-memory
import pandas as pd
df = pd.read_csv("data.csv")
result = hash_columns(
    df=df,
    columns=["national_id", "passport"],
    secret_salts=["salt1", "salt2", "salt3"],
)
```

**Mask columns:**
```python
# Mask sensitive data with ****
result = hash_columns(
    df=df,
    columns=[],  # No hashing
    secret_salts=[],  # Not required when only masking
    mask_columns=["phone", "email", "address"],
    mask_char="*",
    mask_length=4,
)
```

**Combine hash and mask:**
```python
# Hash some columns and mask others
result = hash_columns(
    df=df,
    columns=["national_id"],  # Hash this
    secret_salts=["salt1", "salt2", "salt3"],
    mask_columns=["phone", "email"],  # Mask these
    mask_char="*",
    mask_length=4,
)
```

### Command Line

**Hash columns:**
```bash
d2-hasher \
  --input-file data.csv \
  --columns national_id passport \
  --secret-salts "salt1" "salt2" "salt3" \
  --output data_hashed.csv
```

**Mask columns:**
```bash
d2-hasher \
  --input-file data.csv \
  --mask-columns phone email address \
  --mask-char "*" \
  --mask-length 4 \
  --output data_masked.csv
```

**Combine hash and mask:**
```bash
d2-hasher \
  --input-file data.csv \
  --columns national_id \
  --secret-salts "salt1" "salt2" "salt3" \
  --mask-columns phone email \
  --output data_protected.csv
```

## `hash_columns()` Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `columns` | `list[str]` | No* | `[]` | Column names to hash |
| `secret_salts` | `list[str]` | Conditional** | — | Secret salts applied in order (3 elements) |
| `input_file` | `str` | No*** | — | Path to CSV/TXT file |
| `df` | `DataFrame` | No*** | — | In-memory DataFrame |
| `output` | `str` | No | `<stem>_hashed.csv` | Output file path |
| `chunksize` | `int` | No | `10000` | Rows per chunk |
| `delimiter` | `str` | No | auto-detect | Column delimiter |
| `mask_columns` | `list[str]` | No* | `[]` | Column names to mask |
| `mask_char` | `str` | No | `"*"` | Character for masking |
| `mask_length` | `int` | No | `4` | Number of mask characters |

\* At least one of `columns` or `mask_columns` must be provided.  
\*\* Required (3 elements) when `columns` is not empty.  
\*\*\* At least one of `input_file` or `df` must be provided.

## Algorithm

For each value:

1. Normalize: CID must be exactly 13 consecutive Arabic digits with no hyphens (`-`), spaces, or any special characters
2. For each secret salt: `SHA-512(value + salt)` → 128-char hex string
3. Use the output of one round as input to the next

Null/NaN values are returned as `None` without hashing.

## CLI Reference

```
d2-hasher --input-file FILE 
          [--columns COL [COL ...]] 
          [--secret-salts SALT [SALT ...]]
          [--mask-columns COL [COL ...]]
          [--mask-char CHAR] 
          [--mask-length N]
          [--output FILE] 
          [--chunksize N] 
          [--delimiter CHAR]
```

**Required:**
- `--input-file`: Input CSV/TXT file
- At least one of `--columns` or `--mask-columns`

**Conditional:**
- `--secret-salts`: Required when using `--columns` (must provide 3 salts)

**Optional:**
- `--output`: Output file path (default: `<input>_hashed.csv`)
- `--mask-char`: Character for masking (default: `*`)
- `--mask-length`: Number of mask characters (default: `4`)
- `--chunksize`: Rows per chunk (default: `10000`)
- `--delimiter`: Column delimiter (default: auto-detect)

## License

MIT
