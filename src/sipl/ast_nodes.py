from __future__ import annotations

from dataclasses import dataclass, field, fields


@dataclass(frozen=True)
class SourceSpan:
    start: int
    end: int
    line: int
    col: int
    end_line: int
    end_col: int

    def to_dict(self):
        return {
            "start": self.start,
            "end": self.end,
            "line": self.line,
            "col": self.col,
            "end_line": self.end_line,
            "end_col": self.end_col,
        }


@dataclass(kw_only=True)
class Node:
    span: SourceSpan | None = field(default=None, compare=False, repr=False)

    def children(self):
        for f in fields(self):
            if f.name == "span":
                continue
            v = getattr(self, f.name)
            if isinstance(v, Node):
                yield v
            elif isinstance(v, list):
                yield from (x for x in v if isinstance(x, Node))

    def label(self):
        parts = [type(self).__name__]
        for f in fields(self):
            v = getattr(self, f.name)
            if f.name == "span" or v is None or isinstance(v, (Node, list)):
                continue
            parts.append(str(v).lower() if isinstance(v, bool) else str(v))
        return " ".join(parts)

    def to_dict(self):
        d = {"type": type(self).__name__}
        for f in fields(self):
            if f.name == "span":
                continue
            v = getattr(self, f.name)
            if isinstance(v, Node):
                v = v.to_dict()
            elif isinstance(v, list):
                v = [x.to_dict() for x in v]
            d[f.name] = v
        d["span"] = self.span.to_dict() if self.span else None
        return d


class Expr(Node):
    pass


class Stmt(Node):
    pass


@dataclass
class Num(Expr):
    value: int


@dataclass
class Var(Expr):
    name: str


@dataclass
class Neg(Expr):
    operand: Expr


@dataclass
class BinOp(Expr):
    op: str
    left: Expr
    right: Expr


@dataclass
class Bool(Expr):
    value: bool


@dataclass
class Compare(Expr):
    op: str
    left: Expr
    right: Expr


@dataclass
class Not(Expr):
    operand: Expr


@dataclass
class Logic(Expr):
    op: str
    left: Expr
    right: Expr


@dataclass
class Assign(Stmt):
    name: str
    expr: Expr


@dataclass
class Skip(Stmt):
    pass


@dataclass
class Seq(Stmt):
    stmts: list[Stmt]


@dataclass
class If(Stmt):
    cond: Expr
    then: Stmt
    orelse: Stmt | None = None


@dataclass
class While(Stmt):
    cond: Expr
    body: Stmt


@dataclass
class Block(Stmt):
    body: Stmt
