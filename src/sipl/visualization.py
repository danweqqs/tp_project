from __future__ import annotations

import html
import json
from dataclasses import dataclass, field

from lark import Token

from .ast_nodes import SourceSpan
from .parser import span_of

HGAP, VGAP, PAD, BOX_H = 14, 46, 16, 26


@dataclass
class VNode:
    label: str
    kind: str
    span: SourceSpan | None
    children: list = field(default_factory=list)


def from_cst(t) -> VNode:
    if isinstance(t, Token):
        return VNode(f"{t.type} '{t.value}'", "token", span_of(t))
    return VNode(str(t.data), "rule", span_of(t.meta), [from_cst(c) for c in t.children])


def from_ast(n) -> VNode:
    return VNode(n.label(), "ast", n.span, [from_ast(c) for c in n.children()])


def to_dict(v: VNode):
    return {
        "label": v.label,
        "kind": v.kind,
        "span": v.span.to_dict() if v.span else None,
        "children": [to_dict(c) for c in v.children],
    }


def to_text(v: VNode) -> str:
    lines = []

    def rec(n, prefix, last, root):
        pos = f"  [{n.span.line}:{n.span.col}]" if n.span else ""
        if root:
            lines.append(n.label + pos)
            child_prefix = ""
        else:
            lines.append(prefix + ("└── " if last else "├── ") + n.label + pos)
            child_prefix = prefix + ("    " if last else "│   ")
        for i, c in enumerate(n.children):
            rec(c, child_prefix, i == len(n.children) - 1, False)

    rec(v, "", True, True)
    return "\n".join(lines)


def to_dot(v: VNode) -> str:
    out = ["digraph tree {", '  node [fontname="Courier", shape=box];']
    counter = [0]

    def rec(n):
        i = counter[0]
        counter[0] += 1
        label = n.label.replace("\\", "\\\\").replace('"', '\\"')
        shape = "ellipse" if n.kind == "token" else "box"
        out.append(f'  n{i} [label="{label}", shape={shape}];')
        for c in n.children:
            j = rec(c)
            out.append(f"  n{i} -> n{j};")
        return i

    rec(v)
    out.append("}")
    return "\n".join(out)


def _width(n):
    return 8 * len(n.label) + 16


def to_svg(v: VNode) -> str:
    extent, pos = {}, {}

    def ext(n):
        total = 0
        if n.children:
            total = sum(ext(c) for c in n.children) + HGAP * (len(n.children) - 1)
        extent[id(n)] = max(_width(n), total)
        return extent[id(n)]

    def place(n, left, depth):
        e = extent[id(n)]
        if not n.children:
            x = left + e / 2
        else:
            total = sum(extent[id(c)] for c in n.children) + HGAP * (len(n.children) - 1)
            cl = left + (e - total) / 2
            for c in n.children:
                place(c, cl, depth + 1)
                cl += extent[id(c)] + HGAP
            x = (pos[id(n.children[0])][0] + pos[id(n.children[-1])][0]) / 2
        pos[id(n)] = (x, PAD + depth * VGAP)

    ext(v)
    place(v, PAD, 0)
    width = extent[id(v)] + 2 * PAD
    height = max(y for _, y in pos.values()) + BOX_H + PAD

    edges, nodes = [], []

    def draw(n):
        x, y = pos[id(n)]
        w = _width(n)
        for c in n.children:
            cx, cy = pos[id(c)]
            edges.append(f'<line x1="{x:.1f}" y1="{y + BOX_H}" x2="{cx:.1f}" y2="{cy}"/>')
            draw(c)
        s, e = (n.span.start, n.span.end) if n.span else (0, 0)
        pos_txt = f"{n.span.line}:{n.span.col}" if n.span else ""
        cls = "node tok" if n.kind == "token" else "node"
        nodes.append(
            f'<g class="{cls}" data-start="{s}" data-end="{e}"><title>{pos_txt}</title>'
            f'<rect x="{x - w / 2:.1f}" y="{y}" width="{w}" height="{BOX_H}" rx="5"/>'
            f'<text x="{x:.1f}" y="{y + BOX_H / 2 + 1}" text-anchor="middle" '
            f'dominant-baseline="middle">{html.escape(n.label)}</text></g>'
        )

    draw(v)
    style = (
        "<style>.edges line{stroke:#777}.node rect{fill:#e8eefc;stroke:#456}"
        ".node.tok rect{fill:#e6f4ea}.node.hl rect{fill:#ffd54f}"
        ".node text{font:13px monospace}</style>"
    )
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width:.0f}" height="{height:.0f}" '
        f'viewBox="0 0 {width:.0f} {height:.0f}">{style}<g class="edges">{"".join(edges)}</g>'
        f'{"".join(nodes)}</svg>'
    )


_PAGE = """<!doctype html>
<html lang="uk"><head><meta charset="utf-8"><title>SIPL: Parse Tree ↔ AST</title>
<style>body{font-family:sans-serif;margin:16px}pre{background:#f4f4f4;padding:10px}
mark{background:#ffd54f}.panel{overflow:auto;border:1px solid #ccc;margin-bottom:16px;padding:8px}</style>
</head><body>
<h3>Вихідний код</h3><pre id="src"></pre>
<h3>Parse Tree (конкретний синтаксис)</h3><div class="panel">__CST__</div>
<h3>AST (абстрактний синтаксис)</h3><div class="panel">__AST__</div>
<script>
const SRC = __SRC__;
const pre = document.getElementById('src');
const esc = s => s.replace(/&/g,'&amp;').replace(/</g,'&lt;');
pre.textContent = SRC;
document.querySelectorAll('.node').forEach(n => {
  n.addEventListener('mouseenter', () => {
    const a = +n.dataset.start, b = +n.dataset.end;
    pre.innerHTML = esc(SRC.slice(0,a)) + '<mark>' + esc(SRC.slice(a,b)) + '</mark>' + esc(SRC.slice(b));
    document.querySelectorAll('.node').forEach(m => {
      if (+m.dataset.start === a && +m.dataset.end === b) m.classList.add('hl');
    });
  });
  n.addEventListener('mouseleave', () => {
    pre.textContent = SRC;
    document.querySelectorAll('.hl').forEach(m => m.classList.remove('hl'));
  });
});
</script></body></html>
"""


def compare_html(source: str, cst: VNode, ast: VNode) -> str:
    src = json.dumps(source, ensure_ascii=False).replace("</", "<\\/")
    return _PAGE.replace("__SRC__", src).replace("__CST__", to_svg(cst)).replace("__AST__", to_svg(ast))
