from __future__ import annotations

from dataclasses import dataclass, field

from .ast_nodes import SourceSpan


@dataclass
class Event:
    kind: str
    step: int
    span: SourceSpan | None
    data: dict = field(default_factory=dict)

    def to_dict(self):
        return {
            "kind": self.kind,
            "step": self.step,
            "span": self.span.to_dict() if self.span else None,
            "data": self.data,
        }

    def __str__(self):
        d = self.data
        if self.kind == "assign":
            body = f"{d['var']}: {d['old']} -> {d['new']}"
        elif self.kind == "condition":
            body = f"умова = {str(d['value']).lower()}"
        elif self.kind in ("before_statement", "after_statement"):
            body = d["stmt"]
        elif self.kind == "finished":
            body = ", ".join(f"{k}={v}" for k, v in sorted(d["state"].items()))
        else:
            body = d.get("message", "")
        pos = f" ({self.span.line}:{self.span.col})" if self.span else ""
        return f"[{self.step}] {self.kind}: {body}{pos}"
