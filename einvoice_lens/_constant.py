#!/bin/python3


# The map of characters to replace
DEFAULT_MAPPING_CHARACTERS = {
    # Hyphens / Dashes
    "\u2010": "-",     # Hyphen
    "\u2011": "-",     # Non-breaking hyphen
    "\u2012": "-",     # Figure dash
    "\u2013": "-",     # En dash
    "\u2014": "-",     # Em dash
    "\u2212": "-",     # Minus sign
    "\u00ad": "",      # Soft hyphen (remove!)
    # Spaces
    "\u00a0": " ",     # No-break space
    "\u2000": " ",     # En quad
    "\u2001": " ",     # Em quad
    "\u2002": " ",     # En space
    "\u2003": " ",     # Em space
    "\u2004": " ",     # Three-per-em space
    "\u2005": " ",     # Four-per-em space
    "\u2006": " ",     # Six-per-em space
    "\u2007": " ",     # Figure space
    "\u2008": " ",     # Punctuation space
    "\u2009": " ",     # Thin space
    "\u200a": " ",     # Hair space

    # Zero width / invisible
    "\u200b": "",      # Zero-width space
    "\u200c": "",      # ZWNJ
    "\u200d": "",      # ZWJ
    "\u2060": "",      # Word joiner

    # Bullets / weird symbols
    "\u2022": "*",     # Bullet •
    "\uf0b7": "*",     # Private use bullet
    "\uf0d8": "*",     # Private use bullet
    "\uf0e0": "*",     # Private use bullet
    "\u25cf": "*",     # Black circle ●
    "\u25a0": "*",     # Solid square ■

    # Quotes normalization
    "\u201c": '"',
    "\u201d": '"',
    "\u2018": "'",
    "\u2019": "'",

    # Vietnamese common fixes
    "\u00f0": "đ",     # ð  → đ
    "\u00d0": "Đ",     # Ð  → Đ
}
