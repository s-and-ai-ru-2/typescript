#!/usr/bin/env python3
"""
R47-T028: Run split-second-stopwatch reference in isolated temp copy.
- Reads paths from .meta/config.json
- Copies exercise to temp dir including dotfiles
- Enables all test cases (xit -> it)
- Substitutes reference over solution in temp copy only
- Checks return code and test count
- Runs config path checker (real config passes, 3 invalid fixtures fail)
- Saves inputs, expected vs actual, tool versions to results.txt
- Exits non-zero on any failure
"""
import hashlib, json, os, re, shutil, subprocess, sys, tempfile

REPO     = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
EXERCISE = os.path.join(REPO, "exercises", "practice", "split-second-stopwatch")
CONFIG   = os.path.join(EXERCISE, ".meta", "config.json")
WORK_DIR = os.path.dirname(os.path.abspath(__file__))
CHECKER  = os.path.join(REPO, "tools", "course_checks", "r47-t028.py")

def file_hash(path):
    h = hashlib.md5()
    with open(path, "rb") as f:
        h.update(f.read())
    return h.hexdigest()

def check_config(exercise_root, config_path):
    with open(config_path) as f:
        config = json.load(f)
    files = config.get("files", {})
    for role in ("solution", "test", "example"):
        for rel_path in files.get(role, []):
            if ".." in rel_path.split("/"):
                return False, f"parent traversal in {role}: {rel_path}"
            resolved = os.path.normpath(os.path.join(exercise_root, rel_path))
            if not resolved.startswith(os.path.normpath(exercise_root)):
                return False, f"{role} escapes exercise root: {rel_path}"
            if not os.path.exists(resolved):
                return False, f"{role} does not exist: {rel_path}"
    return True, "all paths valid"

def run():
    lines = []
    def log(msg=""):
        print(msg)
        lines.append(str(msg))

    with open(CONFIG) as f:
        config = json.load(f)

    solution_rel = config["files"]["solution"][0]
    test_rel     = config["files"]["test"][0]
    example_rel  = config["files"]["example"][0]

    stub_path  = os.path.join(EXERCISE, solution_rel)
    proof_path = os.path.join(EXERCISE, example_rel)

    node_ver = subprocess.check_output(["node", "--version"], text=True).strip()
    py_ver   = sys.version.split()[0]
    log(f"node={node_ver}  python={py_ver}")

    stub_hash_before = file_hash(stub_path)
    failures = []

    tmpdir = tempfile.mkdtemp(prefix="r47t028_")
    try:
        dest = os.path.join(tmpdir, "split-second-stopwatch")
        shutil.copytree(EXERCISE, dest)

        # Enable all test cases
        test_path_tmp = os.path.join(dest, test_rel)
        with open(test_path_tmp) as f:
            test_src = f.read()
        test_src = test_src.replace("xit(", "it(")
        with open(test_path_tmp, "w") as f:
            f.write(test_src)

        # Substitute reference over solution
        shutil.copy2(proof_path, os.path.join(dest, solution_rel))

        # Install deps
        subprocess.run(["corepack", "yarn", "install"], cwd=dest,
                       check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        # Run tests with watch disabled
        result = subprocess.run(
            ["corepack", "yarn", "jest", "--no-cache", "--watchAll=false"],
            cwd=dest, capture_output=True, text=True
        )

        output = result.stdout + result.stderr
        log("--- jest output ---")
        log(output)

        match = re.search(r"Tests:\s+(.*)", output)
        test_line = match.group(1) if match else ""
        total_match = re.search(r"(\d+)\s+total", test_line)
        total_tests = int(total_match.group(1)) if total_match else 0

        if total_tests == 0:
            failures.append("FAIL: zero tests ran")
        else:
            log(f"PASS: {total_tests} tests ran")

        if result.returncode != 0:
            failures.append(f"FAIL: jest exit code {result.returncode}")
        else:
            log("PASS: jest exit code 0")

        if file_hash(stub_path) != stub_hash_before:
            failures.append("FAIL: learner stub was modified")
        else:
            log("PASS: learner stub unchanged")

        # Config path checker
        log("")
        log("--- config path checks ---")

        # Real config must pass
        passed, reason = check_config(EXERCISE, CONFIG)
        if passed:
            log(f"PASS: real config — {reason}")
        else:
            failures.append(f"FAIL: real config should pass: {reason}")
            log(failures[-1])

        fixtures_dir = tempfile.mkdtemp(prefix="r47t028_fix_")
        try:
            # Fixture 1: missing reference
            d1 = os.path.join(fixtures_dir, "missing_ref")
            shutil.copytree(EXERCISE, d1)
            os.remove(os.path.join(d1, ".meta", "proof.ci.ts"))
            passed, reason = check_config(d1, os.path.join(d1, ".meta", "config.json"))
            if not passed:
                log(f"PASS: missing-reference fixture failed as expected — {reason}")
            else:
                failures.append("FAIL: missing-reference fixture should have failed")
                log(failures[-1])

            # Fixture 2: missing test
            d2 = os.path.join(fixtures_dir, "missing_test")
            shutil.copytree(EXERCISE, d2)
            os.remove(os.path.join(d2, "split-second-stopwatch.test.ts"))
            passed, reason = check_config(d2, os.path.join(d2, ".meta", "config.json"))
            if not passed:
                log(f"PASS: missing-test fixture failed as expected — {reason}")
            else:
                failures.append("FAIL: missing-test fixture should have failed")
                log(failures[-1])

            # Fixture 3: outside-exercise path
            d3 = os.path.join(fixtures_dir, "outside_path")
            shutil.copytree(EXERCISE, d3)
            bad_cfg_path = os.path.join(d3, ".meta", "config.json")
            with open(bad_cfg_path) as f:
                cfg = json.load(f)
            cfg["files"]["solution"] = ["../../../etc/passwd"]
            with open(bad_cfg_path, "w") as f:
                json.dump(cfg, f)
            passed, reason = check_config(d3, bad_cfg_path)
            if not passed:
                log(f"PASS: outside-exercise path fixture failed as expected — {reason}")
            else:
                failures.append("FAIL: outside-exercise path fixture should have failed")
                log(failures[-1])
        finally:
            shutil.rmtree(fixtures_dir, ignore_errors=True)

        log(f"\nTotal tests run: {total_tests}")
        if failures:
            for f in failures:
                log(f)
            log("RESULT: FAIL")
        else:
            log("RESULT: PASS")

    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)
        with open(os.path.join(WORK_DIR, "results.txt"), "w") as f:
            f.write("\n".join(lines) + "\n")

    if failures:
        sys.exit(1)

if __name__ == "__main__":
    run()
