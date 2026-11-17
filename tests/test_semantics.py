import pytest

from sipl.parser import parse
from sipl.semantics import build_term, render

GOLDEN = [
    ("skip", "ID"),
    ("x := 1", "AS^x(1̄)"),
    ("x := 1; y := 2", "AS^x(1̄) • AS^y(2̄)"),
    (
        "begin R := 1; while Y > 0 do begin R := R * X; Y := Y - 1 end end",
        "AS^R(1̄) • WH(S^2(gr, Y⇒, 0̄), AS^R(S^2(mult, R⇒, X⇒)) • AS^Y(S^2(sub, Y⇒, 1̄)))",
    ),
    ("if x > y then m := x else m := y", "IF(S^2(gr, x⇒, y⇒), AS^m(x⇒), AS^m(y⇒))"),
    ("if x > 0 then skip", "IF(S^2(gr, x⇒, 0̄), ID, ID)"),
    ("x := 2 + 3 * 4", "AS^x(S^2(add, 2̄, S^2(mult, 3̄, 4̄)))"),
    ("x := (2 + 3) * 4", "AS^x(S^2(mult, S^2(add, 2̄, 3̄), 4̄))"),
    ("x := -y", "AS^x(S^1(minus, y⇒))"),
    ("while x >= 1 and not y <> 2 do skip", "WH(S^2(and, S^2(geq, x⇒, 1̄), S^1(neg, S^2(neq, y⇒, 2̄))), ID)"),
    ("a := 1; begin b := 2; c := 3 end; d := 4", "AS^a(1̄) • AS^b(2̄) • AS^c(3̄) • AS^d(4̄)"),
]

@pytest.mark.parametrize("src,expected", GOLDEN)
def test_golden(src, expected):
    assert render(build_term(parse(src))) == expected

def test_term_to_dict():
    d = build_term(parse("x := 1")).to_dict()
    assert d["head"] == "AS" and d["sub"] == "x" and d["args"][0]["head"] == "1̄"