import pytest

from sipl.diagnostics import SiplSyntaxError
from sipl.parser import parse

VALID = [
    "skip",
    "x := 1",
    "x := 1; y := 2",
    "begin skip end",
    "begin begin skip end end",
    "if x > 0 then y := 1",
    "if x > 0 then y := 1 else y := 2",
    "while x > 0 do x := x - 1",
    "x := (1 + 2) * 3",
    "x := -y",
    "x := 7 % 2 / 1",
    "if not (x = 0) and y <> 1 or true then skip",
    "if (x + 1) > 2 then skip",
    "// коментар\nx := 1",
    "begin x := 1; while x < 5 do x := x + 1 end",
]

INVALID = [
    "",
    "x :=",
    "x := ;",
    "begin skip",
    "skip end",
    "if x > 0 skip",
    "while do skip",
    "x = 1",
    "x := 1 +",
    "1 := x",
    "x := 1 $",
    "if x then skip",
    "x := y z",
    "skip;",
    "begin end",
]

@pytest.mark.parametrize("src", VALID)
def test_valid(src):
    assert parse(src) is not None

@pytest.mark.parametrize("src", INVALID)
def test_invalid(src):
    with pytest.raises(SiplSyntaxError) as e:
        parse(src)
    assert e.value.diagnostic.span is not None
