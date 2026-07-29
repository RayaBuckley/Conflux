"""Generate or deterministically check the curated M3 smoke bundle."""

from __future__ import annotations

import argparse
import sys
import tempfile
from pathlib import Path

from conflux.experiments import BUNDLE_FILES, generate_smoke_bundle, load_manifest


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("manifest", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--check", action="store_true")
    arguments = parser.parse_args()
    manifest = load_manifest(arguments.manifest)
    if not arguments.check:
        generate_smoke_bundle(manifest, arguments.output)
        print(f"Generated smoke bundle: {arguments.output}")
        return 0
    with tempfile.TemporaryDirectory(prefix="conflux-smoke-") as temporary:
        regenerated = Path(temporary)
        generate_smoke_bundle(manifest, regenerated)
        names = (*BUNDLE_FILES, "checksums.sha256")
        changed = [
            name
            for name in names
            if not (arguments.output / name).is_file()
            or (arguments.output / name).read_bytes()
            != (regenerated / name).read_bytes()
        ]
    if changed:
        print(f"Smoke evidence is stale: {', '.join(changed)}", file=sys.stderr)
        return 1
    print("Smoke evidence regeneration check passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
