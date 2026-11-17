from __future__ import annotations

from dataclasses import dataclass

from .ast_nodes import SourceSpan


@dataclass
class Diagnostic:
    code: str
    message: str
    span: SourceSpan | None = None
    severity: str = "error"

    def to_dict(self):
        return {
            "severity": self.severity,
            "code": self.code,
            "message": self.message,
            "span": self.span.to_dict() if self.span else None,
        }

    def format(self, path="<input>"):
        pos = f"{self.span.line}:{self.span.col}" if self.span else "?"
        return f"{path}:{pos}: {self.severity}: {self.message}"


class SiplSyntaxError(Exception):
    def __init__(self, diagnostic: Diagnostic):
        super().__init__(diagnostic.message)
        self.diagnostic = diagnostic


class SiplRuntimeError(Exception):
    def __init__(self, diagnostic: Diagnostic):
        super().__init__(diagnostic.message)
        self.diagnostic = diagnostic
