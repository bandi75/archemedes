from __future__ import annotations

from datetime import UTC, datetime


def format_adr_markdown(
    *,
    adr_id: str,
    title: str,
    status: str,
    context: str,
    decision: str,
    consequences: str,
    alternatives: list[dict[str, str]] | None = None,
    references: list[str] | None = None,
) -> str:
    ts = datetime.now(UTC).strftime("%Y-%m-%d")
    alt_lines = _alternatives_section(alternatives or [])
    ref_lines = _references_section(references or [])

    return "\n".join(
        [
            f"# ADR-{adr_id}: {title}",
            "",
            f"- Status: {status}",
            f"- Date: {ts}",
            "",
            "## Context",
            context.strip(),
            "",
            "## Decision",
            decision.strip(),
            "",
            "## Consequences",
            consequences.strip(),
            "",
            "## Alternatives Considered",
            alt_lines,
            "",
            "## References",
            ref_lines,
            "",
        ]
    )


def _alternatives_section(alternatives: list[dict[str, str]]) -> str:
    if not alternatives:
        return "- None documented"

    lines: list[str] = []
    for item in alternatives:
        option = item.get("option", "Unknown option")
        pros = item.get("pros", "")
        cons = item.get("cons", "")
        lines.append(f"- {option}")
        if pros:
            lines.append(f"  - Pros: {pros}")
        if cons:
            lines.append(f"  - Cons: {cons}")
    return "\n".join(lines)


def _references_section(references: list[str]) -> str:
    if not references:
        return "- None"
    return "\n".join(f"- {ref}" for ref in references)
