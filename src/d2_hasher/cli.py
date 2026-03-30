import argparse
import sys

from .hasher import hash_columns


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="d2-hasher",
        description=(
            "Hash PII columns in a CSV/TXT file using Multilayer SHA-512 hashing."
        ),
    )
    parser.add_argument(
        "--input-file",
        required=True,
        metavar="FILE",
        help="Path to the delimiter-separated input file (CSV or TXT).",
    )
    parser.add_argument(
        "--columns",
        required=True,
        nargs="+",
        metavar="COL",
        help="One or more column names to hash.",
    )
    parser.add_argument(
        "--secret-salts",
        required=True,
        nargs="+",
        metavar="SALT",
        help="One or more secret salts applied in order.",
    )
    parser.add_argument(
        "--output",
        default=None,
        metavar="FILE",
        help=(
            "Output file path. Defaults to <input_stem>_hashed.csv "
            "in the same directory as the input file."
        ),
    )
    parser.add_argument(
        "--chunksize",
        type=int,
        default=10_000,
        metavar="N",
        help="Number of rows to process per chunk (default: 10000).",
    )
    parser.add_argument(
        "--delimiter",
        default=None,
        metavar="CHAR",
        help=(
            "Column delimiter for the input file. "
            "Auto-detected from the file when not specified."
        ),
    )
    parser.add_argument(
        "--mask-columns",
        default=None,
        nargs="+",
        metavar="COL",
        help="One or more column names to mask with **** instead of hashing.",
    )
    parser.add_argument(
        "--mask-char",
        default="*",
        metavar="CHAR",
        help="Character to use for masking (default: *).",
    )
    parser.add_argument(
        "--mask-length",
        type=int,
        default=4,
        metavar="N",
        help="Number of masking characters (default: 4).",
    )

    args = parser.parse_args()

    try:
        hash_columns(
            columns=args.columns,
            secret_salts=args.secret_salts,
            input_file=args.input_file,
            output=args.output,
            chunksize=args.chunksize,
            delimiter=args.delimiter,
            mask_columns=args.mask_columns,
            mask_char=args.mask_char,
            mask_length=args.mask_length,
        )
    except (ValueError, FileNotFoundError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)

    output_path = args.output
    if output_path is None:
        from pathlib import Path
        p = Path(args.input_file)
        output_path = str(p.parent / f"{p.stem}_hashed.csv")

    print(f"Done. Output written to: {output_path}")


if __name__ == "__main__":
    main()
