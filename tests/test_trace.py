import json
from sipl.interpreter import trace
from sipl.parser import parse

def kinds(events):
    return [e.kind for e in events]

def test_simple_assign():
    events, res, err = trace(parse("x := 1"))
    assert err is None and res.state == {"x": 1}
    assert kinds(events) == ["before_statement", "assign", "after_statement", "finished"]
    assert events[1].data == {"var": "x", "old": None, "new": 1}

def test_while_conditions():
    events, _, _ = trace(parse("i := 0; while i < 3 do i := i + 1"))
    conds = [e.data["value"] for e in events if e.kind == "condition"]
    assert conds == [True, True, True, False]

def test_after_statement_has_state_snapshot():
    events, _, _ = trace(parse("x := 1; x := 2"))
    after = [e for e in events if e.kind == "after_statement"]
    assert after[0].data["state"] == {"x": 1}
    assert after[1].data["state"] == {"x": 2}

def test_error_event():
    events, res, err = trace(parse("y := x"))
    assert res is None and err is not None
    assert events[-1].kind == "error"

def test_json_serializable_and_str():
    events, _, _ = trace(parse("x := 1"))
    json.dumps([e.to_dict() for e in events])
    assert "assign" in str(events[1])
