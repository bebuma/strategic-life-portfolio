"""Strategic Life Portfolio plotting tool.

Collects importance, satisfaction, and time-invested ratings across a set of
metrics grouped into strategic life areas (SLAs), then renders a 2-D scatter
plot in which bubble size encodes the fraction of a week spent on each metric.
"""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Final, Iterable, Mapping, Sequence

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

# adjustText < 1.2 references ``numpy.Inf``, which NumPy 2.0 removed. Restore
# the alias before importing so older pinned versions stay usable. Remove
# this shim once ``adjustText`` is upgraded to >= 1.2.
if not hasattr(np, "Inf"):
    np.Inf = np.inf  # type: ignore[attr-defined]

from adjustText import adjust_text  # noqa: E402  (after the np shim above)


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

OUTPUT_DIR: Final[Path] = Path(__file__).resolve().parent / "output"

SLA_COLORS: Final[Mapping[str, str]] = {
    "Relationships": "#ff8080",
    "Body, mind, & spirituality": "#8080ff",
    "Community & society": "#80c080",
    "Job, learning, & finances": "#ffff80",
    "Interests & entertainment": "#c080c0",
    "Personal care": "#bfbfbf",
}

METRIC_TO_SLA: Final[Mapping[str, str]] = {
    "Significant other": "Relationships",
    "Family": "Relationships",
    "Friendship": "Relationships",
    "Physical health/sports": "Body, mind, & spirituality",
    "Spirituality/faith": "Body, mind, & spirituality",
    "Mental health/mindfulness": "Body, mind, & spirituality",
    "Community/citizenship": "Community & society",
    "Societal engagement": "Community & society",
    "Job/career": "Job, learning, & finances",
    "Education/learning": "Job, learning, & finances",
    "Finances": "Job, learning, & finances",
    "Hobbies/interests": "Interests & entertainment",
    "Online entertainment": "Interests & entertainment",
    "Offline entertainment": "Interests & entertainment",
    "Physiological needs": "Personal care",
    "Activities of daily living": "Personal care",
}

MINUTES_PER_WEEK: Final[int] = 7 * 24 * 60
BUBBLE_SIZE_SCALE: Final[float] = 50_000.0
RATING_MIN: Final[float] = 0.0
RATING_MAX: Final[float] = 10.0
RATING_MID: Final[float] = (RATING_MIN + RATING_MAX) / 2
LABEL_NUDGE: Final[float] = 0.5
LABEL_FLIP_THRESHOLD: Final[float] = RATING_MAX - LABEL_NUDGE

_TIME_PATTERN: Final[re.Pattern[str]] = re.compile(
    r"^\s*(?:(\d+)\s*h)?\s*(?:(\d+)\s*m)?\s*$"
)


# ---------------------------------------------------------------------------
# Domain types
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class MetricEntry:
    """One row of user input describing a single life metric.

    Attributes:
        metric: The metric name. Must be a key of ``METRIC_TO_SLA``.
        importance: Self-rated importance on ``[RATING_MIN, RATING_MAX]``.
        satisfaction: Self-rated satisfaction on ``[RATING_MIN, RATING_MAX]``.
        time_minutes: Minutes invested in the metric over a typical week.
    """

    metric: str
    importance: float
    satisfaction: float
    time_minutes: int


class InvalidTimeInputError(ValueError):
    """Raised when a duration string cannot be parsed."""


# ---------------------------------------------------------------------------
# Input parsing
# ---------------------------------------------------------------------------


def parse_time_to_minutes(time_str: str) -> int:
    """Parse a duration string into total minutes.

    Accepts forms such as ``"1h30m"``, ``"45m"``, ``"2h"``, or a bare integer
    hours value such as ``"2"``.

    Args:
        time_str: The raw user input.

    Returns:
        Total number of minutes represented by ``time_str``.

    Raises:
        InvalidTimeInputError: If the string matches none of the accepted forms.
    """
    cleaned = time_str.lower().strip()
    if not cleaned:
        raise InvalidTimeInputError("Time string is empty.")

    if cleaned.isdigit():
        return int(cleaned) * 60

    match = _TIME_PATTERN.fullmatch(cleaned)
    if match is None or not any(match.groups()):
        raise InvalidTimeInputError(f"Cannot parse time string: {time_str!r}")

    hours = int(match.group(1) or 0)
    minutes = int(match.group(2) or 0)
    return hours * 60 + minutes


def prompt_float_in_range(prompt: str, lo: float, hi: float) -> float:
    """Prompt the user repeatedly until a float in ``[lo, hi]`` is given.

    Args:
        prompt: Text shown to the user.
        lo: Minimum accepted value (inclusive).
        hi: Maximum accepted value (inclusive).

    Returns:
        The validated float value.
    """
    while True:
        raw = input(prompt)
        try:
            value = float(raw)
        except ValueError:
            print("Invalid input. Please enter a numerical value.", file=sys.stderr)
            continue
        if lo <= value <= hi:
            return value
        print(f"Please enter a value between {lo} and {hi}.", file=sys.stderr)


def prompt_time(metric: str) -> int:
    """Prompt for a weekly duration until a parseable value is given."""
    while True:
        raw = input(f"  Time invested in {metric} (e.g. 1, 30m, 1h40m): ")
        try:
            return parse_time_to_minutes(raw)
        except InvalidTimeInputError as exc:
            print(f"Invalid time: {exc}. Try again.", file=sys.stderr)


def collect_entries(metric_to_sla: Mapping[str, str]) -> list[MetricEntry]:
    """Walk the user through every metric, grouped by SLA, and gather inputs.

    Args:
        metric_to_sla: Ordered mapping from metric name to its SLA grouping.
            Iteration order determines prompt order; consecutive metrics that
            share an SLA print a single SLA header.

    Returns:
        A list of validated :class:`MetricEntry` objects, one per metric.
    """
    entries: list[MetricEntry] = []
    current_sla: str | None = None
    for metric, sla in metric_to_sla.items():
        if sla != current_sla:
            current_sla = sla
            print(f"\nStrategic life area (SLA): {sla}")
        importance = prompt_float_in_range(
            f"  Importance of {metric} ({RATING_MIN:g}-{RATING_MAX:g}): ",
            RATING_MIN,
            RATING_MAX,
        )
        satisfaction = prompt_float_in_range(
            f"  Satisfaction with {metric} ({RATING_MIN:g}-{RATING_MAX:g}): ",
            RATING_MIN,
            RATING_MAX,
        )
        time_minutes = prompt_time(metric)
        entries.append(MetricEntry(metric, importance, satisfaction, time_minutes))
    return entries


# ---------------------------------------------------------------------------
# Plotting
# ---------------------------------------------------------------------------


def entries_to_dataframe(entries: Iterable[MetricEntry]) -> pd.DataFrame:
    """Convert metric entries to a DataFrame sorted by time descending.

    Larger bubbles are drawn first so smaller ones stay readable on top.
    """
    df = pd.DataFrame(
        [
            {
                "Metric": e.metric,
                "Importance": e.importance,
                "Satisfaction": e.satisfaction,
                "Time": e.time_minutes,
            }
            for e in entries
        ]
    )
    return df.sort_values("Time", ascending=False).reset_index(drop=True)


def _nudge(value: float) -> float:
    """Offset a label coordinate off its anchor, flipping near the upper edge."""
    if value > LABEL_FLIP_THRESHOLD:
        return value - LABEL_NUDGE
    return value + LABEL_NUDGE


def plot_portfolio(
    data: pd.DataFrame,
    *,
    sla_colors: Mapping[str, str],
    metric_to_sla: Mapping[str, str],
    title: str = "Strategic Life Portfolio",
) -> plt.Figure:
    """Render the importance/satisfaction bubble plot.

    Args:
        data: DataFrame with columns ``Metric``, ``Importance``, ``Satisfaction``,
            ``Time`` (minutes per week).
        sla_colors: Map from SLA name to a matplotlib color string.
        metric_to_sla: Map from metric name to its SLA grouping.
        title: Figure title.

    Returns:
        The configured matplotlib :class:`~matplotlib.figure.Figure`. The
        caller owns the figure and is responsible for saving/showing/closing it.
    """
    fig, ax = plt.subplots(figsize=(8, 8))
    labels: list[plt.Text] = []
    for row in data.itertuples(index=False):
        color = sla_colors[metric_to_sla[row.Metric]]
        bubble_size = (row.Time / MINUTES_PER_WEEK) * BUBBLE_SIZE_SCALE
        ax.scatter(
            row.Satisfaction,
            row.Importance,
            s=bubble_size,
            color=color,
            alpha=1,
            edgecolors="w",
            linewidth=0.5,
        )
        text_x, text_y = _nudge(row.Satisfaction), _nudge(row.Importance)
        ax.plot(
            [row.Satisfaction, text_x],
            [row.Importance, text_y],
            color="gray",
            linestyle="--",
            linewidth=0.5,
        )
        labels.append(ax.text(text_x, text_y, row.Metric, fontsize=9))

    adjust_text(labels, ax=ax)
    ax.set_xlim(RATING_MIN, RATING_MAX)
    ax.set_ylim(RATING_MIN, RATING_MAX)
    ax.set_xlabel("Satisfaction")
    ax.set_ylabel("Importance")
    ax.set_title(title)
    ax.grid(True)
    ax.axvline(x=RATING_MID, color="gray", linestyle="--")
    ax.axhline(y=RATING_MID, color="gray", linestyle="--")
    return fig


def save_figure(fig: plt.Figure, output_dir: Path, name: str) -> Path:
    """Save ``fig`` to ``output_dir/name`` and return the resulting path.

    A ``.png`` suffix is appended if ``name`` has no extension. The output
    directory is created if it does not already exist.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    target = output_dir / (name if Path(name).suffix else f"{name}.png")
    fig.savefig(target)
    return target


# ---------------------------------------------------------------------------
# Demo data
# ---------------------------------------------------------------------------

DEMO_ENTRIES: Final[Sequence[MetricEntry]] = (
    MetricEntry("Significant other", 8.0, 3.0, 840),
    MetricEntry("Family", 9.0, 4.0, 420),
    MetricEntry("Friendship", 7.0, 3.0, 210),
    MetricEntry("Physical health/sports", 5.0, 5.0, 420),
    MetricEntry("Spirituality/faith", 4.0, 4.0, 210),
    MetricEntry("Mental health/mindfulness", 2.0, 6.0, 45),
    MetricEntry("Community/citizenship", 3.0, 3.0, 420),
    MetricEntry("Societal engagement", 2.0, 2.0, 210),
    MetricEntry("Job/career", 8.0, 7.0, 840),
    MetricEntry("Education/learning", 7.0, 6.0, 420),
    MetricEntry("Finances", 9.0, 8.0, 420),
    MetricEntry("Hobbies/interests", 6.0, 5.0, 420),
    MetricEntry("Online entertainment", 1.0, 4.0, 840),
    MetricEntry("Offline entertainment", 4.0, 3.0, 420),
    MetricEntry("Physiological needs", 7.0, 2.0, 420),
    MetricEntry("Activities of daily living", 8.0, 7.0, 420),
)


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------


def print_welcome() -> None:
    """Print the welcome banner and today's date."""
    today = datetime.today().strftime("%d/%m/%Y")
    print("\nWelcome to Strategic Life Portfolio!")
    print(f"\nToday is {today}")


def prompt_name() -> str:
    """Prompt for the user's name, falling back to ``'Anonymous'`` if blank."""
    return input("\nEnter your name: ").strip() or "Anonymous"


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Strategic Life Portfolio plotter."
    )
    parser.add_argument(
        "--interactive",
        action="store_true",
        help="Prompt for every metric instead of using the built-in demo data.",
    )
    parser.add_argument(
        "--name",
        default=None,
        help="Output filename stem (default: prompt the user, or 'Anonymous').",
    )
    parser.add_argument(
        "--no-show",
        action="store_true",
        help="Save the figure without opening an interactive window.",
    )
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    """Program entry point.

    Returns:
        Process exit code (``0`` on success).
    """
    args = parse_args(argv)
    print_welcome()

    if args.interactive:
        name = args.name or prompt_name()
        entries: Sequence[MetricEntry] = collect_entries(METRIC_TO_SLA)
    else:
        name = args.name or "Anonymous"
        entries = DEMO_ENTRIES

    data = entries_to_dataframe(entries)
    fig = plot_portfolio(
        data, sla_colors=SLA_COLORS, metric_to_sla=METRIC_TO_SLA
    )
    out_path = save_figure(fig, OUTPUT_DIR, name)
    print(f"\nSaved plot to {out_path}")
    if not args.no_show:
        plt.show()
    plt.close(fig)
    print("Thank you! :)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
