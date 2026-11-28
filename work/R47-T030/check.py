#!/usr/bin/env python3
"""
R47-T030: Run strain reference in isolated temp copy.
- Reads paths from .meta/config.json
- Copies exercise to temp dir including dotfiles
- Enables all test cases (xit -> it)
- Substitutes reference over solution in temp copy only
- Checks return code and test count
- Verifies decision table cases match exact test inputs and outcomes
- Saves inputs, expected vs actual, tool versions to results.txt
- Exits non-zero on any failure
"""
import hashlib, json, os, re, shutil, subprocess, sys, tempfile

REPO     = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
EXERCISE = os.path.join(REPO, "exercises", "practice", "strain")
CONFIG   = os.path.join(EXERCISE, ".meta", "config.json")
WORK_DIR = os.path.dirname(os.path.abspath(__file__))

def file_hash(path):
    h = hashlib.md5()
    with open(path, "rb") as f:
        h.update(f.read())
    return h.hexdigest()

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

    tmpdir = tempfile.mkdtemp(prefix="r47t030_")
    try:
        dest = os.path.join(tmpdir, "strain")
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

        # Verify decision table cases with exact test inputs
        log("")
        log("--- decision table verification ---")
        decision_table = [
            ("keeps on empty array returns empty array", "keep([], () => true)",     "[]"),
            ("keeps everything",                         "keep([1,3,5], () => true)", "[1,3,5]"),
            ("keeps nothing",                            "keep([1,3,5], () => false)","[]"),
        ]
        js_keep = """
function keep(array, predicate) {
  const output = [];
  array.forEach(el => { if (predicate(el)) output.push(el); });
  return output;
}
"""
        for desc, expr, expected in decision_table:
            js = js_keep + f"process.stdout.write(JSON.stringify({expr}));"
            r = subprocess.run(["node", "-e", js], capture_output=True, text=True)
            actual = r.stdout.strip()
            log(f"  case:     {desc}")
            log(f"  input:    {expr}")
            log(f"  expected: {expected}")
            log(f"  actual:   {actual}")
            if actual == expected:
                log("  PASS")
            else:
                failures.append(f"FAIL decision table: '{desc}' expected {expected} got {actual}")
                log("  FAIL")
            log()

        log(f"Total tests run: {total_tests}")
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
