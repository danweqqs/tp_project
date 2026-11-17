from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from . import visualization as viz
from .diagnostics import SiplRuntimeError, SiplSyntaxError
from .interpreter import Interpreter, trace
from .parser import build_ast, parse_cst
from .semantics import build_term, render

EXIT_OK, EXIT_SYNTAX, EXIT_USAGE, EXIT_RUNTIME = 0, 1, 2, 3


def _dump(payload):
    print(json.dumps(payload, ensure_ascii=False, indent=2))


def _read(path):
    return sys.stdin.read() if path == "-" else Path(path).read_text(encoding="utf-8")


def _parse_vars(items):
    state = {}
    for item in items or []:
        name, sep, value = item.partition("=")
        if not sep or not name:
            raise ValueError(f"очікується NAME=ЧИСЛО, отримано '{item}'")
        state[name.strip()] = int(value)
    return state


def cmd_parse(args, src):
    cst = parse_cst(src)
    ast = build_ast(cst)
    tree = viz.from_cst(cst) if args.kind == "cst" else viz.from_ast(ast)
    fmt = "json" if args.json else args.format
    if fmt == "json":
        if args.kind == "cst":
            _dump({"ok": True, "kind": "cst", "tree": viz.to_dict(tree)})
        else:
            _dump({"ok": True, "kind": "ast", "ast": ast.to_dict()})
    elif fmt == "dot":
        print(viz.to_dot(tree))
    elif fmt == "svg":
        print(viz.to_svg(tree))
    else:
        print(viz.to_text(tree))
    return EXIT_OK


def cmd_check(args, src):
    build_ast(parse_cst(src))
    if args.json:
        _dump({"ok": True, "diagnostics": []})
    else:
        print("OK")
    return EXIT_OK


def _fail_runtime(args, e):
    if args.json:
        _dump({"ok": False, "diagnostics": [e.diagnostic.to_dict()]})
    else:
        print(e.diagnostic.format(args.file), file=sys.stderr)
    return EXIT_RUNTIME


def cmd_run(args, src):
    program = build_ast(parse_cst(src))
    try:
        res = Interpreter(args.max_steps).run(program, args.state)
    except SiplRuntimeError as e:
        return _fail_runtime(args, e)
    if args.json:
        _dump({"ok": True, "state": res.state, "steps": res.steps, "diagnostics": []})
    else:
        for k in sorted(res.state):
            print(f"{k} = {res.state[k]}")
    return EXIT_OK


def cmd_trace(args, src):
    program = build_ast(parse_cst(src))
    events, _, err = trace(program, args.state, args.max_steps)
    if args.json:
        _dump({
            "ok": err is None,
            "events": [e.to_dict() for e in events],
            "diagnostics": [err.diagnostic.to_dict()] if err else [],
        })
    else:
        for e in events:
            print(e)
        if err:
            print(err.diagnostic.format(args.file), file=sys.stderr)
    return EXIT_RUNTIME if err else EXIT_OK


def cmd_semantics(args, src):
    term = build_term(build_ast(parse_cst(src)))
    if args.json:
        _dump({"ok": True, "term": render(term), "tree": term.to_dict()})
    else:
        print(render(term))
    return EXIT_OK


def cmd_compare(args, src):
    cst = parse_cst(src)
    page = viz.compare_html(src, viz.from_cst(cst), viz.from_ast(build_ast(cst)))
    if args.output:
        Path(args.output).write_text(page, encoding="utf-8")
    else:
        print(page)
    return EXIT_OK


def build_arg_parser():
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("file", help="файл .sipl або '-' для stdin")
    common.add_argument("--json", action="store_true", help="структурований JSON-вивід")

    runtime = argparse.ArgumentParser(add_help=False)
    runtime.add_argument("--var", action="append", metavar="NAME=N", help="початкове значення змінної")
    runtime.add_argument("--max-steps", type=int, default=100_000)

    p = argparse.ArgumentParser(prog="sipl", description="SIPL Language Toolkit")
    sub = p.add_subparsers(dest="cmd", required=True)

    sp = sub.add_parser("parse", parents=[common])
    sp.add_argument("--kind", choices=["cst", "ast"], default="ast")
    sp.add_argument("--format", choices=["text", "json", "dot", "svg"], default="text")
    sp.set_defaults(func=cmd_parse)

    sub.add_parser("check", parents=[common]).set_defaults(func=cmd_check)
    sub.add_parser("run", parents=[common, runtime]).set_defaults(func=cmd_run)
    sub.add_parser("trace", parents=[common, runtime]).set_defaults(func=cmd_trace)
    sub.add_parser("semantics", parents=[common]).set_defaults(func=cmd_semantics)

    sc = sub.add_parser("compare", parents=[common])
    sc.add_argument("-o", "--output")
    sc.set_defaults(func=cmd_compare)
    return p


def main(argv=None) -> int:
    args = build_arg_parser().parse_args(argv)
    try:
        src = _read(args.file)
        args.state = _parse_vars(getattr(args, "var", None))
    except (OSError, ValueError) as e:
        print(f"sipl: {e}", file=sys.stderr)
        return EXIT_USAGE
    try:
        return args.func(args, src)
    except SiplSyntaxError as e:
        if args.json:
            _dump({"ok": False, "diagnostics": [e.diagnostic.to_dict()]})
        else:
            print(e.diagnostic.format(args.file), file=sys.stderr)
        return EXIT_SYNTAX
