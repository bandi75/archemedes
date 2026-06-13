from __future__ import annotations

import argparse
import html
import json
import re
from pathlib import Path


DIAGRAM_FIELDS = (
    ("system_context_diagram", "System Context"),
    ("container_diagram", "Container"),
    ("data_flow_diagram", "Data Flow"),
    ("network_topology_diagram", "Network Topology"),
)


def sanitize_mermaid(diagram: str) -> str:
    """Fix common LLM Mermaid generation errors before browser rendering."""
    lines = diagram.splitlines()
    output: list[str] = []
    for line in lines:
        line = re.sub(r"\bBoundedContext\(", "Boundary(", line)

        def clean_subgraph_label(match: re.Match[str]) -> str:
            return match.group(0).replace("(", "- ").replace(")", "")

        line = re.sub(r"subgraph\s+\w+\s+\[.*?\]", clean_subgraph_label, line)

        if "-->" not in line and "---" not in line:
            split = re.split(r"(?<=\])\s{2,}(?=\w+[\[({])", line)
            if len(split) > 1:
                indent = len(line) - len(line.lstrip())
                prefix = " " * indent
                output.extend(prefix + item.strip() for item in split)
                continue

        output.append(line)
    return "\n".join(output)


def c4_flowchart_fallback(diagram: str) -> str | None:
    """Convert simple C4Context/C4Container diagrams into renderable flowcharts."""
    stripped = diagram.strip()
    if not stripped.startswith(("C4Context", "C4Container")):
        return None

    nodes: dict[str, tuple[str, str]] = {}
    edges: list[tuple[str, str, str, bool]] = []
    node_pattern = re.compile(
        r'^\s*(Person|SystemDb|System|ContainerDb|ContainerQueue|Container|Boundary)\(\s*([^,\s]+)\s*,\s*"([^"]+)"'
    )
    rel_pattern = re.compile(r'^\s*(BiRel|Rel)\(\s*([^,\s]+)\s*,\s*([^,\s]+)\s*,\s*"([^"]*)"')

    def safe_id(value: str) -> str:
        safe = re.sub(r"\W+", "_", value.strip())
        return safe or "node"

    def safe_label(value: str) -> str:
        return (
            value.replace('"', "'")
            .replace("[", "(")
            .replace("]", ")")
            .replace("|", "-")
            .replace("\n", " ")
        )

    for line in stripped.splitlines():
        node_match = node_pattern.match(line)
        if node_match:
            kind, alias, label = node_match.groups()
            nodes[alias] = (kind, label)
            continue

        rel_match = rel_pattern.match(line)
        if rel_match:
            kind, source, target, label = rel_match.groups()
            edges.append((source, target, label, kind == "BiRel"))

    if not nodes:
        return None

    output = ["flowchart TB"]
    for alias, (kind, label) in nodes.items():
        node_id = safe_id(alias)
        node_label = safe_label(label)
        output.append(f'  {node_id}["{node_label}"]')

    for source, target, label, bidirectional in edges:
        source_id = safe_id(source)
        target_id = safe_id(target)
        edge_label = safe_label(label)
        arrow = "<-->" if bidirectional else "-->"
        if edge_label:
            output.append(f"  {source_id} {arrow}|{edge_label}| {target_id}")
        else:
            output.append(f"  {source_id} {arrow} {target_id}")

    return "\n".join(output)


def extract_hld_content(payload: dict) -> dict:
    content = payload.get("content") if isinstance(payload.get("content"), dict) else payload
    return content if isinstance(content, dict) else {}


def render_report(payload: dict, *, native_first: bool = False) -> str:
    content = extract_hld_content(payload)
    cards: list[str] = []
    render_cases: list[dict[str, str | None]] = []

    for index, (field, title) in enumerate(DIAGRAM_FIELDS, start=1):
        raw = content.get(field)
        if not isinstance(raw, str) or not raw.strip():
            cards.append(
                f"""
                <section class="card missing">
                  <h2>{html.escape(title)}</h2>
                  <p>No diagram field found for <code>{html.escape(field)}</code>.</p>
                </section>
                """
            )
            continue

        sanitized = sanitize_mermaid(raw)
        fallback = c4_flowchart_fallback(sanitized)
        case_id = f"diagram-{index}"
        render_cases.append(
            {
                "id": case_id,
                "title": title,
                "source": sanitized,
                "fallback": fallback,
                "prefer_fallback": bool(fallback and not native_first),
            }
        )
        fallback_block = (
            f"""
            <details>
              <summary>Fallback source</summary>
              <pre>{html.escape(fallback)}</pre>
            </details>
            """
            if fallback
            else ""
        )
        cards.append(
            f"""
            <section class="card">
              <div class="card-head">
                <h2>{html.escape(title)}</h2>
                <span id="{case_id}-status" class="status pending">Pending</span>
              </div>
              <div id="{case_id}-note" class="note"></div>
              <div id="{case_id}-render" class="diagram"></div>
              <details>
                <summary>Original source</summary>
                <pre>{html.escape(sanitized)}</pre>
              </details>
              {fallback_block}
            </section>
            """
        )

    cases_json = json.dumps(render_cases)
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>HLD Mermaid Rendering Check</title>
  <style>
    body {{ font-family: Segoe UI, Arial, sans-serif; margin: 24px; color: #182033; background: #f6f7f9; }}
    h1 {{ margin: 0 0 4px; }}
    .subtle {{ color: #687083; margin: 0 0 24px; }}
    .card {{ background: #fff; border: 1px solid #d8dde7; border-radius: 8px; margin: 18px 0; padding: 18px; }}
    .card-head {{ display: flex; justify-content: space-between; gap: 12px; align-items: center; }}
    .card h2 {{ margin: 0 0 12px; }}
    .status {{ border-radius: 999px; padding: 4px 10px; font-size: 12px; }}
    .pending {{ background: #eef1f6; color: #485268; }}
    .ok {{ background: #e7f6ed; color: #116a37; }}
    .fallback {{ background: #eef6ff; color: #1f4e79; }}
    .error {{ background: #fff3cd; color: #7a4b00; }}
    .note {{ display: none; margin: 8px 0 12px; padding: 8px 10px; border-radius: 6px; background: #eef6ff; color: #1f4e79; }}
    .diagram {{ min-height: 60px; overflow: auto; padding: 8px; }}
    details {{ margin-top: 12px; }}
    pre {{ white-space: pre-wrap; background: #101827; color: #e8edf7; padding: 12px; border-radius: 6px; overflow: auto; }}
  </style>
</head>
<body>
  <h1>HLD Mermaid Rendering Check</h1>
  <p class="subtle">C4 diagrams use generated flowchart rendering by default because native C4 output can be cramped or unstable. Use <code>--native-first</code> to compare native C4 rendering.</p>
  {"".join(cards)}
  <script type="module">
    import mermaid from 'https://cdn.jsdelivr.net/npm/mermaid@11/dist/mermaid.esm.min.mjs';
    mermaid.initialize({{ startOnLoad: false, securityLevel: 'loose', theme: 'default' }});
    const cases = {cases_json};
    async function renderDiagram(targetId, source) {{
      const result = await mermaid.render(targetId + '-svg-' + Math.random().toString(16).slice(2), source);
      document.getElementById(targetId + '-render').innerHTML = result.svg;
    }}
    for (const item of cases) {{
      const status = document.getElementById(item.id + '-status');
      const note = document.getElementById(item.id + '-note');
      try {{
        if (item.prefer_fallback && item.fallback) {{
          await renderDiagram(item.id, item.fallback);
          status.className = 'status fallback';
          status.textContent = 'Fallback Preferred';
          note.style.display = 'block';
          note.textContent = 'Using generated flowchart fallback for readability. Native C4 source is still shown below.';
          continue;
        }}
        await new Promise((resolve) => requestAnimationFrame(resolve));
        await renderDiagram(item.id, item.source);
        status.className = 'status ok';
        status.textContent = 'Native OK';
      }} catch (err) {{
        if (item.fallback) {{
          try {{
            await renderDiagram(item.id, item.fallback);
            status.className = 'status fallback';
            status.textContent = 'Fallback OK';
            note.style.display = 'block';
            note.textContent = 'Native render failed: ' + err.message;
          }} catch (fallbackErr) {{
            status.className = 'status error';
            status.textContent = 'Failed';
            note.style.display = 'block';
            note.textContent = 'Native render failed: ' + err.message + ' | Fallback failed: ' + fallbackErr.message;
          }}
        }} else {{
          status.className = 'status error';
          status.textContent = 'Failed';
          note.style.display = 'block';
          note.textContent = err.message;
        }}
      }}
    }}
  </script>
</body>
</html>
"""


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate a standalone HLD Mermaid rendering report.")
    parser.add_argument("input", type=Path, help="Path to HLD artifact JSON, either full artifact or content object.")
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=Path("tmp/hld_render_check.html"),
        help="Output HTML report path. Defaults to tmp/hld_render_check.html.",
    )
    parser.add_argument(
        "--native-first",
        action="store_true",
        help="Try native Mermaid rendering before C4 fallback. Defaults to preferring C4 fallback for readability.",
    )
    args = parser.parse_args()

    payload = json.loads(args.input.read_text(encoding="utf-8"))
    report = render_report(payload, native_first=args.native_first)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(report, encoding="utf-8")

    content = extract_hld_content(payload)
    print(f"Wrote {args.output}")
    for field, title in DIAGRAM_FIELDS:
        diagram = content.get(field)
        if not isinstance(diagram, str) or not diagram.strip():
            print(f"- {title}: missing")
            continue
        fallback = c4_flowchart_fallback(sanitize_mermaid(diagram))
        mode = "native-first" if args.native_first or not fallback else "fallback-preferred"
        print(f"- {title}: {mode}, fallback={'yes' if fallback else 'no'}")


if __name__ == "__main__":
    main()
