from __future__ import annotations
import operator
from dataclasses import dataclass
from .ast_nodes import (
    Assign, BinOp, Block, Bool, Compare, If, Logic, Neg, Node, Not, Num, Seq,
    Skip, Var, While,
)
from .diagnostics import Diagnostic, SiplRuntimeError
from .trace import Event

_CMP = {
    "<": operator.lt, "<=": operator.le, ">": operator.gt,
    ">=": operator.ge, "=": operator.eq, "<>": operator.ne,
}

@dataclass
class RunResult:
    state: dict
    steps: int

class Interpreter:
    def __init__(self, max_steps=100_000, listener=None):
        self.max_steps = max_steps
        self.listener = listener
        self.state = {}
        self.steps = 0

    def run(self, program, state=None) -> RunResult:
        self.state = dict(state or {})
        self.steps = 0
        try:
            self._exec(program)
        except SiplRuntimeError as e:
            self._emit("error", e.diagnostic.span, message=e.diagnostic.message, code=e.diagnostic.code)
            raise
        self._emit("finished", None, state=dict(self.state))
        return RunResult(dict(self.state), self.steps)

    def _emit(self, kind, span, **data):
        if self.listener:
            self.listener(Event(kind, self.steps, span, data))

    def _error(self, code, message, node):
        return SiplRuntimeError(Diagnostic(code, message, node.span))

    def _tick(self, node):
        self.steps += 1
        if self.steps > self.max_steps:
            raise self._error("step-limit", f"перевищено ліміт кроків ({self.max_steps})", node)

    def _exec(self, n: Node):
        if isinstance(n, Seq):
            for s in n.stmts:
                self._exec(s)
            return
        name = type(n).__name__
        self._emit("before_statement", n.span, stmt=name)
        if isinstance(n, Assign):
            self._tick(n)
            value = self._eval(n.expr)
            old = self.state.get(n.name)
            self.state[n.name] = value
            self._emit("assign", n.span, var=n.name, old=old, new=value)
        elif isinstance(n, Skip):
            self._tick(n)
        elif isinstance(n, Block):
            self._exec(n.body)
        elif isinstance(n, If):
            self._tick(n)
            c = self._eval(n.cond)
            self._emit("condition", n.cond.span, value=c)
            if c:
                self._exec(n.then)
            elif n.orelse is not None:
                self._exec(n.orelse)
        elif isinstance(n, While):
            while True:
                self._tick(n)
                c = self._eval(n.cond)
                self._emit("condition", n.cond.span, value=c)
                if not c:
                    break
                self._exec(n.body)
        else:
            raise TypeError(f"не оператор: {name}")
        self._emit("after_statement", n.span, stmt=name, state=dict(self.state))

    def _eval(self, n):
        if isinstance(n, (Num, Bool)):
            return n.value
        if isinstance(n, Var):
            if n.name not in self.state:
                raise self._error("undefined-variable", f"змінна '{n.name}' не визначена", n)
            return self.state[n.name]
        if isinstance(n, Neg):
            return -self._eval(n.operand)
        if isinstance(n, Not):
            return not self._eval(n.operand)
        if isinstance(n, BinOp):
            a, b = self._eval(n.left), self._eval(n.right)
            if n.op == "+":
                return a + b
            if n.op == "-":
                return a - b
            if n.op == "*":
                return a * b
            if b == 0:
                raise self._error("division-by-zero", "ділення на нуль", n)
            return a // b if n.op == "/" else a % b
        if isinstance(n, Compare):
            return _CMP[n.op](self._eval(n.left), self._eval(n.right))
        if isinstance(n, Logic):
            a = self._eval(n.left)
            if n.op == "and":
                return a and self._eval(n.right)
            return a or self._eval(n.right)
        raise TypeError(f"не вираз: {type(n).__name__}")


def run(program, state=None, max_steps=100_000) -> RunResult:
    return Interpreter(max_steps).run(program, state)


def trace(program, state=None, max_steps=100_000):
    events = []
    try:
        result = Interpreter(max_steps, events.append).run(program, state)
        return events, result, None
    except SiplRuntimeError as e:
        return events, None, e