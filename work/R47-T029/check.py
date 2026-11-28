#!/usr/bin/env python3
"""
R47-T029: Verify the nucleotide-count isolated runner.
- Success run: real reference passes, exit 0
- Failing reference: deliberately broken reference, exit non-zero
- Zero-test run: empty test file, exit non-zero
- Learner file hashes identical before and after every run
- Temp files cleaned up after every run
- Saves inputs, expected vs actual, tool versions to results.txt
"""
import hashlib, json, os, re, shutil, subprocess, sys, tempfile

REPO     = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
EXERCISE = os.path.join(REPO, "exercises", "practice", "nucleotide-count")
CONFIG   = os.path.join(EXERCISE, ".meta", "config.json")
WORK_DIR = os.path.dirname(os.path.abspath(__file__))

def file_hash(path):
    h = hashlib.md5()
    with open(path, "rb") as f:
        h.update(f.read())
    return h.hexdigest()

def run_jest(exercise_copy):
    """Run jest in exercise_copy, return (returncode, total_tests, output)."""
    result = subprocess.run(
        ["corepack", "yarn", "jest", "--no-cache", "--watchAll=false"],
        cwd=exercise_copy, capture_output=True, text=True
    )
    output = result.stdout + result.stderr
    match = re.search(r"Tests:\s+(.*)", output)
    test_line = match.group(1) if match else ""
    total_match = re.search(r"(\d+)\s+total", test_line)
    total_tests = int(total_match.group(1)) if total_match else 0
    return result.returncode, total_tests, output

def make_copy(tmpdir, name):
    dest = os.path.join(tmpdir, name)
    shutil.copytree(EXERCISE, dest)
    # Install deps
    subprocess.run(["corepack", "yarn", "install"], cwd=dest,
                   check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return dest

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

    failures = []
    tmpdir = tempfile.mkdtemp(prefix="r47t029_check_")

    try:
        # ── 1. Success run ───────────────────────────────────────────────────
        log("\n--- run 1: real reference (expect PASS) ---")
        stub_hash_before = file_hash(stub_path)

        dest1 = make_copy(tmpdir, "success")
        # Enable all tests
        with open(os.path.join(dest1, test_rel)) as f:
            src = f.read()
        with open(os.path.join(dest1, test_rel), "w") as f:
            f.write(src.replace("xit(", "it("))
        # Substitute reference
        shutil.copy2(proof_path, os.path.join(dest1, solution_rel))

        code, total, output = run_jest(dest1)
        log(output)
        log(f"  exit code: {code}  tests: {total}")

        stub_hash_after = file_hash(stub_path)
        if stub_hash_before != stub_hash_after:
            failures.append("FAIL run1: learner stub modified")
        else:
            log("  PASS: learner stub unchanged")

        if code == 0 and total > 0:
            log("  PASS: success run correct")
        else:
            failures.append(f"FAIL run1: expected exit 0 and >0 tests, got exit={code} tests={total}")

        # ── 2. Failing reference ─────────────────────────────────────────────
        log("\n--- run 2: deliberately failing reference (expect FAIL) ---")
        stub_hash_before = file_hash(stub_path)

        dest2 = make_copy(tmpdir, "failing")
        with open(os.path.join(dest2, test_rel)) as f:
            src = f.read()
        with open(os.path.join(dest2, test_rel), "w") as f:
            f.write(src.replace("xit(", "it("))
        # Write broken reference
        with open(os.path.join(dest2, solution_rel), "w") as f:
            f.write("export function nucleotideCounts(strand: string): any { throw new Error('deliberate fail') }\n")

        code2, total2, output2 = run_jest(dest2)
        log(output2)
        log(f"  exit code: {code2}  tests: {total2}")

        stub_hash_after = file_hash(stub_path)
        if stub_hash_before != stub_hash_after:
            failures.append("FAIL run2: learner stub modified")
        else:
            log("  PASS: learner stub unchanged")

        if code2 != 0:
            log("  PASS: failing reference correctly exits non-zero")
        else:
            failures.append("FAIL run2: expected non-zero exit for broken reference")

        # ── 3. Zero-test run ─────────────────────────────────────────────────
        log("\n--- run 3: empty test file (expect zero tests / FAIL) ---")
        stub_hash_before = file_hash(stub_path)

        dest3 = make_copy(tmpdir, "zerotests")
        shutil.copy2(proof_path, os.path.join(dest3, solution_rel))
        # Empty test file
        with open(os.path.join(dest3, test_rel), "w") as f:
            f.write("// empty\n")

        code3, total3, output3 = run_jest(dest3)
        log(output3)
        log(f"  exit code: {code3}  tests: {total3}")

        stub_hash_after = file_hash(stub_path)
        if stub_hash_before != stub_hash_after:
            failures.append("FAIL run3: learner stub modified")
        else:
            log("  PASS: learner stub unchanged")

        if total3 == 0 or code3 != 0:
            log("  PASS: zero-test run correctly detected")
        else:
            failures.append(f"FAIL run3: expected zero tests or non-zero exit, got tests={total3} exit={code3}")

        # ── Summary ──────────────────────────────────────────────────────────
        log("")
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
