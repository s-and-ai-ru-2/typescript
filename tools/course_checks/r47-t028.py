#!/usr/bin/env python3
"""
R47-T028: Path/configuration checker for split-second-stopwatch.
- Parses .meta/config.json files object
- Resolves each path relative to exercise root
- Rejects parent traversal
- Checks every declared file exists
- Tests 3 deliberately invalid fixtures
"""
import json, os, shutil, sys, tempfile

REPO     = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
EXERCISE = os.path.join(REPO, "exercises", "practice", "split-second-stopwatch")
CONFIG   = os.path.join(EXERCISE, ".meta", "config.json")

def check_config(exercise_root, config_path):
    """
    Returns (passed, reason).
    passed=True if all declared paths resolve inside exercise_root and exist.
    """
    with open(config_path) as f:
        config = json.load(f)

    files = config.get("files", {})
    all_paths = []
    for role in ("solution", "test", "example"):
        for p in files.get(role, []):
            all_paths.append((role, p))

    for role, rel_path in all_paths:
        # Reject parent traversal
        if ".." in rel_path.split("/"):
            return False, f"parent traversal in {role} path: {rel_path}"
        resolved = os.path.normpath(os.path.join(exercise_root, rel_path))
        # Must stay inside exercise root
        if not resolved.startswith(os.path.normpath(exercise_root)):
            return False, f"{role} path escapes exercise root: {rel_path}"
        # Must exist
        if not os.path.exists(resolved):
            return False, f"{role} path does not exist: {rel_path}"

    return True, "all paths valid"

def run():
    failures = []

    # 1. Real config must pass
    passed, reason = check_config(EXERCISE, CONFIG)
    if passed:
        print("PASS: real config valid —", reason)
    else:
        failures.append(f"FAIL: real config should pass but got: {reason}")
        print(failures[-1])

    tmpdir = tempfile.mkdtemp(prefix="r47t028_fixtures_")
    try:
        # 2. Missing reference fixture — remove .meta/proof.ci.ts
        dest = os.path.join(tmpdir, "missing_ref")
        shutil.copytree(EXERCISE, dest)
        os.remove(os.path.join(dest, ".meta", "proof.ci.ts"))
        passed, reason = check_config(dest, os.path.join(dest, ".meta", "config.json"))
        if not passed:
            print(f"PASS: missing-reference fixture correctly failed — {reason}")
        else:
            failures.append("FAIL: missing-reference fixture should have failed")
            print(failures[-1])

        # 3. Missing test fixture — remove test file
        dest2 = os.path.join(tmpdir, "missing_test")
        shutil.copytree(EXERCISE, dest2)
        os.remove(os.path.join(dest2, "split-second-stopwatch.test.ts"))
        passed, reason = check_config(dest2, os.path.join(dest2, ".meta", "config.json"))
        if not passed:
            print(f"PASS: missing-test fixture correctly failed — {reason}")
        else:
            failures.append("FAIL: missing-test fixture should have failed")
            print(failures[-1])

        # 4. Outside-exercise path fixture — inject parent traversal path
        dest3 = os.path.join(tmpdir, "outside_path")
        shutil.copytree(EXERCISE, dest3)
        bad_config = os.path.join(dest3, ".meta", "config.json")
        with open(bad_config) as f:
            cfg = json.load(f)
        cfg["files"]["solution"] = ["../../../etc/passwd"]
        with open(bad_config, "w") as f:
            json.dump(cfg, f)
        passed, reason = check_config(dest3, bad_config)
        if not passed:
            print(f"PASS: outside-exercise path fixture correctly failed — {reason}")
        else:
            failures.append("FAIL: outside-exercise path fixture should have failed")
            print(failures[-1])

    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)

    if failures:
        for f in failures:
            print(f)
        sys.exit(1)
    else:
        print("\nRESULT: all config checks PASS")

if __name__ == "__main__":
    run()
