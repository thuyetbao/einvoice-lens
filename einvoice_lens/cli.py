#!/bin/python3

# Internal
import argparse
from einvoice_lens.engine import parse_commerical_invoice


if __name__ == "__main__":

    # Handlers
    parser = argparse.ArgumentParser(description="Einvoice Lens CLI")
    parser.add_argument("path", help="Path to the PDF file", type=str)
    args = parser.parse_args()

    # Parse
    result = parse_commerical_invoice(args.path)
    print(result)
