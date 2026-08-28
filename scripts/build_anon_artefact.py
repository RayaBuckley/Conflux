"""Build the anonymous supplementary code artefact for FLMSec submission.

Copies the minimal claim-dependency closure of the source tree, strips
identifying metadata, renames the package, and packages into a zip.

Usage::

    python scripts/build_anon_artefact.py
"""

from __future__ import annotations

import hashlib
import re
import shutil
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / ".local" / "anon-arteffact"

# --- 1. Source modules to include (claim dependency closure) ---
SRC_INCLUDE_DIRS = [
    "src/conflux/__init__.py",
    "src/conflux/py.typed",
    "src/conflux/domain",
    "src/conflux/ites",
    "src/conflux/policy",
    "src/conflux/execution",
    "src/conflux/ports",
    "src/conflux/evaluation",
    "src/conflux/verification",
    "src/conflux/planning",
    "src/conflux/application",
    "src/conflux/adapters/__init__.py",
    "src/conflux/adapters/scenarios.py",
    "src/conflux/adapters/models",
    "src/conflux/adapters/providers",
]

SRC_EXCLUDE_DIRS: list[str] = [
    "src/conflux/adapters/benchmarks",
    "src/conflux/adapters/policy",
    "src/conflux/visualisation",
    "src/conflux/experiments",
    "src/conflux/cli.py",
]

# --- 2. Tests to include ---
TEST_INCLUDE = [
    "tests/conftest.py",
    "tests/test_policy_and_ites.py",
    "tests/test_domain.py",
    "tests/test_sled.py",
    "tests/test_defence_models.py",
    "tests/test_verification_ir.py",
    "tests/test_verification_ir_sets.py",
    "tests/test_self_composition.py",
    "tests/test_delegation_foundation.py",
    "tests/test_confidentiality_levels.py",
    "tests/test_combinatorial.py",
    "tests/test_refinement_conformance.py",
    "tests/test_controller_synthesis.py",
    "tests/test_endorsement.py",
    "tests/test_robust_disclosure.py",
    "tests/test_diagnostics.py",
    "tests/test_records_and_schemas.py",
    "tests/test_refinement_conformance.py",
    "tests/fixtures",
]

# --- 3. Result fixtures cited by the paper ---
RESULT_FIXTURES = [
    "research/output/runs/defence-models-v1",
    "research/output/runs/native-sled-reproduction-v1",
    "research/output/runs/sled-coi-reduction-v1",
    "research/output/runs/z3-agreement-v1",
    "research/output/runs/coi-scaling-v1",
    "research/output/runs/native-sled-partb-reproduction-v1",
    "research/output/runs/direction-readiness-v1",
    "research/output/runs/smoke",
]

# --- 4. Scripts needed for reproduction ---
SCRIPTS_INCLUDE = [
    "scripts/generate_flmsec_tables.py",
    "scripts/__init__.py",
    "scripts/validate_schemas.py",
]

# --- 5. Config files ---
CONFIG_INCLUDE = [
    "schemas",
    "pyproject.toml",
]

# --- Identity patterns to scan for ---
IDENTITY_PATTERNS = [
    r"Raya",
    r"Buckley",
    r"Oxford",
    r"Keble",
    r"RayaBuckley",
    r"conflux",
    r"Conflux",
    r"github\.com",
]

PACKAGE_NAME = "pe_ites"


def _clean_dir(path: Path) -> None:
    if path.exists():
        shutil.rmtree(path)
    path.mkdir(parents=True)


def _copy_file(src: Path, dst: Path) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)


def _copy_dir(src: Path, dst: Path, exclude_names: set[str] | None = None) -> None:
    exclude_names = exclude_names or set()
    for item in src.rglob("*"):
        if item.is_file():
            rel = item.relative_to(src)
            if any(part in exclude_names for part in rel.parts):
                continue
            dst_file = dst / rel
            dst_file.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(item, dst_file)


def _rename_package(content: str) -> str:
    """Mechanically rename conflux -> pe_ites in source content."""
    return content.replace("conflux", PACKAGE_NAME)


def _anonymise_file(path: Path) -> list[str]:
    """Apply anonymisation transforms to a file. Returns list of findings."""
    findings: list[str] = []
    try:
        text = path.read_text(encoding="utf-8")
    except (UnicodeDecodeError, OSError):
        return findings

    original = text

    # Rename package
    text = _rename_package(text)

    # Check for identity patterns (after rename, 'conflux' is gone)
    for pattern in IDENTITY_PATTERNS:
        if pattern.lower() == r"conflux":
            continue  # already replaced
        matches = re.findall(pattern, text, re.IGNORECASE)
        for m in matches:
            findings.append(f"  {path}: found '{m}'")

    if text != original:
        path.write_text(text, encoding="utf-8")

    return findings


def build() -> None:
    artefact = OUT / "flmsec-anonymous-artefact"
    _clean_dir(artefact)

    all_findings: list[str] = []

    # Copy source
    src_dst = artefact / "src" / PACKAGE_NAME
    for item in SRC_INCLUDE_DIRS:
        src_path = ROOT / item
        if not src_path.exists():
            print(f"  SKIP (missing): {item}")
            continue
        # Preserve the path relative to src/conflux/
        rel = src_path.relative_to(ROOT / "src" / "conflux")
        dst_path = src_dst / rel
        if src_path.is_dir():
            _copy_dir(src_path, dst_path)
        else:
            _copy_file(src_path, dst_path)

    # Copy tests
    tests_dst = artefact / "tests"
    for item in TEST_INCLUDE:
        src_path = ROOT / item
        if not src_path.exists():
            print(f"  SKIP (missing): {item}")
            continue
        if src_path.is_dir():
            _copy_dir(src_path, tests_dst / src_path.name)
        else:
            _copy_file(src_path, tests_dst / src_path.name)

    # Copy result fixtures
    results_dst = artefact / "results"
    for item in RESULT_FIXTURES:
        src_path = ROOT / item
        if not src_path.exists():
            print(f"  SKIP (missing): {item}")
            continue
        rel = src_path.relative_to(ROOT / "research" / "output" / "runs")
        _copy_dir(src_path, results_dst / rel)

    # Copy scripts
    scripts_dst = artefact / "scripts"
    for item in SCRIPTS_INCLUDE:
        src_path = ROOT / item
        if not src_path.exists():
            print(f"  SKIP (missing): {item}")
            continue
        _copy_file(src_path, scripts_dst / src_path.name)

    # Copy schemas
    schemas_dst = artefact / "schemas"
    _copy_dir(ROOT / "schemas", schemas_dst)

    # Copy and anonymise pyproject.toml
    pyproject_src = ROOT / "pyproject.toml"
    pyproject_dst = artefact / "pyproject.toml"
    if pyproject_src.exists():
        text = pyproject_src.read_text(encoding="utf-8")
        # Remove author, rename package, strip description
        text = re.sub(r'name = "conflux"', f'name = "{PACKAGE_NAME}"', text)
        text = re.sub(r"authors = \[.*?\]", "authors = []", text, flags=re.DOTALL)
        text = re.sub(r'description = ".*?"', 'description = "Anonymous supplementary artefact."', text)
        text = re.sub(r"keywords = \[.*?\]", "keywords = []", text, flags=re.DOTALL)
        text = text.replace("conflux", PACKAGE_NAME)
        pyproject_dst.write_text(text, encoding="utf-8")

    # Anonymise all .py files
    for py_file in artefact.rglob("*.py"):
        findings = _anonymise_file(py_file)
        all_findings.extend(findings)

    # Write README
    readme = artefact / "README.md"
    readme.write_text(
        "# Anonymous Supplementary Code Artefact\n\n"
        "This artefact accompanies an anonymous FLMSec 2026 submission.\n"
        "It contains the minimal source code, tests, and result fixtures\n"
        "needed to reproduce the paper's claims.\n\n"
        "## Setup\n\n"
        "```bash\n"
        "pip install -e .\n"
        "```\n\n"
        "## Reproduce Paper Results\n\n"
        "```bash\n"
        "# Run core tests\n"
        "python -m pytest tests/ -q\n\n"
        "# Regenerate evidence tables\n"
        "python scripts/generate_flmsec_tables.py\n"
        "```\n",
        encoding="utf-8",
    )

    # Write ANONYMISATION_AUDIT.md
    audit = artefact / "ANONYMISATION_AUDIT.md"
    audit_lines = [
        "# Anonymisation Audit\n\n",
        "## Identity scan patterns\n\n",
        "- Raya / Buckley / Oxford / Keble / RayaBuckley / conflux / Conflux / github.com URLs\n\n",
        "## Findings\n\n",
    ]
    if all_findings:
        audit_lines.append("The following identity strings were found and replaced:\n\n")
        audit_lines.extend(f"- {f}\n" for f in all_findings)
    else:
        audit_lines.append("No identity strings found after package rename.\n\n")
    audit_lines.append("\n## Package rename\n\n")
    audit_lines.append(f"- `conflux` -> `{PACKAGE_NAME}` (mechanical replacement in all .py and .toml files)\n")
    audit_lines.append("- Author metadata stripped from pyproject.toml\n")
    audit_lines.append("- No git history included\n")
    audit.write_text("".join(audit_lines), encoding="utf-8")

    # Zip
    zip_path = OUT / "flmsec-anonymous-artefact.zip"
    if zip_path.exists():
        zip_path.unlink()
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for file in artefact.rglob("*"):
            if file.is_file():
                zf.write(file, file.relative_to(artefact))

    # SHA-256
    sha = hashlib.sha256(zip_path.read_bytes()).hexdigest()
    print(f"\nArtefact: {zip_path}")
    print(f"SHA-256:  {sha}")
    print(f"Files:    {sum(1 for _ in artefact.rglob('*') if _.is_file())}")
    if all_findings:
        print(f"\nIdentity findings ({len(all_findings)}):")
        for f in all_findings:
            print(f"  {f}")
    else:
        print("\nNo identity findings.")


if __name__ == "__main__":
    build()
