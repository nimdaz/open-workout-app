"""Builds a small inline SVG line chart showing an exercise's weight or
duration trend over time, used at the top of the exercise overview page.

When multiple activities are logged on the same day, weight uses that day's
maximum and duration uses that day's total.
"""

from collections import defaultdict

CHART_WIDTH = 600
CHART_HEIGHT = 110
PADDING_LEFT = 40
PADDING_RIGHT = 12
PADDING_TOP = 10
PADDING_BOTTOM = 22
LINE_COLOR = "#f97316"


def build_progress_chart(exercise, activities):
    """Return {"svg": ..., "title": ...} for the given exercise's activity
    history, or None if there isn't enough numeric data to plot a trend line.

    Weight is preferred over duration when an exercise tracks both.
    """
    if exercise.has_weight:
        metric_name, daily_aggregate, title = "weight", max, "Max. weight over time (kg)"
    elif exercise.has_duration:
        metric_name, daily_aggregate, title = "duration", sum, "Total duration over time (min)"
    else:
        return None

    values_by_day = defaultdict(list)
    for activity in activities:
        value = getattr(activity, metric_name)
        if value is not None:
            values_by_day[activity.timestamp.date()].append(value)

    if len(values_by_day) < 2:
        return None

    data_points = sorted(
        (day, daily_aggregate(values)) for day, values in values_by_day.items()
    )

    return {"svg": _render_svg(data_points), "title": title}


def _render_svg(data_points):
    plot_width = CHART_WIDTH - PADDING_LEFT - PADDING_RIGHT
    plot_height = CHART_HEIGHT - PADDING_TOP - PADDING_BOTTOM

    dates = [point[0] for point in data_points]
    values = [point[1] for point in data_points]

    first_day = dates[0]
    day_span = max((dates[-1] - first_day).days, 1)
    min_value, max_value = min(values), max(values)
    if min_value == max_value:
        min_value -= 1
        max_value += 1
    value_span = max_value - min_value

    def x_position(day):
        return PADDING_LEFT + ((day - first_day).days / day_span) * plot_width

    def y_position(value):
        return PADDING_TOP + plot_height - ((value - min_value) / value_span) * plot_height

    coordinates = [(x_position(day), y_position(value)) for day, value in data_points]
    polyline_points = " ".join(f"{x:.1f},{y:.1f}" for x, y in coordinates)
    dot_markup = "".join(
        f'<circle cx="{x:.1f}" cy="{y:.1f}" r="3" fill="{LINE_COLOR}" />'
        for x, y in coordinates
    )

    first_label = f"{dates[0].day}/{dates[0].month}"
    last_label = f"{dates[-1].day}/{dates[-1].month}"

    return (
        f'<svg viewBox="0 0 {CHART_WIDTH} {CHART_HEIGHT}" role="img" '
        f'style="width:100%; height:auto; display:block;">'
        f'<line x1="{PADDING_LEFT}" y1="{PADDING_TOP}" x2="{PADDING_LEFT}" '
        f'y2="{PADDING_TOP + plot_height}" stroke="currentColor" stroke-opacity="0.25" />'
        f'<line x1="{PADDING_LEFT}" y1="{PADDING_TOP + plot_height}" '
        f'x2="{PADDING_LEFT + plot_width}" y2="{PADDING_TOP + plot_height}" '
        f'stroke="currentColor" stroke-opacity="0.25" />'
        f'<text x="2" y="{PADDING_TOP + 4}" font-size="10" fill="currentColor" opacity="0.7">{max_value:g}</text>'
        f'<text x="2" y="{PADDING_TOP + plot_height}" font-size="10" fill="currentColor" opacity="0.7">{min_value:g}</text>'
        f'<polyline points="{polyline_points}" fill="none" stroke="{LINE_COLOR}" stroke-width="2" />'
        f'{dot_markup}'
        f'<text x="{PADDING_LEFT}" y="{CHART_HEIGHT - 4}" font-size="10" fill="currentColor" opacity="0.7">{first_label}</text>'
        f'<text x="{PADDING_LEFT + plot_width}" y="{CHART_HEIGHT - 4}" font-size="10" '
        f'fill="currentColor" opacity="0.7" text-anchor="end">{last_label}</text>'
        f'</svg>'
    )
