import json
from pathlib import Path
import pytest
from sipl.cli import main

EXAMPLES = Path(__file__).resolve().parents[1] / "examples"

def call(capsys, *argv):
    code = main(list(map(str, argv)))
    out = capsys.readouterr()
    return code, out.out, out.err

@pytest.fixture
def src(tmp_path):
    def make(text, name="p.sipl"):
        p = tmp_path / name
        p.write_text(text, encoding="utf-8")
        return p
    return make

def test_run_text(capsys):
    code, out, _ = call(capsys, "run", EXAMPLES / "power.sipl", "--var", "X=2", "--var", "Y=3")
    assert code == 0 and "R = 8" in out

def test_run_json(capsys):
    code, out, _ = call(capsys, "run", EXAMPLES / "power.sipl", "--var", "X=2", "--var", "Y=3", "--json")
    data = json.loads(out)
    assert code == 0 and data["ok"] and data["state"]["R"] == 8

def test_syntax_error_exit_code(capsys, src):
    code, _, err = call(capsys, "check", src("x = 1"))
    assert code == 1 and ":1:3:" in err

def test_syntax_error_json(capsys, src):
    code, out, _ = call(capsys, "check", src("x = 1"), "--json")
    d = json.loads(out)
    assert code == 1 and not d["ok"] and d["diagnostics"][0]["span"]["col"] == 3

def test_runtime_error(capsys, src):
    code, out, _ = call(capsys, "run", src("y := x"), "--json")
    assert code == 3 and json.loads(out)["diagnostics"][0]["code"] == "undefined-variable"

def test_step_limit_option(capsys):
    code, _, err = call(capsys, "run", EXAMPLES / "infinite.sipl", "--max-steps", 10)
    assert code == 3 and "ліміт" in err

def test_missing_file(capsys):
    code, _, err = call(capsys, "run", "nope.sipl")
    assert code == 2 and err

def test_bad_var(capsys, src):
    code, _, _ = call(capsys, "run", src("skip"), "--var", "oops")
    assert code == 2

def test_check_ok(capsys):
    code, out, _ = call(capsys, "check", EXAMPLES / "gcd.sipl")
    assert code == 0 and "OK" in out

@pytest.mark.parametrize("fmt", ["text", "json", "dot", "svg"])
@pytest.mark.parametrize("kind", ["cst", "ast"])
def test_parse_formats(capsys, kind, fmt):
    code, out, _ = call(capsys, "parse", EXAMPLES / "max.sipl", "--kind", kind, "--format", fmt)
    assert code == 0 and out.strip()

def test_parse_json_ast(capsys):
    _, out, _ = call(capsys, "parse", EXAMPLES / "max.sipl", "--json")
    assert json.loads(out)["ast"]["type"] == "If"

def test_trace_text_and_json(capsys):
    code, out, _ = call(capsys, "trace", EXAMPLES / "sum.sipl", "--var", "N=3")
    assert code == 0 and "assign" in out
    code, out, _ = call(capsys, "trace", EXAMPLES / "sum.sipl", "--var", "N=3", "--json")
    assert json.loads(out)["events"][-1]["kind"] == "finished"

def test_trace_error(capsys):
    code, out, _ = call(capsys, "trace", EXAMPLES / "sum.sipl", "--json")
    assert code == 3 and not json.loads(out)["ok"]

def test_semantics(capsys):
    code, out, _ = call(capsys, "semantics", EXAMPLES / "max.sipl")
    assert code == 0 and out.strip() == "IF(S^2(gr, X⇒, Y⇒), AS^M(X⇒), AS^M(Y⇒))"

def test_compare_output_file(capsys, tmp_path):
    target = tmp_path / "out.html"
    code, _, _ = call(capsys, "compare", EXAMPLES / "power.sipl", "-o", target)
    assert code == 0 and target.read_text(encoding="utf-8").count("<svg") == 2

def test_stdin(capsys, monkeypatch):
    import io
    monkeypatch.setattr("sys.stdin", io.StringIO("x := 5"))
    code, out, _ = call(capsys, "run", "-")
    assert code == 0 and "x = 5" in out
