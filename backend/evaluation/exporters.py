"""
Result Exporters for Evaluation.

Supports CSV, JSON, Markdown, and LaTeX export formats.
All exports are UTF-8 encoded and Excel-compatible.

Do not commit large generated result directories.
"""

import csv
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union


class LaTeXEscaper:
    """Escape LaTeX special characters in text."""

    _replacements = {
        "&": "\\&",
        "%": "\\%",
        "$": "\\$",
        "#": "\\#",
        "_": "\\_",
        "{": "\\{",
        "}": "\\}",
        "~": "\\textasciitilde{}",
        "^": "\\textasciicircum{}",
        "\\": "\\textbackslash{}",
    }

    @classmethod
    def escape(cls, text: str) -> str:
        if not isinstance(text, str):
            text = str(text)
        for char, escaped in cls._replacements.items():
            text = text.replace(char, escaped)
        return text


def export_json(data: Any, output_path: Path) -> None:
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False, default=str)


def export_jsonl(data: List[Dict[str, Any]], output_path: Path) -> None:
    with open(output_path, "w", encoding="utf-8") as f:
        for item in data:
            f.write(json.dumps(item, ensure_ascii=False, default=str) + "\n")


def export_csv(results: List[Dict[str, Any]], output_path: Path) -> None:
    if not results:
        with open(output_path, "w", newline="", encoding="utf-8") as f:
            pass
        return

    fieldnames = list(results[0].keys())
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for row in results:
            safe_row = {k: (_na_to_empty(v) if v is not None else "") for k, v in row.items()}
            writer.writerow(safe_row)


def export_markdown_table(
    headers: List[str],
    rows: List[List[Any]],
    output_path: Path,
    title: Optional[str] = None,
) -> None:
    lines = []
    if title:
        lines.append(f"# {title}\n")

    col_count = len(headers)
    lines.append("| " + " | ".join(str(h) for h in headers) + " |")
    lines.append("|" + "|".join([" --- " for _ in range(col_count)]) + "|")

    for row in rows:
        formatted = []
        for cell in row:
            if cell is None:
                formatted.append("N/A")
            elif isinstance(cell, float):
                formatted.append(f"{cell:.4f}")
            else:
                formatted.append(str(cell))
        lines.append("| " + " | ".join(formatted) + " |")

    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


def _na_to_empty(v: Any) -> str:
    if v is None:
        return ""
    if isinstance(v, (int, float)):
        return v
    return str(v)


def export_latex_table(
    headers: List[str],
    rows: List[List[Any]],
    output_path: Path,
    caption: str = "",
    label: str = "",
    booktabs: bool = True,
) -> None:
    escaped_headers = [LaTeXEscaper.escape(str(h)) for h in headers]
    escaped_rows = []
    for row in rows:
        escaped_row = []
        for cell in row:
            if cell is None:
                escaped_row.append("N/A")
            elif isinstance(cell, float):
                escaped_row.append(f"{cell:.2f}")
            else:
                escaped_row.append(LaTeXEscaper.escape(str(cell)))
        escaped_rows.append(escaped_row)

    lines = ["\\begin{table}[h]", "\\centering"]

    if caption:
        lines.append(f"\\caption{{{LaTeXEscaper.escape(caption)}}}")
    if label:
        lines.append(f"\\label{{{LaTeXEscaper.escape(label)}}}")

    if booktabs:
        lines.append("\\begin{tabular}{|" + "c|" * len(headers) + "}")
        lines.append("\\hline")
        lines.append(" & ".join(escaped_headers) + " \\\\")
        lines.append("\\hline")
        for row in escaped_rows:
            lines.append(" & ".join(row) + " \\\\")
        lines.append("\\hline")
        lines.append("\\end{tabular}")
    else:
        lines.append("\\begin{tabular}{|" + "c|" * len(headers) + "}")
        lines.append("\\hline")
        lines.append(" & ".join(escaped_headers) + " \\\\")
        lines.append("\\hline")
        for row in escaped_rows:
            lines.append(" & ".join(row) + " \\\\")
        lines.append("\\hline")
        lines.append("\\end{tabular}")

    lines.append("\\end{table}")

    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


def format_value(value: Any, fmt: str = "auto") -> str:
    if value is None:
        return "N/A"
    if fmt == "pct":
        return f"{value:.1f}\\%"
    if fmt == "km":
        return f"{value:.2f} km"
    if fmt == "ms":
        return f"{value:.2f} ms"
    if isinstance(value, float):
        return f"{value:.4f}"
    return str(value)


def export_rescue_comparison(
    results: List[Dict[str, Any]],
    output_dir: Path,
) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)

    export_json(results, output_dir / "rescue_comparison.json")
    export_csv(results, output_dir / "rescue_comparison.csv")

    headers = ["Algorithm", "Scenario", "Success", "Distance (km)", "Skill Match (%)",
               "Equipment Match (%)", "Latency (ms)", "Failure Reason"]
    rows = []
    for r in results:
        rows.append([
            r.get("algorithm", ""),
            r.get("scenario_id", ""),
            "Yes" if r.get("success") else "No",
            r.get("distance_km", 0),
            r.get("skill_match_pct", 0),
            r.get("equipment_match_pct", 0),
            r.get("computation_time_ms", 0),
            r.get("failure_reason", "") or "",
        ])

    export_markdown_table(headers, rows, output_dir / "rescue_comparison.md")
    export_latex_table(headers, rows, output_dir / "rescue_comparison.tex",
                        caption="Rescue Allocation Comparison", label="tab:rescue-comparison")


def export_relief_comparison(
    results: List[Dict[str, Any]],
    output_dir: Path,
) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)

    export_json(results, output_dir / "relief_comparison.json")
    export_csv(results, output_dir / "relief_comparison.csv")

    headers = ["Algorithm", "Scenario", "Success", "Fulfilment (%)", "Shortage",
               "Warehouses", "Distance (km)", "Latency (ms)"]
    rows = []
    for r in results:
        rows.append([
            r.get("algorithm", ""),
            r.get("scenario_id", ""),
            "Yes" if r.get("success") else "No",
            r.get("fulfilment_pct", 0),
            r.get("shortage", 0),
            len(r.get("warehouses_used", [])),
            r.get("distance_km", 0),
            r.get("computation_time_ms", 0),
        ])

    export_markdown_table(headers, rows, output_dir / "relief_comparison.md")
    export_latex_table(headers, rows, output_dir / "relief_comparison.tex",
                        caption="Relief Allocation Comparison", label="tab:relief-comparison")


def export_shelter_comparison(
    results: List[Dict[str, Any]],
    output_dir: Path,
) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)

    export_json(results, output_dir / "shelter_comparison.json")
    export_csv(results, output_dir / "shelter_comparison.csv")

    headers = ["Algorithm", "Scenario", "Success", "Admitted", "Projected Occ",
               "Uncovered", "Overcrowding", "Latency (ms)"]
    rows = []
    for r in results:
        rows.append([
            r.get("algorithm", ""),
            r.get("scenario_id", ""),
            "Yes" if r.get("success") else "No",
            r.get("admitted_count", 0),
            r.get("projected_occupancy", 0),
            r.get("uncovered_population", 0),
            "Yes" if r.get("overcrowding_risk") else "No",
            r.get("computation_time_ms", 0),
        ])

    export_markdown_table(headers, rows, output_dir / "shelter_comparison.md")
    export_latex_table(headers, rows, output_dir / "shelter_comparison.tex",
                        caption="Shelter Allocation Comparison", label="tab:shelter-comparison")


def export_experiment_metadata(
    metadata: Dict[str, Any],
    output_dir: Path,
) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    export_json(metadata, output_dir / "experiment_metadata.json")