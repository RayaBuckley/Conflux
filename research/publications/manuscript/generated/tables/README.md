# Generated tables

Files in this directory are produced by `scripts/generate_fourth_year_tables.py`
from versioned result JSON. Hand-written headline numbers are prohibited.
The standard validation tier runs that generator with `--check`, so a table that
no longer matches the retained bundles fails the gate. The manuscript in
`../../conflux_fourth_year_2026.tex` inputs both files, and
`tests/test_manuscript_references.py` checks that every `\ref` in the
manuscript resolves to a label in the manuscript or in a file it inputs, so a
cited table cannot stay unreachable.
