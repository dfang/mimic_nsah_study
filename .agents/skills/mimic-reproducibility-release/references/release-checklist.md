# Reproducibility release checklist

## Source and environment

- MIMIC and linked dataset versions are explicit.
- Derived concepts identify their source release or commit.
- Git commit and dirty-worktree status are recorded.
- Python/R/system dependencies are exactly locked.
- External services and SQL dialects are identified.
- Required environment variables are named without exposing values.

## Determinism and execution

- Seeds cover all stochastic stages.
- Nondeterministic behavior is documented.
- Pipeline DAG contains every reported result path.
- Notebooks run from a clean kernel in order.
- Python and R checks pass or failures are recorded.
- SQL syntax/dry-run and row-grain checks are recorded.

## Provenance

- SQL, code, configuration, and lockfiles are hashed.
- Tables, figures, and primary estimates map to a run and generating code.
- Regenerated results were compared with the manuscript.
- Differences and numerical tolerances are explained.

## Data governance

- Public and restricted roots are separate.
- No credentials, patient-level rows, identifiers, or sensitive caches are public.
- Notebook outputs and logs were inspected.
- Derived datasets and models were assessed for disclosure risk.
- Access instructions require users to obtain their own authorization.

## Release statement

State whether verification achieved bitwise, computational, statistical, or conceptual reproducibility. List every known gap and unexecuted check.
