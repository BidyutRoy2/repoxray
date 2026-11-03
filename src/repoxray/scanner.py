"""Walk a project tree and parse Python sources into module records.

Zero third-party dependencies: everything is built on :mod:`ast` and the
standard library, so the tool runs anywhere Python 3.10+ runs.

Design notes
------------
* Only ``.py`` files are parsed. Everything else is counted, not analysed,
  so a mixed-language repo still gets an honest report instead of a crash.
* Directories that never contain project code (``.git``, virtualenvs,
  ``__pycache__``, ``node_modules``, ``.venv``) are skipped.
* Imports are resolved to *project-internal* module names when possible;
  third-party and stdlib imports are recorded separately and never drawn
  as internal edges, which keeps the graph truthful.
"""

from __future__ import annotations

import ast
import os
from dataclasses import dataclass, field

SKIP_DIRS = {
    ".git", "__pycache__", ".venv", "venv", "env", ".tox",
    "node_modules", ".mypy_cache", ".pytest_cache", "dist", "build",
    ".eggs", "site-packages",
}

SKIP_FILES = {"setup.py"}  # packaging shims add noise, not architecture


@dataclass
class FunctionInfo:
    """One top-level function or method found in a module."""

    name: str
    lineno: int
    complexity: int = 1  # cyclomatic-ish: 1 + one per branch keyword
    calls: set[str] = field(default_factory=set)


@dataclass
class ModuleInfo:
    """Everything repoxray knows about one Python file."""

    path: str               # path relative to the scanned root
    module: str             # dotted name, e.g. ``core.engine``
    lines: int
    defines: dict[str, FunctionInfo] = field(default_factory=dict)
    classes: list[str] = field(default_factory=list)
    imports: set[str] = field(default_factory=set)       # internal dotted names
    external_imports: set[str] = field(default_factory=set)
    called_names: set[str] = field(default_factory=set)
    has_main_guard: bool = False
    parse_error: str | None = None


def module_name(root: str, filepath: str) -> str:
    """Turn ``<root>/core/engine.py`` into ``core.engine``."""
    rel = os.path.relpath(filepath, root)
    if rel.endswith(".py"):
        rel = rel[:-3]
    parts = [p for p in rel.split(os.sep) if p not in (".",)]
    if parts and parts[-1] == "__init__":
        parts = parts[:-1]
    return ".".join(parts)


def _resolve_relative(current: str, level: int, name: str | None) -> str:
    """Resolve a relative import (``from .x import y``) to a dotted name."""
    parts = current.split(".") if current else []
    # ``current`` is the module itself, so level 1 means "this package".
    base = parts[:-1] if level == 1 else parts[: -(level)] if level <= len(parts) else []
    if name:
        return ".".join(base + [name])
    return ".".join(base)


class _Visitor(ast.NodeVisitor):
    """Collect definitions, calls and imports from one parsed module."""

    def __init__(self, module: str) -> None:
        self.module = module
        self.defines: dict[str, FunctionInfo] = {}
        self.classes: list[str] = []
        self.imports: set[str] = set()
        self.external: set[str] = set()
        self.called: set[str] = set()
        self.has_main_guard = False
        self._current: FunctionInfo | None = None

    # -- definitions -----------------------------------------------------
    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        fn = FunctionInfo(name=node.name, lineno=node.lineno)
        self.defines[node.name] = fn
        prev = self._current
        self._current = fn
        self.generic_visit(node)
        self._current = prev

    visit_AsyncFunctionDef = visit_FunctionDef

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        self.classes.append(node.name)
        self.generic_visit(node)

    # -- branches (complexity) -------------------------------------------
    # Named visit_branch (not _branch) so dead-code detection, which
    # excludes visit_* methods dispatched dynamically by ast, is correct.
    def visit_branch(self, node: ast.AST) -> None:
        if self._current is not None:
            self._current.complexity += 1
        self.generic_visit(node)

    visit_If = visit_branch
    visit_For = visit_branch
    visit_While = visit_branch
    visit_ExceptHandler = visit_branch
    visit_With = visit_branch

    def visit_BoolOp(self, node: ast.BoolOp) -> None:
        if self._current is not None:
            self._current.complexity += max(0, len(node.values) - 1)
        self.generic_visit(node)

    def visit_Compare(self, node: ast.Compare) -> None:
        # ``if __name__ == "__main__"`` is a guard, not a hotspot.
        if (
            isinstance(node.left, ast.Name)
            and node.left.id == "__name__"
            and any(
                isinstance(c, ast.Constant) and c.value == "__main__"
                for c in node.comparators
            )
        ):
            self.has_main_guard = True
        self.generic_visit(node)

    # -- calls ------------------------------------------------------------
    def visit_Call(self, node: ast.Call) -> None:
        func = node.func
        if isinstance(func, ast.Name):
            self.called.add(func.id)
            if self._current is not None:
                self._current.calls.add(func.id)
        elif isinstance(func, ast.Attribute):
            self.called.add(func.attr)
            if self._current is not None:
                self._current.calls.add(func.attr)
        self.generic_visit(node)

    # -- imports ----------------------------------------------------------
    def visit_Import(self, node: ast.Import) -> None:
        for alias in node.names:
            self.imports.add(alias.name.split(".")[0])
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        if node.level and node.level > 0:
            resolved = _resolve_relative(self.module, node.level, node.module)
            if resolved:
                self.imports.add(resolved)
        elif node.module:
            self.imports.add(node.module)
        self.generic_visit(node)


def scan_file(root: str, filepath: str) -> ModuleInfo:
    """Parse one file. A syntax error is recorded, never raised."""
    rel = os.path.relpath(filepath, root)
    mod = module_name(root, filepath)
    try:
        with open(filepath, encoding="utf-8", errors="replace") as fh:
            source = fh.read()
    except OSError as exc:
        return ModuleInfo(path=rel, module=mod, lines=0, parse_error=str(exc))
    lines = source.count("\n") + (0 if source.endswith("\n") or not source else 1)
    try:
        tree = ast.parse(source, filename=rel)
    except SyntaxError as exc:
        return ModuleInfo(path=rel, module=mod, lines=lines,
                          parse_error=f"{exc.msg} (line {exc.lineno})")
    visitor = _Visitor(mod)
    visitor.visit(tree)
    return ModuleInfo(
        path=rel, module=mod, lines=lines, defines=visitor.defines,
        classes=visitor.classes, imports=visitor.imports,
        external_imports=set(), called_names=visitor.called,
        has_main_guard=visitor.has_main_guard,
    )


def scan_project(root: str) -> tuple[dict[str, ModuleInfo], dict[str, int]]:
    """Scan ``root`` and return ``(modules, file_counts)``.

    After the first pass, raw import names are split into internal edges
    (they match a scanned module or one of its parents) and external
    imports (stdlib / third-party). This two-pass design is what makes
    ``from core import engine`` and ``from . import utils`` both resolve.
    """
    modules: dict[str, ModuleInfo] = {}
    counts = {"python_files": 0, "other_files": 0, "parse_errors": 0}
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = sorted(d for d in dirnames if d not in SKIP_DIRS)
        for filename in sorted(filenames):
            if filename in SKIP_FILES:
                continue
            full = os.path.join(dirpath, filename)
            if filename.endswith(".py"):
                info = scan_file(root, full)
                modules[info.module] = info
                counts["python_files"] += 1
                if info.parse_error:
                    counts["parse_errors"] += 1
            else:
                counts["other_files"] += 1

    known = set(modules)
    for info in modules.values():
        internal: set[str] = set()
        external: set[str] = set()
        for imp in info.imports:
            # Exact match, or the longest known prefix (``core.engine`` for
            # ``core.engine.helper`` style imports of a submodule member).
            match = None
            candidate = imp
            while candidate:
                if candidate in known:
                    match = candidate
                    break
                candidate = candidate.rsplit(".", 1)[0] if "." in candidate else ""
            if match and match != info.module:
                internal.add(match)
            else:
                external.add(imp.split(".")[0])
        info.imports = internal
        info.external_imports = external
    return modules, counts
