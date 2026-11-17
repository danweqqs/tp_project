import json
from sipl import visualization as viz
from sipl.parser import build_ast, parse_cst

def trees(src):
    cst = parse_cst(src)
    return viz.from_cst(cst), viz.from_ast(build_ast(cst))

def test_text_ast():
    _, ast = trees("x := 1")
    assert viz.to_text(ast).splitlines() == ["Assign x  [1:1]", "└── Num 1  [1:6]"]

def test_cst_contains_tokens():
    cst, _ = trees("x := 1")
    text = viz.to_text(cst)
    assert "NAME 'x'" in text and "ASSIGN ':='" in text and "NUMBER '1'" in text

def test_cst_is_larger_than_ast():
    cst, ast = trees("x := 1 + 2")
    count = lambda n: 1 + sum(count(c) for c in n.children)
    assert count(cst) > count(ast)

def test_json_roundtrip():
    cst, _ = trees("skip")
    d = json.loads(json.dumps(viz.to_dict(cst)))
    assert d["label"] == "start"

def test_dot():
    _, ast = trees("x := 1")
    dot = viz.to_dot(ast)
    assert dot.startswith("digraph") and "n0 -> n1" in dot

def test_svg():
    _, ast = trees("while x > 0 do x := x - 1")
    svg = viz.to_svg(ast)
    assert svg.startswith("<svg") and svg.endswith("</svg>") and "While" in svg

def test_svg_escapes_labels():
    cst, _ = trees("if x < 1 then skip")
    assert "<'" not in viz.to_svg(cst)

def test_compare_html():
    cst, ast = trees("x := 1")
    page = viz.compare_html("x := 1", cst, ast)
    assert page.count("<svg") == 2 and "x := 1" in page
