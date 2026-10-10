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

ALLOWED_FILE_NAME = re.compile(r"^[A-Za-z0-9_+\-.,=]+$")
ABSTRACT_LIMIT = 1920


def name_problems(paths: list[Path], root: Path) -> list[str]:
    """arXiv accepts only a-z A-Z 0-9 _ + - . , = inside a file name."""
    problems = []
    for path in paths:
        relative = path.relative_to(root)
        for segment in relative.parts:
            if not ALLOWED_FILE_NAME.match(segment):
                problems.append(f"{relative.as_posix()}: arXiv rejects the file-name segment {segment!r}")
    return problems


def case_mismatch(name: str, actual: str, suffixes: tuple[str, ...]) -> bool:
    """True when a reference does not name the resolved file exactly."""
    if actual == name:
        return False
    extension_added = Path(name).suffix == "" and Path(actual).suffix in suffixes
    return not (extension_added and Path(actual).with_suffix("").as_posix() == name)


def reference_case_problems(manuscript: Path, root: Path) -> list[str]:
    """Every reference must name the shipped file exactly, case included.

    arXiv's file system is case sensitive and mismatched figure paths are a
    listed common failure, so the check compares strings instead of trusting
    the local file system to notice.
    """
    problems: list[str] = []
    pending = [manuscript]
    seen = {manuscript}
    while pending:
        current = pending.pop()
        text = source_text(current)
        references = [
            *((target, (".tex",)) for target in INPUT.findall(text)),
            *((target, (".bib",)) for target in BIBLIOGRAPHY.findall(text)),
            *((target, GRAPHICS_SUFFIXES) for target in GRAPHICS.findall(text)),
        ]
        for target, suffixes in references:
            for entry in target.split(","):
                name = entry.strip()
                resolved = next(
                    (item for item in _candidates(current.parent, name, suffixes) if item.is_file()),
                    None,
                )
                if resolved is None:
                    continue  # dependency_paths already reports the missing file
                if resolved not in seen:
                    seen.add(resolved)
                    pending.append(resolved)
                actual = resolved.relative_to(current.parent).as_posix()
                if case_mismatch(name, actual, suffixes):
                    problems.append(
                        f"{current.name}: reference {name!r} resolves to {actual!r}; names are case sensitive",
                    )
    return problems


def metadata_strings(manuscript: Path) -> tuple[str, str]:
    """Return the title and abstract text the submission form asks for."""
    text = manuscript.read_text(encoding="utf-8")
    marker = "\\title{"
    start = text.find(marker)
    if start < 0:
        raise ValueError(f"{manuscript.name}: no \\title{{...}} found")
    depth = 0
    end = -1
    for index in range(start + len(marker) - 1, len(text)):
        if text[index] == "{":
            depth += 1
        elif text[index] == "}":
            depth -= 1
            if depth == 0:
                end = index
                break
    if end < 0:
        raise ValueError(f"{manuscript.name}: unbalanced \\title{{...}}")
    raw_title = text[start + len(marker) : end]
    title = plain_text(raw_title.split("\\\\")[0])
    if "\\begin{abstract}" not in text or "\\end{abstract}" not in text:
        raise ValueError(f"{manuscript.name}: no abstract environment found")
    raw_abstract = text.split("\\begin{abstract}", 1)[1].split("\\end{abstract}", 1)[0]
    return title, plain_text(raw_abstract)


def plain_text(text: str) -> str:
    """Strip LaTeX markup, keeping the words a metadata field needs."""
    body = COMMENT.sub("", text)
    body = re.sub(r"\\[a-zA-Z]+\*?(?:\[[^\]]*\])?", " ", body)
    body = body.replace("{", " ").replace("}", " ").replace("~", " ")
    body = re.sub(r"\s+", " ", body)
    return body.strip()


def metadata_problems(manuscript: Path) -> list[str]:
    """The submission form needs ASCII metadata and refuses a 1921-character abstract."""
    try:
        title, abstract = metadata_strings(manuscript)
    except ValueError as error:
        return [str(error)]
    problems = []
    for field, value in (("title", title), ("abstract", abstract)):
        if not value.isascii():
            problems.append(f"the {field} metadata must be ASCII for the submission form")
    if len(abstract) > ABSTRACT_LIMIT:
        problems.append(
            f"the abstract metadata is {len(abstract)} characters; arXiv refuses more than {ABSTRACT_LIMIT}",
        )
    return problems


def manifest_for(manuscript: Path, root: Path) -> tuple[Manifest, list[str]]:
    """Build the manifest: the ship set keyed by its path below the archive root."""
    paths, problems = dependency_paths(manuscript, root)
    problems.extend(name_problems(paths, root))
    problems.extend(reference_case_problems(manuscript, root))
    problems.extend(metadata_problems(manuscript))
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
    parser.add_argument(
        "--metadata",
        action="store_true",
        help="print the title and abstract the submission form wants",
    )
    parser.add_argument("--write", action="store_true", help="rewrite the tracked manifest from the tree")
    parser.add_argument("--out", default=str(OUT), help="directory for the staged tree and archive")
    args = parser.parse_args(argv)

    if args.metadata:
        title, abstract = metadata_strings(MANUSCRIPT)
        print(f"[arxiv-bundle] title ({len(title)} characters)\n{title}\n")
        print(f"[arxiv-bundle] abstract ({len(abstract)} characters)\n{abstract}")
        return 0

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
