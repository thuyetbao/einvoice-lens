#!/bin/python3

# Global
import pprint
import argparse
import textwrap

# Internal
from einvoice_lens.engine import parse_commerical_invoice


if __name__ == "__main__":

    # Handlers
    parser = argparse.ArgumentParser(
        prog="python -m einvoice_lens.cli",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description=textwrap.dedent("""
        [Einvoice Lens] CLI

        Usage
        -----

        Base case
        >>> python -m einvoice_lens.cli --path <document-path>

        Help
        >>> python -m einvoice_lens.cli --help
        """),
        epilog="Copyright (c) of Thuyet Bao"
    )
    parser.add_argument("--path", help="Path to the PDF file", type=str)
    parameters = parser.parse_args()

    # Parse
    result = parse_commerical_invoice(parameters.path)
    pprint.pp(result, depth=4)
