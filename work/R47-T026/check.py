#!/usr/bin/env python3
"""
R47-T026 check: run bowling reference in isolated temp copy, verify learner stub unchanged.
Also runs approach2 against the 3 named cases to confirm both implementations agree.
Saves inputs, expected vs actual, and tool versions to work/R47-T026/results.txt.
"""
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile

REPO     = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
EXERCISE = os.path.join(REPO, "exercises", "practice", "bowling")
CONFIG   = os.path.join(EXERCISE, ".meta", "config.json")
WORK_DIR = os.path.dirname(os.path.abspath(__file__))
RESULTS  = os.path.join(WORK_DIR, "results.txt")

def file_hash(path):
    h = hashlib.md5()
    with open(path, "rb") as f:
        h.update(f.read())
    return h.hexdigest()

def run_check():
    lines = []
    def log(msg=""):
        print(msg)
        lines.append(msg)

    with open(CONFIG) as f:
        config = json.load(f)

    solution_rel = config["files"]["solution"][0]   # bowling.ts
    example_rel  = config["files"]["example"][0]    # .meta/proof.ci.ts

    stub_path  = os.path.join(EXERCISE, solution_rel)
    proof_path = os.path.join(EXERCISE, example_rel)

    node_ver = subprocess.check_output(["node", "--version"], text=True).strip()
    py_ver   = sys.version.split()[0]

    log(f"Versions: node={node_ver}  python={py_ver}")
    log()

    stub_hash_before = file_hash(stub_path)
    failures = []

    tmpdir = tempfile.mkdtemp(prefix="r47t026_")
    try:
        # ── 1. Copy exercise including dotfiles ──────────────────────────────
        dest = os.path.join(tmpdir, "bowling")
        shutil.copytree(EXERCISE, dest)

        # ── 2. Substitute reference over solution in temp copy ───────────────
        shutil.copy2(proof_path, os.path.join(dest, solution_rel))

        # ── 3. Install deps ──────────────────────────────────────────────────
        subprocess.run(
            ["corepack", "yarn", "install"],
            cwd=dest, check=True,
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
        )

        # ── 4. Run via package.json test:implementation script (watch disabled)
        result = subprocess.run(
            ["corepack", "yarn", "jest", "--no-cache", "--watchAll=false"],
            cwd=dest,
            capture_output=True, text=True
        )

        output = result.stdout + result.stderr
        log("--- jest output ---")
        log(output)

        # ── 5. Parse test count ──────────────────────────────────────────────
        match       = re.search(r"Tests:\s+(.*)", output)
        test_line   = match.group(1) if match else ""
        total_match = re.search(r"(\d+)\s+total", test_line)
        total_tests = int(total_match.group(1)) if total_match else 0

        # ── 6. Assertions ────────────────────────────────────────────────────
        if total_tests == 0:
            failures.append("FAIL: zero tests ran")
        else:
            log(f"PASS: {total_tests} tests ran")

        if result.returncode != 0:
            failures.append(f"FAIL: jest exited with code {result.returncode}")
        else:
            log("PASS: jest exit code 0")

        stub_hash_after = file_hash(stub_path)
        if stub_hash_before != stub_hash_after:
            failures.append("FAIL: learner stub was modified!")
        else:
            log("PASS: learner stub unchanged")

        # ── 7. Verify approach2 passes the 3 named cases ────────────────────
        log()
        log("--- approach2 named-case verification ---")
        named_cases = [
            # (description, rolls, expected_score)
            ("should be able to score a game with all zeros",
             [0]*20, 0),
            ("should be able to score a game with no strikes or spares",
             [3, 6]*10, 90),
            ("a spare followed by zeros is worth ten points",
             [6, 4] + [0]*18, 10),
        ]

        approach2_js = r"""
function keep(array, predicate) { return array.filter(predicate); }
class Bowling {
  constructor() { this.rolls = []; }
  roll(pins) { this.rolls.push(pins); }
  score() {
    let total = 0, i = 0;
    for (let frame = 0; frame < 10; frame++) {
      if (this.rolls[i] === 10) {
        total += 10 + (this.rolls[i+1]||0) + (this.rolls[i+2]||0); i += 1;
      } else if ((this.rolls[i]||0) + (this.rolls[i+1]||0) === 10) {
        total += 10 + (this.rolls[i+2]||0); i += 2;
      } else {
        total += (this.rolls[i]||0) + (this.rolls[i+1]||0); i += 2;
      }
    }
    return total;
  }
}
"""
        for desc, rolls, expected in named_cases:
            js = approach2_js + f"""
const b = new Bowling();
const rolls = {json.dumps(rolls)};
rolls.forEach(p => b.roll(p));
const actual = b.score();
process.stdout.write(String(actual));
"""
            r = subprocess.run(["node", "--input-type=module"],
                               input=js, capture_output=True, text=True)
            actual_str = r.stdout.strip()
            log(f"  Input:    rolls={rolls}")
            log(f"  Expected: {expected}")
            log(f"  Actual:   {actual_str}")
            try:
                actual = int(actual_str)
            except ValueError:
                actual = None
            if actual == expected:
                log(f"  PASS: {desc}")
            else:
                failures.append(f"FAIL approach2: '{desc}' expected {expected} got {actual_str}")
                log(f"  FAIL: {desc}")
            log()

        # ── 8. Summary ───────────────────────────────────────────────────────
        log(f"Tests run: {total_tests}")
        if failures:
            for f in failures:
                log(f)
            log("\nRESULT: FAIL")
        else:
            log("\nRESULT: PASS")

    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)
        # Save results
        with open(RESULTS, "w") as f:
            f.write("\n".join(lines) + "\n")

    if failures:
        sys.exit(1)

if __name__ == "__main__":
    run_check()
