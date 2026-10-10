"""Prepare the current manuscript's arXiv source bundle.

arXiv compiles a submission from the root of the submission directory, so the
bundle is staged with the manuscript directory as its root and every file the
manuscript inputs is resolved before anything is packaged. The tracked manifest
records the shipped files and their digests; a stale manifest or a missing
dependency stops the build instead of producing a bundle that cannot compile.

This host has no TeX distribution, so the bundle is checked for completeness and
consistency rather than by compiling it. The rules encoded here were read from
https://info.arxiv.org/help/submit_tex.html on 2026-10-10:

* a collection of TeX input files may be packaged in a `.tar` or `.zip` archive;
* compilation always runs from the root of the submission directory, even when
  the main file sits in a subdirectory;
* `.bib` or `.bbl` files must be included when BibTeX is used (arXiv runs
  `bibtex`), and auxiliary or output files are removed automatically;
* no on-the-fly figure conversion and no embedded JavaScript is permitted.

Usage::

    python scripts/build_arxiv_bundle.py --check
    python scripts/build_arxiv_bundle.py --write
    python scripts/build_arxiv_bundle.py
"""

from __future__ import annotations

import argparse
import gzip
import hashlib
import io
import json
import re
import shutil
import sys
import tarfile
from pathlib import Path
from typing import TypedDict, cast

ROOT = Path(__file__).resolve().parents[1]
MANUSCRIPT = ROOT / "research" / "publications" / "manuscript" / "conflux_fourth_year_2026.tex"
MANIFEST = ROOT / "research" / "publications" / "manuscript" / "ARXIV_BUNDLE.json"
OUT = ROOT / ".local" / "arxiv-bundle"

INPUT = re.compile(r"\\(?:input|include)\{([^}]+)\}")
BIBLIOGRAPHY = re.compile(r"\\bibliography\{([^}]+)\}")
GRAPHICS = re.compile(r"\\includegraphics(?:\[[^\]]*\])?\{([^}]+)\}")
COMMENT = re.compile(r"(?<!\\)%.*")
GRAPHICS_SUFFIXES = (".pdf", ".png", ".jpg", ".jpeg", ".eps", ".ps")


class ManifestFile(TypedDict):
    """One shipped file, keyed by its path below the archive root."""

    path: str
    bytes: int
    sha256: str


class Manifest(TypedDict):
    """The tracked record of what an arXiv submission would carry."""

    schema: str
    manuscript: str
    archive_root: str
    source: str
    notes: list[str]
    files: list[ManifestFile]


def source_text(path: Path) -> str:
    """Return the file with LaTeX comments removed, line by line."""
    return "\n".join(COMMENT.sub("", line) for line in path.read_text(encoding="utf-8").splitlines())


def _candidates(base: Path, target: str, suffixes: tuple[str, ...]) -> list[Path]:
    plain = base / target
    return [plain, *(plain.with_name(plain.name + suffix) for suffix in suffixes)]


def dependency_paths(manuscript: Path, root: Path) -> tuple[list[Path], list[str]]:
    """Resolve every file the manuscript inputs, reporting anything missing."""
    found: list[Path] = [manuscript]
    problems: list[str] = []
    pending: list[Path] = [manuscript]
    seen: set[Path] = {manuscript}
    while pending:
        current = pending.pop()
        text = source_text(current)
        for target in INPUT.findall(text):
            resolved = next((item for item in _candidates(current.parent, target, (".tex",)) if item.is_file()), None)
            if resolved is None:
                problems.append(f"{current.name}: input target not found: {target}")
                continue
            if resolved not in seen:
                seen.add(resolved)
                found.append(resolved)
                pending.append(resolved)
        for target in BIBLIOGRAPHY.findall(text):
            for entry in target.split(","):
                name = entry.strip()
                resolved = next(
                    (item for item in _candidates(current.parent, name, (".bib",)) if item.is_file()),
                    None,
                )
                if resolved is None:
                    problems.append(f"{current.name}: bibliography not found: {name}")
                elif resolved not in seen:
                    seen.add(resolved)
                    found.append(resolved)
        for target in GRAPHICS.findall(text):
            resolved = next(
                (item for item in _candidates(current.parent, target, GRAPHICS_SUFFIXES) if item.is_file()),
                None,
            )
            if resolved is None:
                problems.append(f"{current.name}: figure not found: {target}")
            elif resolved not in seen:
                seen.add(resolved)
                found.append(resolved)
    return found, problems


def _digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def manifest_for(manuscript: Path, root: Path) -> tuple[Manifest, list[str]]:
    """Build the manifest: the ship set keyed by its path below the archive root."""
    paths, problems = dependency_paths(manuscript, root)
    archive_root = manuscript.parent
    files: list[ManifestFile] = []
    for path in sorted(paths, key=str):
        try:
            relative = path.relative_to(archive_root).as_posix()
        except ValueError:
            problems.append(f"{path} is outside the manuscript directory")
            continue
        files.append({"path": relative, "bytes": path.stat().st_size, "sha256": _digest(path)})
    manifest: Manifest = {
        "schema": "conflux-arxiv-bundle/1",
        "manuscript": manuscript.relative_to(root).as_posix(),
        "archive_root": archive_root.relative_to(root).as_posix(),
        "source": "https://info.arxiv.org/help/submit_tex.html (read 2026-10-10)",
        "notes": [
            "arXiv compiles from the root of the submission directory, so this tree is the archive root.",
            "The manifest digest of every shipped file is checked before packaging.",
        ],
        "files": files,
    }
    return manifest, problems


def manifest_problems(manifest_path: Path = MANIFEST, manuscript: Path = MANUSCRIPT, root: Path = ROOT) -> list[str]:
    """Compare the tracked manifest with the current tree."""
    if not manifest_path.is_file():
        return [f"{manifest_path.name} is missing; run with --write"]
    stored = cast(Manifest, json.loads(manifest_path.read_text(encoding="utf-8")))
    current, problems = manifest_for(manuscript, root)
    if stored != current:
        stored_files = {item["path"]: item["sha256"] for item in stored.get("files", [])}
        current_files = {item["path"]: item["sha256"] for item in current["files"]}
        for path in sorted(current_files.keys() - stored_files.keys()):
            problems.append(f"{path} is not in the manifest")
        for path in sorted(stored_files.keys() - current_files.keys()):
            problems.append(f"{path} is in the manifest but no longer ships")
        for path in sorted(current_files.keys() & stored_files.keys()):
            if current_files[path] != stored_files[path]:
                problems.append(f"{path} changed since the manifest was written")
        if not problems:
            problems.append("the manifest records different metadata")
    return problems


def build(manifest_path: Path = MANIFEST, manuscript: Path = MANUSCRIPT, root: Path = ROOT, out: Path = OUT) -> tuple[Path, list[str]]:
    """Package the manifest's files into a deterministic .tar.gz below `out`."""
    problems = manifest_problems(manifest_path, manuscript, root)
    if problems:
        return out, problems
    manifest = cast(Manifest, json.loads(manifest_path.read_text(encoding="utf-8")))
    staging = out / Path(manifest["manuscript"]).stem
    if staging.exists():
        shutil.rmtree(staging)
    archive_root = root / manifest["archive_root"]
    for item in manifest["files"]:
        destination = staging / item["path"]
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(archive_root / item["path"], destination)
    archive = out / f"{staging.name}-arxiv.tar.gz"
    archive.parent.mkdir(parents=True, exist_ok=True)
    buffer = io.BytesIO()
    with tarfile.open(fileobj=buffer, mode="w") as tar:
        for item in manifest["files"]:
            path = staging / item["path"]
            info = tar.gettarinfo(str(path), arcname=item["path"])
            info.mtime = 0
            info.uid = info.gid = 0
            info.uname = info.gname = ""
            with path.open("rb") as handle:
                tar.addfile(info, handle)
    with gzip.GzipFile(filename="", mode="wb", fileobj=archive.open("wb"), mtime=0) as compressed:
        compressed.write(buffer.getvalue())
    return archive, problems


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="verify the manifest against the tree and write nothing")
    parser.add_argument("--write", action="store_true", help="rewrite the tracked manifest from the tree")
    parser.add_argument("--out", default=str(OUT), help="directory for the staged tree and archive")
    args = parser.parse_args(argv)

    current, problems = manifest_for(MANUSCRIPT, ROOT)
    if problems:
        for problem in problems:
            print(f"[arxiv-bundle] {problem}")
        print("[arxiv-bundle] refusing to package a bundle with missing dependencies")
        return 1
    if args.write:
        MANIFEST.write_text(json.dumps(current, indent=2) + "\n", encoding="utf-8")
        print(f"[arxiv-bundle] wrote {MANIFEST.relative_to(ROOT)} with {len(current['files'])} files")
        return 0
    if args.check:
        problems = manifest_problems()
        for problem in problems:
            print(f"[arxiv-bundle] {problem}")
        if problems:
            print("[arxiv-bundle] the manifest is stale; run with --write")
            return 1
        print(f"[arxiv-bundle] manifest current: {len(current['files'])} files ship from {current['archive_root']}")
        return 0
    archive, problems = build(out=Path(args.out))
    for problem in problems:
        print(f"[arxiv-bundle] {problem}")
    if problems:
        return 1
    print(f"[arxiv-bundle] packaged {archive} ({archive.stat().st_size} bytes)")
    for item in current["files"]:
        print(f"[arxiv-bundle]   {item['path']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
