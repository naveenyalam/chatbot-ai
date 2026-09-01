"""
Data Analysis Service — Real statistical analysis and profiling for CSV/JSON datasets.
Calculates exact row counts, column types, missing values, and numerical summary stats.
"""

import io
import csv
import json
import logging
import math
from typing import Dict, Any, List, Optional

logger = logging.getLogger("nova-ai.services.data_analysis")


def parse_data_content(content: str, filename_or_type: str = "csv") -> List[Dict[str, Any]]:
    """Parse CSV or JSON string into a list of row dictionaries."""
    content_clean = content.strip()
    if not content_clean:
        return []

    # Check if JSON
    if filename_or_type.endswith(".json") or content_clean.startswith("[") or content_clean.startswith("{"):
        try:
            data = json.loads(content_clean)
            if isinstance(data, dict):
                # Handle wrapped JSON like {"data": [...]}
                for key, val in data.items():
                    if isinstance(val, list):
                        data = val
                        break
            if isinstance(data, list) and all(isinstance(row, dict) for row in data):
                return data
        except Exception as json_err:
            logger.debug(f"JSON parse attempt failed: {json_err}")

    # Fallback to CSV parsing
    try:
        reader = csv.DictReader(io.StringIO(content_clean))
        rows = [dict(r) for r in reader if r]
        return rows
    except Exception as csv_err:
        logger.error(f"CSV parse failed: {csv_err}")
        return []


def analyze_dataset(content: str, filename_or_type: str = "csv") -> Dict[str, Any]:
    """
    Perform schema detection, missing value counting, data type inference,
    and exact summary statistics computation on input dataset.
    """
    rows = parse_data_content(content, filename_or_type)
    if not rows:
        return {
            "error": "Unable to parse tabular dataset. Please supply valid CSV or JSON.",
            "row_count": 0,
            "column_count": 0,
            "columns": []
        }

    row_count = len(rows)
    headers = list(rows[0].keys())
    column_count = len(headers)

    column_stats = []

    for col in headers:
        values = [r.get(col) for r in rows]
        null_count = sum(1 for v in values if v is None or str(v).strip() in ("", "null", "none", "nan", "NaN", "N/A"))
        non_null_values = [v for v in values if v is not None and str(v).strip() not in ("", "null", "none", "nan", "NaN", "N/A")]

        # Infer data type
        numeric_values = []
        is_float = False
        for v in non_null_values:
            try:
                num = float(v)
                numeric_values.append(num)
                if "." in str(v):
                    is_float = True
            except (ValueError, TypeError):
                pass

        if len(numeric_values) == len(non_null_values) and len(non_null_values) > 0:
            inferred_type = "float" if is_float else "integer"
        else:
            inferred_type = "string"

        stat_summary: Dict[str, Any] = {
            "name": col,
            "type": inferred_type,
            "total_count": row_count,
            "non_null_count": len(non_null_values),
            "missing_count": null_count,
            "missing_pct": round((null_count / row_count) * 100, 2) if row_count > 0 else 0
        }

        if numeric_values:
            numeric_values.sort()
            n = len(numeric_values)
            min_val = numeric_values[0]
            max_val = numeric_values[-1]
            sum_val = sum(numeric_values)
            mean_val = sum_val / n
            
            # Median
            if n % 2 == 1:
                median_val = numeric_values[n // 2]
            else:
                median_val = (numeric_values[n // 2 - 1] + numeric_values[n // 2]) / 2.0

            # Standard deviation
            variance = sum((x - mean_val) ** 2 for x in numeric_values) / n if n > 0 else 0
            std_dev = math.sqrt(variance)

            stat_summary.update({
                "min": round(min_val, 4),
                "max": round(max_val, 4),
                "mean": round(mean_val, 4),
                "median": round(median_val, 4),
                "std_dev": round(std_dev, 4),
                "sum": round(sum_val, 4)
            })
        else:
            # Categorical stats
            distinct_vals = set(str(v).strip() for v in non_null_values)
            stat_summary["unique_count"] = len(distinct_vals)
            # Find top values
            freq: Dict[str, int] = {}
            for v in non_null_values:
                s = str(v).strip()
                freq[s] = freq.get(s, 0) + 1
            top_sorted = sorted(freq.items(), key=lambda x: x[1], reverse=True)[:5]
            stat_summary["top_values"] = [{"value": k, "count": cnt} for k, cnt in top_sorted]

        column_stats.append(stat_summary)

    sample_rows = rows[:5]

    return {
        "row_count": row_count,
        "column_count": column_count,
        "columns": column_stats,
        "sample_rows": sample_rows
    }


def format_dataset_summary_for_llm(analysis: Dict[str, Any]) -> str:
    """Format dataset analysis results as structured text for LLM system prompt injection."""
    if "error" in analysis:
        return f"DATASET PARSING ERROR: {analysis['error']}"

    lines = [
        "### DATASET STATISTICAL ANALYSIS",
        f"- Total Rows: {analysis['row_count']}",
        f"- Total Columns: {analysis['column_count']}",
        "",
        "#### COLUMN SCHEMA & METRICS:"
    ]

    for col in analysis["columns"]:
        if col["type"] in ("integer", "float"):
            lines.append(
                f"- **{col['name']}** ({col['type']}): non-null={col['non_null_count']}/{col['total_count']}, "
                f"missing={col['missing_count']} ({col['missing_pct']}%), min={col.get('min')}, max={col.get('max')}, "
                f"mean={col.get('mean')}, median={col.get('median')}, std_dev={col.get('std_dev')}"
            )
        else:
            top_str = ", ".join(f"'{tv['value']}': {tv['count']}" for tv in col.get("top_values", []))
            lines.append(
                f"- **{col['name']}** ({col['type']}): non-null={col['non_null_count']}/{col['total_count']}, "
                f"missing={col['missing_count']} ({col['missing_pct']}%), unique_values={col.get('unique_count')}. Top sample: [{top_str}]"
            )

    lines.append("")
    lines.append("#### FIRST 5 ROWS SAMPLE:")
    lines.append(json.dumps(analysis["sample_rows"], indent=2))

    return "\n".join(lines)
