# Reproducibility

> Migration notice: current reproducibility guidance is in
> [EVALUATION.md](EVALUATION.md) and [DEVELOPMENT.md](DEVELOPMENT.md).

Conflux targets Python 3.12 or newer. Create the repository-local `.venv` and
install the package with development dependencies using:

```powershell
.\scripts\setup.ps1
```

Before experiments, run the complete validation workflow:

```powershell
.\scripts\validate.ps1
```

For direct, non-activated execution, use
`.\.venv\Scripts\python.exe -m <tool>`. Rerunning the setup script refreshes
the editable installation and dependencies. The `.venv/` directory is ignored
and must not be committed.

Experiments should record the scenario, attack, defence, model configuration,
provider configuration, random seed, and produced trace/metrics. Generated
experiment data belongs outside version control unless it is an intentional
paper artefact.

The paper source is in `paper/`. Build it with the repository's LaTeX source
and required `.sty`/`.bst` files. Commit the source, diagrams, bibliography,
and final PDF; LaTeX intermediates are ignored by `.gitignore`.
