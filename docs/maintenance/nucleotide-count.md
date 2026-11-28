# nucleotide-count — Isolated Runner

## Command

```
python3 tools/course_checks/r47-t029.py
```

## Requirements

- Node matching `package.json` (`engines` field)
- Corepack/Yarn 4.5.1 (pinned by the exercise)
- Python 3

## What it does

1. Reads `exercises/practice/nucleotide-count/.meta/config.json` to find solution, test and example paths
2. Copies the entire exercise to a temp directory (including dotfiles)
3. Enables all test cases (`xit` → `it`) in the temp copy
4. Substitutes `.meta/proof.ci.ts` over `nucleotide-count.ts` in the temp copy only
5. Runs jest with watch mode disabled
6. Reports the number of tests executed
7. Verifies the learner stub (`nucleotide-count.ts`) is unchanged before and after every run
8. Cleans up the temp directory
9. Exits non-zero on failure

## File roles

| Role | Path | Purpose |
|------|------|---------|
| Learner stub | `nucleotide-count.ts` | Unsolved starter file — never modified by this runner |
| Test suite | `nucleotide-count.test.ts` | Jest tests |
| Reference | `.meta/proof.ci.ts` | Substituted into temp copy for CI verification |
