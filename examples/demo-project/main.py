"""Entry point of the demo project."""

import sys

from core.engine import run


def main() -> None:
    if len(sys.argv) > 1:
        print("arg mode")
    run()


if __name__ == "__main__":
    main()
