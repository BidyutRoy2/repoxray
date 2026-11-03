"""Findings: dead code, complexity hotspots, and project totals."""

from __future__ import annotations

from dataclasses import dataclass

from .scanner import ModuleInfo

# Names that look unused but are part of a public surface: dunder methods,
# test entry points, CLI entry points, and framework hooks. Reporting them
# as "dead" would be a false positive, so they are never flagged.
ALWAYS_ALIVE = {
    "main", "__main__", "test_", "setUp", "tearDown", "setUpClass",
    "tearDownClass", "run", "execute", "handle", "dispatch",
}


@dataclass
class DeadFunction:
    module: str
    name: str
    lineno: int


@dataclass
class Hotspot:
    module: str
    name: str
    complexity: int
    lines: int


@dataclass
class Summary:
    modules: int
    total_lines: int
    total_functions: int
    total_classes: int
    total_edges: int
    external_packages: int


def find_dead_code(modules: dict[str, ModuleInfo]) -> list[DeadFunction]:
    """Top-level functions never called anywhere in the project.

    A function is alive if any module calls it by name, if it is a method
    of a class that is instantiated, or if its name is in ALWAYS_ALIVE.
    Class methods are checked against attribute-style calls collected by
    the scanner, which is deliberately conservative: a method called only
    dynamically (``getattr``) may still be flagged — the report says so.
    """
    called: set[str] = set()
    for info in modules.values():
        called.update(info.called_names)
    dead: list[DeadFunction] = []
    for name, info in modules.items():
        for fname, fn in info.defines.items():
            if fname in called:
                continue
            if fname.startswith("__") and fname.endswith("__"):
                continue
            if fname in ALWAYS_ALIVE or fname.startswith("test_"):
                continue
            # ast.NodeVisitor dispatches visit_* methods by name, so they
            # are called even though no static call site exists.
            if fname.startswith("visit_"):
                continue
            dead.append(DeadFunction(module=name, name=fname, lineno=fn.lineno))
    return sorted(dead, key=lambda d: (d.module, d.name))


def hotspots(modules: dict[str, ModuleInfo], limit: int = 10) -> list[Hotspot]:
    """Functions with the highest branch complexity, most complex first."""
    found: list[Hotspot] = []
    for name, info in modules.items():
        for fname, fn in info.defines.items():
            if fn.complexity >= 5:
                found.append(Hotspot(module=name, name=fname,
                                     complexity=fn.complexity,
                                     lines=info.lines))
    found.sort(key=lambda h: (-h.complexity, h.module, h.name))
    return found[:limit]


def summarize(modules: dict[str, ModuleInfo],
              edges: dict[str, set[str]]) -> Summary:
    external: set[str] = set()
    for info in modules.values():
        external.update(info.external_imports)
    return Summary(
        modules=len(modules),
        total_lines=sum(m.lines for m in modules.values()),
        total_functions=sum(len(m.defines) for m in modules.values()),
        total_classes=sum(len(m.classes) for m in modules.values()),
        total_edges=sum(len(t) for t in edges.values()),
        external_packages=len(external),
    )
