from __future__ import annotations
from dataclasses import dataclass, field
from .ast_nodes import (
    Assign,
    BinOp,
    Block,
    Bool,
    Compare,
    If,
    Logic,
    Neg,
    Not,
    Num,
    Seq,
    Skip,
    SourceSpan,
    Var,
    While,
)

OP_NAMES = {
    "+": "add",
    "-": "sub",
    "*": "mult",
    "/": "div",
    "%": "mod",
    "=": "eq",
    "<>": "neq",
    ">": "gr",
    "<": "lt",
    ">=": "geq",
    "<=": "leq",
    "and": "and",
    "or": "or",
}


@dataclass
class Term:
    head: str
    args: list = field(default_factory=list)
    sub: str | None = None
    kind: str = "call"
    span: SourceSpan | None = None

    def to_dict(self):
        return {
            "head": self.head,
            "sub": self.sub,
            "kind": self.kind,
            "args": [a.to_dict() for a in self.args],
            "span": self.span.to_dict() if self.span else None,
        }


def build_term(n) -> Term:
    sp = n.span
    if isinstance(n, Num):
        return Term(f"{n.value}\u0304", kind="leaf", span=sp)
    if isinstance(n, Var):
        return Term(f"{n.name}⇒", kind="leaf", span=sp)
    if isinstance(n, Bool):
        return Term("true" if n.value else "false", kind="leaf", span=sp)
    if isinstance(n, Neg):
        return Term("S^1", [Term("minus", kind="leaf", span=sp), build_term(n.operand)], span=sp)
    if isinstance(n, Not):
        return Term("S^1", [Term("neg", kind="leaf", span=sp), build_term(n.operand)], span=sp)
    if isinstance(n, (BinOp, Compare, Logic)):
        fn = OP_NAMES.get(n.op, n.op)
        return Term(
            "S^2",
            [Term(fn, kind="leaf", span=sp), build_term(n.left), build_term(n.right)],
            span=sp,
        )
    if isinstance(n, Assign):
        return Term("AS", [build_term(n.expr)], sub=n.name, span=sp)
    if isinstance(n, Skip):
        return Term("ID", span=sp)
    if isinstance(n, Block):
        return build_term(n.body)
    if isinstance(n, Seq):
        parts = []
        for s in n.stmts:
            t = build_term(s)
            if t.kind == "infix" and t.head == "•":
                parts.extend(t.args)
            else:
                parts.append(t)
        return Term("•", parts, kind="infix", span=sp)
    if isinstance(n, If):
        orelse = build_term(n.orelse) if n.orelse else Term("ID")
        return Term("IF", [build_term(n.cond), build_term(n.then), orelse], span=sp)
    if isinstance(n, While):
        return Term("WH", [build_term(n.cond), build_term(n.body)], span=sp)
    raise TypeError(type(n).__name__)


def render(t: Term, wrap=False) -> str:
    if t.kind == "leaf":
        return t.head
    if t.kind == "prefix":
        return t.head + render(t.args[0], True)
    if t.kind == "infix":
        s = f" {t.head} ".join(render(a, True) for a in t.args)
        return f"({s})" if wrap else s
    name = f"{t.head}^{t.sub}" if t.sub else t.head
    if not t.args:
        return name
    return f"{name}({', '.join(render(a) for a in t.args)})"