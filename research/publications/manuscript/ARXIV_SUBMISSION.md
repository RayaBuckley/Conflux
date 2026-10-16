# arXiv submission checklist

Every rule below was read live on 2026-10-10 from
<https://info.arxiv.org/help/submit_tex.html>,
<https://info.arxiv.org/help/submit/index.html> and
<https://info.arxiv.org/help/prep.html>.

## What this repository enforces

`scripts/build_arxiv_bundle.py --check` is a standard-tier step and fails when:

- a shipped file name contains anything outside `a-z A-Z 0-9 _ + - . , =`, the
  only characters arXiv accepts;
- a reference resolves to a file whose name differs in case, because arXiv's
  file system is case sensitive and mismatched figure paths are a listed common
  failure;
- the metadata is not ASCII, because the submission form accepts ASCII only;
- the abstract runs past 1920 characters, where arXiv refuses it.

`--metadata` prints the exact title and abstract the form wants: the title
without its typeset subtitle line, the abstract without its LaTeX markup. Both
strings come from the manuscript itself, so the form cannot drift from the
paper. It fails, printing the same problem list as `--check`, when either field
cannot be submitted as it stands.

`python scripts/build_arxiv_bundle.py` writes a deterministic `.tar.gz` below
`.local/arxiv-bundle/`, containing exactly the files listed in
`ARXIV_BUNDLE.json`. The archive root is this directory, because arXiv compiles
a submission from its root, and `\input{generated/tables/...}` has to resolve
from there.

## Owner-only steps

- The submission comes from a registered author. arXiv expects authors to
  self-submit, and a first submission to a category may need an endorsement
  from an existing endorser in that category.
- The author grants arXiv an irrevocable licence to distribute the work, and
  accepts the Submittal Agreement, the code of conduct, the moderation policy
  and the privacy policy.
- Choose the primary category and any cross-lists. The likely pair here is
  `cs.CR` for the security kernel with `cs.AI` or `cs.CL` cross-listed for the
  agent evaluation, but this is the owner's judgement, not the script's.
- The `ACM-class` field serves cs archives; fill it only if the paper is
  classified that way. `Journal-ref` and `DOI` stay empty until a venue
  publishes the work.
- Decide whether the venue currently reviewing the FLMSec paper permits an
  arXiv posting.

## Limits of the local check

This host has no TeX distribution (`pdflatex`, `latexmk` and `tectonic` are all
absent), so the bundle is checked for completeness, for arXiv's file-name and
case rules and for the metadata limits, but it is never compiled here. No
`.bbl` is pre-generated: arXiv runs `bibtex` on the shipped `references.bib`.
A failure that only a TeX run can reveal, such as a package missing from
arXiv's TeX Live, cannot be caught on this host.
