#!/bin/python3

# Global
import os
import pprint
import argparse
import textwrap
import json

# Internal
from einvoice_lens.engine import parse_commerical_invoice


if __name__ == "__main__":

    parser = argparse.ArgumentParser(
        prog="python -m einvoice_lens.cli",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description=textwrap.dedent("""
        [Einvoice Lens] Parse an e-invoice into structured output

        Usage
        -----

        Base case
        >>> python -m einvoice_lens.cli --path <document-path>

        Output to file
        >>> python -m einvoice_lens.cli --path <document-path> --output <output-path>

        Help
        >>> python -m einvoice_lens.cli --help
        """),
        epilog="Copyright (c) of Thuyet Bao"
    )
    parser.add_argument("--path", help="Path to the PDF file", type=str, required=True)
    parser.add_argument("--output", help="Path to the output file", type=str, default=None)
    parameters = parser.parse_args()

    # Parse
    result = parse_commerical_invoice(parameters.path)
    pprint.pp(result, depth=4)

    # Output
    if parameters.output is not None:
        with open(
            file=os.path.join(parameters.output, f"{result['runtime_metadata']['checksum_crc32c']}.json"),
            mode="w",
            encoding="utf-8"
        ) as _file:
            json.dump(result, _file, indent=4, default=str, ensure_ascii=False)
