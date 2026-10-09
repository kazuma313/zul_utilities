import io
import json
import logging
import re
import uuid
from pathlib import Path

import matplotlib
matplotlib.use("Agg")  # non-interactive backend — must be set before pyplot import
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
from langchain_core.runnables import RunnableConfig
from langchain_core.tools import tool

from app.agent.minio_connection import upload_file_to_minio

logger = logging.getLogger(__name__)


def _loads_lenient(text: str):
    """json.loads that forgives what a small model adds around the JSON it passes as a string.

    Seen with qwen3:4b and qwen3:8b calling these tools: a stray quote or a remark after the closing
    brace, a code fence around the JSON, a comma before a closing bracket.  The first complete JSON
    value is taken and the rest is ignored.
    """
    text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text.strip())
    start = min((i for i in (text.find("{"), text.find("[")) if i >= 0), default=0)
    text = text[start:]
    error = None
    no_trailing = re.sub(r",\s*([\]}])", r"\1", text)
    for candidate in (text, no_trailing, _closed(no_trailing)):
        try:
            return json.JSONDecoder().raw_decode(candidate)[0]
        except json.JSONDecodeError as e:
            error = error or e
    raise error


def _closed(text: str) -> str:
    """The text plus the brackets it opened and never closed (a model often drops the last one)."""
    stack, in_string, escaped = [], False, False
    for ch in text:
        if in_string:
            if escaped:
                escaped = False
            elif ch == "\\":
                escaped = True
            elif ch == '"':
                in_string = False
        elif ch == '"':
            in_string = True
        elif ch in "{[":
            stack.append("}" if ch == "{" else "]")
        elif ch in "}]" and stack:
            stack.pop()
    return text + ('"' if in_string else "") + "".join(reversed(stack))

# utilities/chart/ → project root → app/static/charts/
CHARTS_DIR = Path(__file__).parent.parent.parent / "app" / "static" / "charts"
CHARTS_DIR.mkdir(parents=True, exist_ok=True)

SUPPORTED_CHARTS = {"bar", "line", "scatter", "histogram", "heatmap", "box"}


def _auto_rotate_xlabels(ax) -> None:
    """Rotate and shrink x-axis tick labels when they would overlap.

    Thresholds:
      ≤ 5 labels  → no rotation (horizontal, default size)
      6–9 labels  → 30° rotation
      10–14 labels → 45° rotation
      ≥ 15 labels  → 60° rotation + smaller font
    Labels longer than 8 chars are also weighted heavier to trigger rotation sooner.
    """
    labels = [t.get_text() for t in ax.get_xticklabels()]
    n = len(labels)
    if n == 0:
        return

    # Weight long labels as if there were more of them
    avg_len = sum(len(l) for l in labels) / n
    weight = max(1.0, avg_len / 6)
    effective_n = n * weight

    if effective_n <= 5:
        rotation, fontsize, ha = 0, 10, "center"
    elif effective_n <= 12:
        rotation, fontsize, ha = 30, 9, "right"
    elif effective_n <= 20:
        rotation, fontsize, ha = 45, 8, "right"
    else:
        rotation, fontsize, ha = 60, 7, "right"

    ax.set_xticklabels(labels, rotation=rotation, ha=ha, fontsize=fontsize)


def _parse_data(data: str) -> pd.DataFrame:
    """Auto-detect JSON or CSV and return a DataFrame."""
    data = data.strip()
    if data.startswith("[") or data.startswith("{"):
        parsed = _loads_lenient(data)
        if isinstance(parsed, dict):
            return pd.DataFrame([parsed])
        return pd.DataFrame(parsed)
    return pd.read_csv(io.StringIO(data))


@tool
def generate_chart(
    data: str,
    chart_type: str,
    x_col: str,
    title: str = "Chart",
    y_col: str = "",
    hue: str = "",
    config: RunnableConfig = None,
) -> str:
    """Generate a chart from data and return a URL to display it.

    Use this whenever the user asks to plot, visualize, or chart any data.
    Supported chart types: bar, line, scatter, histogram, heatmap, box.

    Args:
        data: Data as a JSON array of objects OR a CSV string.
            JSON: '[{"month":"Jan","sales":100},{"month":"Feb","sales":150}]'
            CSV:  'month,sales\\nJan,100\\nFeb,150'
        chart_type: One of: bar, line, scatter, histogram, heatmap, box
        x_col: Column name for the x-axis (or the main variable for histogram/heatmap)
        title: Title to display above the chart
        y_col: Column name for the y-axis (not needed for histogram)
        hue: Optional column name for color grouping
    """
    chart_type = chart_type.lower().strip()
    if chart_type not in SUPPORTED_CHARTS:
        return f"Unsupported chart type '{chart_type}'. Choose from: {sorted(SUPPORTED_CHARTS)}"

    logger.info("[TOOL] generate_chart | type=%s x=%s y=%s title=%r", chart_type, x_col, y_col, title)

    try:
        df = _parse_data(data)
    except Exception as e:
        logger.error("[TOOL] generate_chart parse error: %s", e)
        return f"Failed to parse data: {e}. Provide a valid JSON array or CSV string."

    hue_col = hue if hue and hue in df.columns else None
    y_col_val = y_col if y_col and y_col in df.columns else None

    try:
        sns.set_theme(style="darkgrid", palette="tab10")

        # Scale figure width based on category count and number of groups
        n_categories = df[x_col].nunique() if x_col in df.columns else 1
        n_groups = df[hue_col].nunique() if hue_col and hue_col in df.columns else 1
        fig_width = max(10, n_categories * max(1.2, n_groups * 0.6))
        fig_height = max(6, fig_width * 0.45)
        fig, ax = plt.subplots(figsize=(min(fig_width, 24), min(fig_height, 14)))

        if chart_type == "bar":
            sns.barplot(data=df, x=x_col, y=y_col_val, hue=hue_col, ax=ax, errorbar=None)
            # Annotate bar values when there are few enough bars to read
            if n_categories * n_groups <= 30:
                for container in ax.containers:
                    ax.bar_label(container, fmt="%.1f", fontsize=7, padding=2)
        elif chart_type == "line":
            sns.lineplot(data=df, x=x_col, y=y_col_val, hue=hue_col, ax=ax,
                         errorbar=None, marker="o", markersize=5)
        elif chart_type == "scatter":
            sns.scatterplot(data=df, x=x_col, y=y_col_val, hue=hue_col, ax=ax)
        elif chart_type == "histogram":
            sns.histplot(data=df, x=x_col, hue=hue_col, kde=True, ax=ax)
        elif chart_type == "heatmap":
            numeric_df = df.select_dtypes(include="number")
            sns.heatmap(numeric_df.corr(), annot=True, fmt=".2f", ax=ax)
        elif chart_type == "box":
            sns.boxplot(data=df, x=x_col, y=y_col_val, hue=hue_col, ax=ax)

        ax.set_title(title, fontsize=14, fontweight="bold", pad=14)
        # Move legend outside plot when there are multiple groups to avoid overlap
        if hue_col and n_groups > 1:
            ax.legend(title=hue_col, bbox_to_anchor=(0.5, -0.22), loc="upper center",
                      ncols=min(n_groups, 5), frameon=True)
        _auto_rotate_xlabels(ax)
        plt.tight_layout()

        filename = f"{uuid.uuid4().hex}.png"
        out_path = CHARTS_DIR / filename
        fig.savefig(out_path, dpi=150, bbox_inches="tight")
        plt.close(fig)

        thread_id = (config or {}).get("configurable", {}).get("thread_id", "")
        username = thread_id.split("__")[0] if "__" in thread_id else "charts"
        upload_file_to_minio(out_path.read_bytes(), username, filename, "image/png", folder="images")

        url = f"/static/charts/{filename}"
        logger.info("[TOOL] generate_chart saved | url=%s", url)
        return f"Chart generated successfully. chart_url:{url}"

    except Exception as e:
        plt.close("all")
        logger.error("[TOOL] generate_chart render error: %s", e)
        return f"Failed to generate chart: {e}"
