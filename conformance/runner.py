import argparse
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CASES = Path(__file__).resolve().parent / "cases.json"

def call(cmd, sub, path, extra=()):
    env = dict(os.environ)
    env["PYTHONPATH"] = str(ROOT / "src") + os.pathsep + env.get("PYTHONPATH", "")
    p = subprocess.run(
        [*cmd, sub, str(path), "--json", *extra],
        capture_output=True, text=True, encoding="utf-8", env=env,
    )
    return json.loads(p.stdout)

def strip_spans(x):
    if isinstance(x, dict):
        return {k: strip_spans(v) for k, v in x.items() if k != "span"}
    if isinstance(x, list):
        return [strip_spans(v) for v in x]
    return x

def status_of(resp):
    if resp["ok"]:
        return "ok"
    return "syntax_error" if resp["diagnostics"][0]["code"] == "syntax-error" else "runtime_error"

def check_case(cmd, case, path):
    errors = []
    exp = case["expect"]
    extra = [a for k, v in case.get("vars", {}).items() for a in ("--var", f"{k}={v}")]
    resp = call(cmd, "run", path, extra)
    if status_of(resp) != exp["status"]:
        return [f"status {status_of(resp)} != {exp['status']}"]
    if "state" in exp and resp.get("state") != exp["state"]:
        errors.append(f"state {resp.get('state')} != {exp['state']}")
    if "error" in exp:
        d = resp["diagnostics"][0]
        for key, val in exp["error"].items():
            actual = d["code"] if key == "code" else d["span"][key]
            if actual != val:
                errors.append(f"error.{key} {actual} != {val}")
    if "term" in exp:
        got = call(cmd, "semantics", path)["term"]
        if got != exp["term"]:
            errors.append(f"term {got!r} != {exp['term']!r}")
    if "ast" in exp:
        got = strip_spans(call(cmd, "parse", path, ["--kind", "ast"])["ast"])
        if got != exp["ast"]:
            errors.append(f"ast {got} != {exp['ast']}")
    return errors

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cmd", default=f"{sys.executable} -m sipl")
    ap.add_argument("--cases", default=str(CASES))
    args = ap.parse_args()
    cmd = args.cmd.split()
    cases = json.loads(Path(args.cases).read_text(encoding="utf-8"))
    failed = 0
    with tempfile.TemporaryDirectory() as tmp:
        for case in cases:
            path = Path(tmp) / "case.sipl"
            path.write_text(case["source"], encoding="utf-8")
            errors = check_case(cmd, case, path)
            print(("FAIL " if errors else "ok   ") + case["name"])
            for e in errors:
                print("     " + e)
            failed += bool(errors)
    print(f"{len(cases) - failed}/{len(cases)} passed")
    return 1 if failed else 0

if __name__ == "__main__":
    raise SystemExit(main())
