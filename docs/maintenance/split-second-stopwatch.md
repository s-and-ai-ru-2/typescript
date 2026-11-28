# split-second-stopwatch — Exercise File Map

## File roles

| Role | Path | Purpose |
|------|------|---------|
| Learner stub | `split-second-stopwatch.ts` | Unsolved starter file given to the learner — do not modify |
| Test suite | `split-second-stopwatch.test.ts` | Jest tests — generated from canonical problem-specifications; change via source, not by hand |
| Reference implementation | `.meta/proof.ci.ts` | Maintained reference used by the CI runner to verify tests pass |
| Metadata | `.meta/config.json` | Maps file roles (`solution`, `test`, `example`); controls which test types run |
| Test inclusion flags | `.meta/tests.toml` | Canonical test case inclusion/exclusion flags |

## How the runner finds files

The test runner reads `.meta/config.json` and resolves paths relative to the exercise root (`exercises/practice/split-second-stopwatch/`):

- `files.example[0]` → `.meta/proof.ci.ts` — substituted over the learner stub in a temp copy
- `files.test[0]` → `split-second-stopwatch.test.ts` — the Jest test suite that is run
- `files.solution[0]` → `split-second-stopwatch.ts` — the learner stub (never modified in the working tree)

All paths are resolved strictly inside the exercise directory. Parent traversal (`..`) is rejected.

## Generated vs maintained

- `split-second-stopwatch.test.ts` — **generated** from canonical problem-specifications; do not hand-edit
- `.meta/proof.ci.ts` — **maintained** by track contributors
- `split-second-stopwatch.ts` — **learner stub**; kept unsolved

## Validation command

```
python3 work/R47-T028/check.py
```

This runs the reference in an isolated temp copy, verifies all declared paths resolve inside the exercise, and confirms the three invalid metadata fixtures fail for the intended reason.
