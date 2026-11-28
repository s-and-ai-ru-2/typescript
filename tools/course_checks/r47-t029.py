#!/usr/bin/env python3
"""
R47-T029: Isolated runner for exercises/practice/nucleotide-count.
- Reads paths from .meta/config.json
- Copies exercise to temp dir including dotfiles
- Enables all test cases (xit -> it)
- Substitutes reference over solution in temp copy only
- Checks return code and test count
- Verifies learner file hashes unchanged before and after
- Cleans up temp dir in finally block
- Exits non-zero on any failure
"""
import hashlib, json, os, re, shutil, subprocess, sys, tempfile

REPO     = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
EXERCISE = os.path.join(REPO, "exercises", "practice", "nucleotide-count")
CONFIG   = os.path.join(EXERCISE, ".meta", "config.json")

def file_hash(path):
    h = hashlib.md5()
    with open(path, "rb") as f:
        h.update(f.read())
    return h.hexdigest()

def run(verbose=True):
    def log(msg=""):
        if verbose:
            print(msg)

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

    tmpdir = tempfile.mkdtemp(prefix="r47t029_")
    try:
        dest = os.path.join(tmpdir, "nucleotide-count")
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

        log(f"Tests run: {total_tests}")

        failures = []
        if total_tests == 0:
            failures.append("FAIL: zero tests ran")
        if result.returncode != 0:
            failures.append(f"FAIL: jest exit code {result.returncode}")

        return total_tests, result.returncode, failures

    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)
        stub_hash_after = file_hash(stub_path)
        if stub_hash_before != stub_hash_after:
            print("FAIL: learner stub was modified!")
            sys.exit(1)

if __name__ == "__main__":
    total, code, failures = run()
    if failures:
        for f in failures:
            print(f)
        sys.exit(1)
    print(f"PASS: {total} tests ran, exit code {code}")
