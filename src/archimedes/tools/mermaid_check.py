from __future__ import annotations

import re
from dataclasses import dataclass, field


_DECLARATIONS = {
    "flowchart": re.compile(r"^\s*flowchart\s+(TB|TD|BT|LR|RL)\b", re.IGNORECASE),
    "sequenceDiagram": re.compile(r"^\s*sequenceDiagram\b", re.IGNORECASE),
    "C4Context": re.compile(r"^\s*C4Context\b", re.IGNORECASE),
    "C4Container": re.compile(r"^\s*C4Container\b", re.IGNORECASE),
}

_ARROWS = ("-->", "---", "-.->", "==>")


@dataclass(slots=True)
class MermaidCheckResult:
    valid: bool
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


def mermaid_render_check(diagram_string: str, diagram_type: str) -> MermaidCheckResult:
    errors: list[str] = []
    warnings: list[str] = []

    if not diagram_string.strip():
        return MermaidCheckResult(valid=False, errors=["Diagram source is empty."])

    decl_regex = _DECLARATIONS.get(diagram_type)
    if decl_regex is None:
        errors.append(f"Unsupported diagram type: {diagram_type}.")
    elif not decl_regex.search(diagram_string):
        errors.append(f"Missing or invalid Mermaid declaration for {diagram_type}.")

    balance_errors = _check_bracket_balance(diagram_string)
    errors.extend(balance_errors)

    node_warnings = _check_duplicate_node_ids(diagram_string)
    warnings.extend(node_warnings)

    if diagram_type in {"flowchart", "C4Context", "C4Container"}:
        arrow_errors = _check_arrows(diagram_string)
        errors.extend(arrow_errors)

    return MermaidCheckResult(valid=not errors, errors=errors, warnings=warnings)


def _check_bracket_balance(diagram_source: str) -> list[str]:
    pairs = {"(": ")", "[": "]", "{": "}"}
    closing = {v: k for k, v in pairs.items()}
    stack: list[str] = []
    errors: list[str] = []

    for char in diagram_source:
        if char in pairs:
            stack.append(char)
        elif char in closing:
            if not stack or stack[-1] != closing[char]:
                errors.append(f"Unbalanced bracket: unexpected '{char}'.")
                continue
            stack.pop()

    if stack:
        errors.append("Unbalanced brackets: missing closing symbols.")
    return errors


def _check_duplicate_node_ids(diagram_source: str) -> list[str]:
    ids = re.findall(r"\b([A-Za-z][A-Za-z0-9_]*)\s*\[", diagram_source)
    duplicates = sorted({node_id for node_id in ids if ids.count(node_id) > 1})
    if not duplicates:
        return []
    return [f"Duplicate node ids found: {', '.join(duplicates)}"]


def _check_arrows(diagram_source: str) -> list[str]:
    errors: list[str] = []
    for line in diagram_source.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("%%"):
            continue
        if "--" in stripped and not any(arrow in stripped for arrow in _ARROWS):
            errors.append(f"Invalid arrow syntax in line: {stripped}")
    return errors
