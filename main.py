#!/usr/bin/env python3
"""jarvis-os entry point.

Usage: python3 main.py <command>  (see: python3 main.py --help)
"""

from interfaces.cli import main

if __name__ == "__main__":
    raise SystemExit(main())
