import pytest

from sipl.ast_nodes import (
    Assign, BinOp, Block, Compare, If, Logic, Num, Seq, Skip, Var, While,
)
from sipl.diagnostics import SiplSyntaxError
from sipl.parser import parse, parse_cst

def test_assign():
    assert parse("x := 1") == Assign("x", Num(1))

def test_skip_and_block():
    assert parse("begin skip end") == Block(Skip())

def test_precedence():
    assert parse("x := 2 + 3 * 4") == Assign("x", BinOp("+", Num(2), BinOp("*", Num(3), Num(4))))

def test_left_associativity():
    expected = Assign("x", BinOp("-", BinOp("-", Num(10), Num(3)), Num(2)))
    assert parse("x := 10 - 3 - 2") == expected

def test_logic_precedence():
    node = parse("if a > 0 or b > 0 and c > 0 then skip")
    assert isinstance(node.cond, Logic) and node.cond.op == "or"
    assert node.cond.right.op == "and"

def test_seq():
    assert parse("x := 1; y := 2") == Seq([Assign("x", Num(1)), Assign("y", Num(2))])

def test_while():
    node = parse("while x > 0 do x := x - 1")
    assert node == While(Compare(">", Var("x"), Num(0)), Assign("x", BinOp("-", Var("x"), Num(1))))

def test_dangling_else_binds_to_nearest_if():
    node = parse("if a > 0 then if b > 0 then x := 1 else x := 2")
    assert isinstance(node, If) and node.orelse is None
    assert node.then.orelse is not None

def test_cst_root():
    assert str(parse_cst("skip").data) == "start"

def test_spans():
    node = parse("x := 1")
    assert (node.span.start, node.span.end, node.span.line, node.span.col) == (0, 6, 1, 1)
    assert node.expr.span.col == 6

def test_spans_multiline():
    node = parse("x := 1;\ny := 2")
    assert node.stmts[1].span.line == 2 and node.stmts[1].span.col == 1

@pytest.mark.parametrize(
    "src,line,col",
    [("begin x := 1", 1, 13), ("x = 1", 1, 3), ("x := 1 $ 2", 1, 8), ("x := 1;\ny :=", 2, 5)],
)
def test_error_positions(src, line, col):
    with pytest.raises(SiplSyntaxError) as e:
        parse(src)
    assert (e.value.diagnostic.span.line, e.value.diagnostic.span.col) == (line, col)
