import pytest

from sipl.diagnostics import SiplRuntimeError
from sipl.interpreter import run
from sipl.parser import parse

POWER = """
begin
  R := 1;
  while Y > 0 do
  begin
    R := R * X;
    Y := Y - 1
  end
end
"""

def result(src, state=None, **kw):
    return run(parse(src), state, **kw).state

def test_power():
    assert result(POWER, {"X": 2, "Y": 3}) == {"X": 2, "Y": 0, "R": 8}

def test_gcd():
    src = "while not (A = B) do if A > B then A := A - B else B := B - A"
    assert result(src, {"A": 12, "B": 18})["A"] == 6

def test_if_without_else():
    assert result("if x > 0 then y := 1", {"x": 0}) == {"x": 0}

def test_skip():
    assert result("skip", {"x": 1}) == {"x": 1}

def test_precedence_and_unary():
    assert result("x := 2 + 3 * 4; y := -3 + 5") == {"x": 14, "y": 2}

def test_floor_division_and_mod():
    assert result("x := 0 - 7; y := x / 2; z := x % 2") == {"x": -7, "y": -4, "z": 1}

def test_short_circuit():
    assert result("if false and (1 / 0 = 1) then skip") == {}

def test_input_state_not_mutated():
    s = {"x": 1}
    run(parse("x := 2"), s)
    assert s == {"x": 1}

def test_step_limit():
    with pytest.raises(SiplRuntimeError) as e:
        run(parse("while true do skip"), max_steps=50)
    assert e.value.diagnostic.code == "step-limit"

def test_undefined_variable():
    with pytest.raises(SiplRuntimeError) as e:
        run(parse("y := x + 1"))
    d = e.value.diagnostic
    assert d.code == "undefined-variable" and d.span.col == 6

def test_division_by_zero():
    with pytest.raises(SiplRuntimeError) as e:
        run(parse("x := 1 / 0"))
    assert e.value.diagnostic.code == "division-by-zero"

def test_steps_counted():
    assert run(parse("x := 1; y := 2")).steps == 2
