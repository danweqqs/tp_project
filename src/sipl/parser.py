from __future__ import annotations

from pathlib import Path

from lark import Lark, Token, Tree
from lark.exceptions import UnexpectedCharacters, UnexpectedInput, UnexpectedToken

from .ast_nodes import (
    Assign, BinOp, Block, Bool, Compare, If, Logic, Neg, Not, Num, Seq, Skip,
    SourceSpan, Var, While,
)
from .diagnostics import Diagnostic, SiplSyntaxError

GRAMMAR_PATH = Path(__file__).resolve().parents[2] / "grammar" / "sipl.lark"

_parser = Lark(
    GRAMMAR_PATH.read_text(encoding="utf-8"),
    parser="lalr",
    propagate_positions=True,
    keep_all_tokens=True,
    maybe_placeholders=False,
)

_PASS = {"start", "simple", "cond", "atom_cond"}

def span_of(x) -> SourceSpan:
    return SourceSpan(x.start_pos, x.end_pos, x.line, x.column, x.end_line, x.end_column)

def _term_name(name):
    if name == "NAME":
        return "ідентифікатор"
    if name == "NUMBER":
        return "число"
    if name == "$END":
        return "кінець програми"
    for t in _parser.terminals:
        if t.name == name and type(t.pattern).__name__ == "PatternStr":
            return f"'{t.pattern.value}'"
    return name

def _eof_pos(text):
    return text.count("\n") + 1, len(text) - (text.rfind("\n") + 1) + 1

def _syntax_error(text, e):
    if isinstance(e, UnexpectedToken):
        expected = sorted({_term_name(x) for x in (getattr(e, "expected", None) or ())})
        hint = f"; очікувалось: {', '.join(expected[:6])}" if expected else ""
        tok = e.token
        if tok.type == "$END":
            line, col = _eof_pos(text)
            span = SourceSpan(len(text), len(text), line, col, line, col)
            return Diagnostic("syntax-error", "неочікуваний кінець програми" + hint, span)
        return Diagnostic("syntax-error", f"неочікуваний токен '{tok.value}'" + hint, span_of(tok))
    if isinstance(e, UnexpectedCharacters):
        p = e.pos_in_stream
        span = SourceSpan(p, p + 1, e.line, e.column, e.line, e.column + 1)
        return Diagnostic("syntax-error", f"недопустимий символ {text[p]!r}", span)
    line, col = _eof_pos(text)
    return Diagnostic("syntax-error", "синтаксична помилка", SourceSpan(0, 0, line, col, line, col))

def parse_cst(text: str) -> Tree:
    try:
        return _parser.parse(text)
    except UnexpectedInput as e:
        raise SiplSyntaxError(_syntax_error(text, e)) from None

def _trees(t):
    return [c for c in t.children if isinstance(c, Tree)]

def _build(t):
    d = str(t.data)
    ch = t.children
    tr = _trees(t)
    sp = span_of(t.meta)

    if d in _PASS:
        return _build(tr[0])
    if d == "stmt":
        stmts = [_build(x) for x in tr]
        return stmts[0] if len(stmts) == 1 else Seq(stmts, span=sp)
    if d == "assign":
        return Assign(ch[0].value, _build(tr[0]), span=sp)
    if d == "skip":
        return Skip(span=sp)
    if d == "if_stmt":
        orelse = _build(tr[2]) if len(tr) == 3 else None
        return If(_build(tr[0]), _build(tr[1]), orelse, span=sp)
    if d == "while_stmt":
        return While(_build(tr[0]), _build(tr[1]), span=sp)
    if d == "block":
        return Block(_build(tr[0]), span=sp)
    if d in ("or_cond", "and_cond"):
        if len(tr) == 1:
            return _build(tr[0])
        return Logic(d[:-5], _build(tr[0]), _build(tr[1]), span=sp)
    if d == "not_cond":
        if len(ch) == 1:
            return _build(tr[0])
        return Not(_build(tr[0]), span=sp)
    if d == "compare":
        return Compare(tr[1].children[0].value, _build(tr[0]), _build(tr[2]), span=sp)
    if d == "bool":
        return Bool(ch[0].type == "TRUE", span=sp)
    if d in ("expr", "term"):
        if len(ch) == 1:
            return _build(tr[0])
        return BinOp(ch[1].value, _build(tr[0]), _build(tr[1]), span=sp)
    if d == "factor":
        first = ch[0]
        if first.type == "NUMBER":
            return Num(int(first.value), span=span_of(first))
        if first.type == "NAME":
            return Var(first.value, span=span_of(first))
        if first.type == "MINUS":
            return Neg(_build(tr[0]), span=sp)
        return _build(tr[0])
    raise ValueError(f"unknown rule {d}")

def build_ast(cst: Tree):
    return _build(cst)

def parse(text: str):
    return build_ast(parse_cst(text))