"""Generate API documentation from typed docstrings using pdoc."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate API documentation.")
    parser.add_argument(
        "--output",
        default="docs/api",
        help="Output directory for generated documentation.",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Verify that pdoc can import and render the package without errors.",
    )
    arguments = parser.parse_args()

    try:
        import pdoc  # noqa: F401
    except ImportError:
        print(
            "pdoc is not installed. Install with: pip install -e '.[docs]'",
            file=sys.stderr,
        )
        return 2

    if arguments.check:
        result = subprocess.run(
            [sys.executable, "-m", "pdoc", "--no-config", "conflux", "-o", str(arguments.output)],
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            print(result.stderr, file=sys.stderr)
            return result.returncode
        print("API documentation built successfully.")
        return 0

    output = Path(arguments.output)
    output.mkdir(parents=True, exist_ok=True)
    result = subprocess.run(
        [sys.executable, "-m", "pdoc", "--no-config", "conflux", "-o", str(output)],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        return result.returncode
    print(f"API documentation written to {output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
