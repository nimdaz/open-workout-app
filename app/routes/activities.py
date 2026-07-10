"""Routes for logging, browsing, editing, and deleting activities."""

from datetime import datetime, time

from flask import Blueprint, render_template, request, redirect, url_for

from ..models import db, Exercise, Activity
from ..helpers import get_or_create_workout, parse_date_param

bp = Blueprint("activities", __name__, url_prefix="/activities")

ADJUSTMENTS = ["-", "*", "+"]


@bp.route("/")
def activities_list():
    activities = (
        Activity.query.join(Exercise)
        .order_by(Activity.timestamp.desc())
        .all()
    )
    return render_template("activities.html", activities=activities)


@bp.route("/new")
def activity_new():
    # An optional ?date=YYYY-MM-DD carries a backdated day through the whole
    # "pick an exercise, then fill in the activity" flow, e.g. when starting
    # from a specific workout's page.
    prefill_date = request.args.get("date", "")
    return render_template("activity_new.html", prefill_date=prefill_date)


@bp.route("/search")
def activity_search():
    query_text = request.args.get("q", "").strip()
    prefill_date = request.args.get("date", "")
    if query_text:
        exercises = (
            Exercise.query.filter(Exercise.name.ilike(f"%{query_text}%"))
            .order_by(Exercise.name)
            .all()
        )
    else:
        exercises = _top_recently_used_exercises(limit=10)
    return render_template(
        "_exercise_search_results.html", exercises=exercises, prefill_date=prefill_date
    )


def _top_recently_used_exercises(limit):
    """Exercises ordered by their most recently logged activity, newest first."""
    last_activity_timestamp = db.func.max(Activity.timestamp)
    rows = (
        db.session.query(Exercise, last_activity_timestamp)
        .outerjoin(Activity, Activity.exercise_id == Exercise.id)
        .group_by(Exercise.id)
        .order_by(last_activity_timestamp.desc().nullslast(), Exercise.name)
        .limit(limit)
        .all()
    )
    return [exercise for exercise, _last_timestamp in rows]


@bp.route("/form")
def activity_form():
    exercise_id = request.args.get("exercise_id", type=int)
    prefill_date = request.args.get("date", "")
    exercise = Exercise.query.get_or_404(exercise_id)
    previous_activities = (
        Activity.query.filter_by(exercise_id=exercise_id)
        .order_by(Activity.timestamp.desc())
        .all()
    )
    most_recent_activity = previous_activities[0] if previous_activities else None

    return render_template(
        "_activity_form.html",
        exercise=exercise,
        last=most_recent_activity,
        previous=previous_activities,
        adjustments=ADJUSTMENTS,
        reps_prefill=_reps_prefill(most_recent_activity),
        prefill_date=prefill_date,
    )


def _reps_prefill(activity):
    """Up to 3 previous rep values, padded with None for empty input fields."""
    reps = list(activity.reps) if activity and activity.reps else []
    return (reps + [None, None, None])[:3]


def _read_reps_from_form(form):
    reps = []
    for field_name in ("reps1", "reps2", "reps3"):
        raw_value = form.get(field_name, "").strip()
        if raw_value:
            try:
                reps.append(int(raw_value))
            except ValueError:
                pass
    return reps or None


def _apply_form_to_activity(activity, exercise, form):
    """Copy submitted form fields onto an Activity, respecting which fields
    this exercise actually tracks.
    """
    activity.weight = form.get("weight", type=float) if exercise.has_weight else None
    activity.duration = form.get("duration", type=float) if exercise.has_duration else None
    activity.reps = _read_reps_from_form(form) if exercise.has_reps else None
    activity.settings = form.get("settings", "").strip() or None
    activity.adjustment = form.get("adjustment", "").strip() or None
    activity.description = form.get("description", "").strip() or None


@bp.route("/", methods=["POST"])
def activity_add():
    exercise_id = request.form.get("exercise_id", type=int)
    exercise = Exercise.query.get_or_404(exercise_id)

    override_date = parse_date_param(request.form.get("date", ""))
    timestamp = datetime.combine(override_date, time.min) if override_date else datetime.now()
    workout = get_or_create_workout(timestamp.date())

    activity = Activity(exercise_id=exercise.id, workout_id=workout.id, timestamp=timestamp)
    _apply_form_to_activity(activity, exercise, request.form)

    db.session.add(activity)
    db.session.commit()
    return redirect(url_for("activities.activities_list"))


@bp.route("/<int:activity_id>/edit")
def activity_edit_page(activity_id):
    activity = Activity.query.get_or_404(activity_id)
    return render_template(
        "activity_edit.html", activity=activity, exercise=activity.exercise,
        adjustments=ADJUSTMENTS,
    )


@bp.route("/<int:activity_id>/edit", methods=["POST"])
def activity_update(activity_id):
    activity = Activity.query.get_or_404(activity_id)
    _apply_form_to_activity(activity, activity.exercise, request.form)

    new_date = parse_date_param(request.form.get("date", ""))
    if new_date and new_date != activity.timestamp.date():
        activity.timestamp = datetime.combine(new_date, time.min)
        activity.workout_id = get_or_create_workout(new_date).id

    db.session.commit()
    return redirect(url_for("activities.activities_list"))


@bp.route("/<int:activity_id>/delete", methods=["POST"])
def activity_delete(activity_id):
    activity = Activity.query.get_or_404(activity_id)
    db.session.delete(activity)
    db.session.commit()
    return redirect(url_for("activities.activities_list"))
