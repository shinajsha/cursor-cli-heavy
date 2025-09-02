#!/usr/bin/env python3
"""
main.py - Cursor CLI Heavy Research System
Parallel research orchestration
"""

import argparse
import sys

from ccheavy import CCHeavy, Fore, Style


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Cursor CLI Heavy Research System - Parallel research orchestration"
    )

    parser.add_argument("query", nargs="?", help="Research query")
    parser.add_argument(
        "-f",
        "--format",
        choices=["markdown", "text"],
        default="markdown",
        help="Output format (default: markdown)",
    )
    parser.add_argument(
        "-w", "--workdir", help="Working directory to analyze (absolute path)"
    )
    parser.add_argument(
        "--no-prompt",
        action="store_true",
        help="Skip confirmation prompt and run immediately",
    )

    args = parser.parse_args()

    try:
        ccheavy = CCHeavy()
        ccheavy.run(args)
    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}Cancelled by user.{Style.RESET_ALL}")
        sys.exit(1)
    except Exception as e:
        print(f"{Fore.RED}Error: {e}{Style.RESET_ALL}")
        sys.exit(1)


if __name__ == "__main__":
    main()
