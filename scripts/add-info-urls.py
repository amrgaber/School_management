#!/usr/bin/env python3
"""
Script to add "More info" URLs to pylint-odoo output
"""

import re
import sys

# Mapping of pylint-odoo message codes to their info URLs
INFO_URLS = {
    "W8161": "https://github.com/odoo/odoo/pull/174844",
    "W8301": "https://github.com/odoo/odoo/pull/174844",
    "W8113": "https://github.com/OCA/odoo-community.org/blob/master/website/Contribution/CONTRIBUTING.rst",
    "W8120": "https://github.com/OCA/odoo-community.org/blob/master/website/Contribution/CONTRIBUTING.rst",
    "C8101": "https://github.com/OCA/maintainer-tools",
    "E0602": "https://docs.python.org/3/tutorial/errors.html",
    "E1101": "https://pylint.pycqa.org/en/latest/user_guide/messages/error/no-member.html",
    "W0611": "https://pylint.pycqa.org/en/latest/user_guide/messages/warning/unused-import.html",
    "W0612": "https://pylint.pycqa.org/en/latest/user_guide/messages/warning/unused-variable.html",
    "W0107": "https://pylint.pycqa.org/en/latest/user_guide/messages/warning/unnecessary-pass.html",
    "R1705": "https://pylint.pycqa.org/en/latest/user_guide/messages/refactor/no-else-return.html",
}


def add_info_urls(line):
    """Add info URLs to pylint output lines"""
    # Pattern to match pylint messages with codes
    pattern = r"\[([A-Z]\d+)\("
    match = re.search(pattern, line)

    if match:
        code = match.group(1)
        if code in INFO_URLS:
            # Add the URL after the message, preserving newline
            return line.rstrip() + f" More info at {INFO_URLS[code]}\n"

    return line


def main():
    """Process stdin and add info URLs"""
    for line in sys.stdin:
        print(add_info_urls(line), end="")


if __name__ == "__main__":
    main()
