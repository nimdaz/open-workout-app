"""CSV export and import for backing up and restoring exercises and activities."""

import csv
import io
from datetime import datetime

from .models import db, Exercise, Activity
from .helpers import get_or_create_workout

CSV_COLUMNS = [
    "type", "id", "name", "has_weight", "has_duration", "has_reps", "description",
    "exercise_id", "exercise_name", "timestamp", "weight", "duration", "reps",
    "settings", "adjustment", "activity_description",
]


def export_all_data_as_csv():
    """Return a CSV string containing every exercise and activity."""
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(CSV_COLUMNS)

    for exercise in Exercise.query.order_by(Exercise.id).all():
        writer.writerow([
            "exercise", exercise.id, exercise.name,
            int(exercise.has_weight), int(exercise.has_duration), int(exercise.has_reps),
            exercise.description or "",
            "", "", "", "", "", "", "", "", "",
        ])

    for activity in Activity.query.order_by(Activity.id).all():
        reps_as_text = ",".join(str(rep) for rep in activity.reps) if activity.reps else ""
        writer.writerow([
            "activity", activity.id, "", "", "", "", "",
            activity.exercise_id,
            activity.exercise.name,
            activity.timestamp.isoformat(sep=" "),
            activity.weight if activity.weight is not None else "",
            activity.duration if activity.duration is not None else "",
            reps_as_text,
            activity.settings or "",
            activity.adjustment or "",
            activity.description or "",
        ])

    return output.getvalue()


def import_data_from_csv(file_stream):
    """Import exercises and activities from a CSV file previously produced by
    export_all_data_as_csv(). Existing exercises are matched by name and
    reused; activities are always added as new rows. Returns a human-readable
    summary message, or an error message if the import failed.
    """
    try:
        text_stream = io.StringIO(file_stream.read().decode("utf-8-sig"))
        reader = csv.DictReader(text_stream)

        exercises_by_name = {exercise.name: exercise for exercise in Exercise.query.all()}
        imported_exercise_count = 0
        imported_activity_count = 0

        for row in reader:
            row_type = (row.get("type") or "").strip().lower()
            if row_type == "exercise":
                imported_exercise_count += _import_exercise_row(row, exercises_by_name)
            elif row_type == "activity":
                activities_added, exercises_added = _import_activity_row(row, exercises_by_name)
                imported_activity_count += activities_added
                imported_exercise_count += exercises_added

        db.session.commit()
        return (
            f"Imported {imported_exercise_count} exercise(s) and "
            f"{imported_activity_count} activity/activities."
        )
    except Exception as error:
        db.session.rollback()
        return f"Import failed: {error}"


def _is_truthy(raw_value):
    return (raw_value or "").strip() in ("1", "true", "True", "yes")


def _import_exercise_row(row, exercises_by_name):
    name = (row.get("name") or "").strip()
    if not name or name in exercises_by_name:
        return 0

    exercise = Exercise(
        name=name,
        has_weight=_is_truthy(row.get("has_weight")) if row.get("has_weight") not in (None, "") else True,
        has_duration=_is_truthy(row.get("has_duration")),
        has_reps=_is_truthy(row.get("has_reps")) if row.get("has_reps") not in (None, "") else True,
        description=(row.get("description") or "").strip() or None,
    )
    db.session.add(exercise)
    db.session.flush()
    exercises_by_name[name] = exercise
    return 1


def _import_activity_row(row, exercises_by_name):
    exercise_name = (row.get("exercise_name") or "").strip()
    if not exercise_name:
        return 0, 0

    new_exercise_count = 0
    exercise = exercises_by_name.get(exercise_name)
    if not exercise:
        exercise = Exercise(name=exercise_name)
        db.session.add(exercise)
        db.session.flush()
        exercises_by_name[exercise_name] = exercise
        new_exercise_count = 1

    reps_raw = (row.get("reps") or "").strip()
    reps = [int(value) for value in reps_raw.split(",") if value.strip() != ""] if reps_raw else None

    weight_raw = (row.get("weight") or "").strip()
    weight = float(weight_raw) if weight_raw != "" else None

    duration_raw = (row.get("duration") or "").strip()
    duration = float(duration_raw) if duration_raw != "" else None

    timestamp_raw = (row.get("timestamp") or "").strip()
    try:
        timestamp = datetime.fromisoformat(timestamp_raw) if timestamp_raw else datetime.now()
    except ValueError:
        timestamp = datetime.now()

    workout = get_or_create_workout(timestamp.date())

    activity = Activity(
        exercise_id=exercise.id,
        workout_id=workout.id,
        timestamp=timestamp,
        weight=weight,
        duration=duration,
        reps=reps,
        settings=(row.get("settings") or "").strip() or None,
        adjustment=(row.get("adjustment") or "").strip() or None,
        description=(row.get("activity_description") or "").strip() or None,
    )
    db.session.add(activity)
    return 1, new_exercise_count
