"""Architecture graph: edges, cycles, entry points, orphans, layers."""

from __future__ import annotations

from .scanner import ModuleInfo


def build_edges(modules: dict[str, ModuleInfo]) -> dict[str, set[str]]:
    """Internal import edges: ``{importer: {imported, ...}}``."""
    return {name: set(info.imports) & set(modules) for name, info in modules.items()}


def find_cycles(edges: dict[str, set[str]]) -> list[list[str]]:
    """All simple import cycles, each reported once, in discovery order."""
    cycles: list[list[str]] = []
    seen: set[tuple[str, ...]] = set()
    stack: list[str] = []
    on_stack: set[str] = set()

    def dfs(node: str) -> None:
        stack.append(node)
        on_stack.add(node)
        for nxt in sorted(edges.get(node, ())):
            if nxt in on_stack:
                idx = stack.index(nxt)
                cyc = stack[idx:]
                key = tuple(sorted(cyc))
                if key not in seen:
                    seen.add(key)
                    cycles.append(list(cyc))
            elif nxt not in visited:
                visited.add(nxt)
                dfs(nxt)
        stack.pop()
        on_stack.discard(node)

    visited: set[str] = set()
    for start in sorted(edges):
        if start not in visited:
            visited.add(start)
            dfs(start)
    return cycles


def entry_points(modules: dict[str, ModuleInfo],
                  edges: dict[str, set[str]]) -> list[str]:
    """Modules nothing else imports — plus every ``__main__`` guard module.

    Entry points are where a human (or an agent) should *start* reading.
    """
    imported_by = {name: 0 for name in modules}
    for targets in edges.values():
        for target in targets:
            imported_by[target] = imported_by.get(target, 0) + 1
    entries = [name for name, count in imported_by.items() if count == 0]
    for name, info in modules.items():
        if info.has_main_guard and name not in entries:
            entries.append(name)
    return sorted(entries)


def orphans(modules: dict[str, ModuleInfo],
            edges: dict[str, set[str]]) -> list[str]:
    """Modules with no internal edges in either direction.

    Orphans are usually dead scripts, forgotten experiments, or a package
    that was never wired in. ``__init__`` files are excluded: empty
    ``__init__`` modules are normal, not suspicious.
    """
    imported_by: set[str] = set()
    for targets in edges.values():
        imported_by.update(targets)
    return sorted(
        name for name, info in modules.items()
        if not edges.get(name) and name not in imported_by
        and not info.path.endswith("__init__.py")
    )


def layers(modules: dict[str, ModuleInfo],
           edges: dict[str, set[str]]) -> dict[str, int]:
    """Depth of each module: 0 = entry point, +1 per import hop.

    Depth is computed by longest path from any entry point so that shared
    low-level modules (loggers, config) sink to the bottom, which is
    exactly how the HTML map lays them out.
    """
    depth: dict[str, int] = {name: 0 for name in modules}
    changed = True
    guard = 0
    while changed and guard < len(modules) + 2:
        changed = False
        guard += 1
        for src, targets in edges.items():
            for target in targets:
                if depth[target] < depth[src] + 1:
                    depth[target] = depth[src] + 1
                    changed = True
    return depth
