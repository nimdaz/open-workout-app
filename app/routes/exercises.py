"""Routes for creating, browsing, editing, and deleting exercises."""

from flask import Blueprint, render_template, request, redirect, url_for

from ..models import db, Exercise, Activity
from ..helpers import read_checkbox
from ..charts import build_progress_chart

bp = Blueprint("exercises", __name__, url_prefix="/exercises")


@bp.route("/")
def exercises_list():
    exercises = Exercise.query.order_by(Exercise.name).all()
    return render_template("exercises.html", exercises=exercises)


@bp.route("/new")
def exercise_new_page():
    prefill_name = request.args.get("name", "")
    return render_template(
        "exercise_form.html", is_edit=False, exercise_id=None,
        name=prefill_name, has_weight=True, has_duration=False, has_reps=True,
        description="",
    )


@bp.route("/new", methods=["POST"])
def exercise_create():
    name = request.form.get("name", "").strip()
    has_weight = read_checkbox(request.form, "has_weight")
    has_duration = read_checkbox(request.form, "has_duration")
    has_reps = read_checkbox(request.form, "has_reps")
    description = request.form.get("description", "").strip() or None

    def rerender_with_error(error_message):
        return render_template(
            "exercise_form.html", is_edit=False, exercise_id=None,
            name=name, has_weight=has_weight, has_duration=has_duration,
            has_reps=has_reps, description=description, error=error_message,
        )

    if not name:
        return rerender_with_error("Please enter a name.")
    if Exercise.query.filter_by(name=name).first():
        return rerender_with_error(f'An exercise named "{name}" already exists.')

    exercise = Exercise(
        name=name, has_weight=has_weight, has_duration=has_duration,
        has_reps=has_reps, description=description,
    )
    db.session.add(exercise)
    db.session.commit()
    return redirect(url_for("exercises.exercises_list"))


@bp.route("/<int:exercise_id>")
def exercise_detail(exercise_id):
    exercise = Exercise.query.get_or_404(exercise_id)
    activities = (
        Activity.query.filter_by(exercise_id=exercise_id)
        .order_by(Activity.timestamp.desc())
        .all()
    )
    chart = build_progress_chart(exercise, activities)
    return render_template(
        "exercise_detail.html", exercise=exercise, activities=activities, chart=chart
    )


@bp.route("/<int:exercise_id>/edit")
def exercise_edit_page(exercise_id):
    exercise = Exercise.query.get_or_404(exercise_id)
    return render_template(
        "exercise_form.html", is_edit=True, exercise_id=exercise.id,
        name=exercise.name, has_weight=exercise.has_weight,
        has_duration=exercise.has_duration, has_reps=exercise.has_reps,
        description=exercise.description,
    )


@bp.route("/<int:exercise_id>/edit", methods=["POST"])
def exercise_update(exercise_id):
    exercise = Exercise.query.get_or_404(exercise_id)
    name = request.form.get("name", "").strip()
    has_weight = read_checkbox(request.form, "has_weight")
    has_duration = read_checkbox(request.form, "has_duration")
    has_reps = read_checkbox(request.form, "has_reps")
    description = request.form.get("description", "").strip() or None

    def rerender_with_error(error_message):
        return render_template(
            "exercise_form.html", is_edit=True, exercise_id=exercise.id,
            name=name, has_weight=has_weight, has_duration=has_duration,
            has_reps=has_reps, description=description, error=error_message,
        )

    if not name:
        return rerender_with_error("Please enter a name.")
    existing = Exercise.query.filter_by(name=name).first()
    if existing and existing.id != exercise.id:
        return rerender_with_error(f'An exercise named "{name}" already exists.')

    exercise.name = name
    exercise.has_weight = has_weight
    exercise.has_duration = has_duration
    exercise.has_reps = has_reps
    exercise.description = description
    db.session.commit()
    return redirect(url_for("exercises.exercises_list"))


@bp.route("/<int:exercise_id>/delete", methods=["POST"])
def exercise_delete(exercise_id):
    exercise = Exercise.query.get_or_404(exercise_id)
    db.session.delete(exercise)
    db.session.commit()
    return redirect(url_for("exercises.exercises_list"))
