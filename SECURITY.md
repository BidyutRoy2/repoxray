# Security policy

## What repoxray does with your code

repoxray runs entirely on your machine, has zero dependencies, and makes
no network requests. It reads your source files to build its map and writes
only the report files you ask for. It never uploads, transmits, or stores
your code anywhere else.

## Reporting a vulnerability

If you find a security issue in repoxray itself (for example, a path
handling flaw that could read files outside the scanned directory), please
open a GitHub issue describing it. Since the tool only reads files under
the directory you point it at and writes reports you request, the attack
surface is intentionally small — but reports are still welcome and will be
addressed promptly.

## Supported versions

| Version | Supported |
|---|---|
| 0.1.x | ✅ |
