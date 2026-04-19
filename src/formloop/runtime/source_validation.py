"""Static validation for agent-authored CAD source."""

from __future__ import annotations

import ast
from dataclasses import dataclass

ALLOWED_IMPORTS = {
    "build123d",
    "math",
    "typing",
}

BANNED_CALLS = {
    "eval",
    "exec",
    "compile",
    "open",
    "__import__",
    "input",
}

BANNED_KEYWORDS = {
    "centered",
    "pos",
}

BANNED_NAMES = {
    "os",
    "sys",
    "subprocess",
    "socket",
    "pathlib",
    "shutil",
    "requests",
}


@dataclass(slots=True)
class ValidationResult:
    ok: bool
    errors: list[str]


class _SourceValidator(ast.NodeVisitor):
    def __init__(self) -> None:
        self.errors: list[str] = []

    def visit_Import(self, node: ast.Import) -> None:
        for alias in node.names:
            root_name = alias.name.split(".", 1)[0]
            if root_name not in ALLOWED_IMPORTS:
                self.errors.append(f"import {alias.name!r} is not allowed")
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        module = (node.module or "").split(".", 1)[0]
        if module not in ALLOWED_IMPORTS:
            self.errors.append(f"from {node.module!r} import ... is not allowed")
        self.generic_visit(node)

    def visit_Call(self, node: ast.Call) -> None:
        if isinstance(node.func, ast.Name) and node.func.id in BANNED_CALLS:
            self.errors.append(f"call to banned builtin {node.func.id!r}")
        if isinstance(node.func, ast.Attribute) and isinstance(node.func.value, ast.Name):
            if node.func.value.id in BANNED_NAMES:
                self.errors.append(
                    f"call via banned module {node.func.value.id!r}.{node.func.attr}"
                )
        for keyword in node.keywords:
            if keyword.arg in BANNED_KEYWORDS:
                self.errors.append(
                    f"keyword argument {keyword.arg!r} is not allowed; "
                    "use explicit Pos(...) placement instead"
                )
        self.generic_visit(node)

    def visit_Name(self, node: ast.Name) -> None:
        if node.id in BANNED_NAMES:
            self.errors.append(f"banned name {node.id!r} is not allowed")
        self.generic_visit(node)


def validate_cad_source(source_code: str) -> ValidationResult:
    """Apply a small AST-based allowlist for model authoring."""
    # Req: FLH-D-004, FLH-NF-001, FLH-NF-005, FLH-V-001
    try:
        tree = ast.parse(source_code)
    except SyntaxError as exc:
        return ValidationResult(ok=False, errors=[f"syntax error: {exc.msg}"])
    validator = _SourceValidator()
    validator.visit(tree)
    has_build_model = any(
        isinstance(node, ast.FunctionDef) and node.name == "build_model" for node in tree.body
    )
    if not has_build_model:
        validator.errors.append("source must define build_model(params, context)")
    return ValidationResult(ok=not validator.errors, errors=validator.errors)
