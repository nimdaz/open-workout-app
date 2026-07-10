"""Routes for browsing workouts (activities grouped by day) and editing
their comments and date.
"""

from datetime import datetime, time

from flask import Blueprint, render_template, request, redirect, url_for

from ..models import db, Activity, Workout
from ..helpers import parse_date_param

bp = Blueprint("workouts", __name__, url_prefix="/workouts")


@bp.route("/")
def workouts_list():
    workouts = (
        Workout.query.filter((Workout.activities.any()) | (Workout.comment.isnot(None)))
        .order_by(Workout.date.desc())
        .all()
    )
    return render_template("workouts.html", workouts=workouts)


@bp.route("/<int:workout_id>")
def workout_detail(workout_id):
    workout = Workout.query.get_or_404(workout_id)
    activities = (
        Activity.query.filter_by(workout_id=workout.id)
        .order_by(Activity.timestamp.desc())
        .all()
    )
    return render_template("workout_detail.html", workout=workout, activities=activities)


@bp.route("/<int:workout_id>/comment", methods=["POST"])
def workout_comment_update(workout_id):
    workout = Workout.query.get_or_404(workout_id)
    workout.comment = request.form.get("comment", "").strip() or None
    db.session.commit()
    return render_template("_workout_comment.html", workout=workout)


@bp.route("/<int:workout_id>/date", methods=["POST"])
def workout_date_update(workout_id):
    """Move a workout (and every activity in it) to a different day. Their
    times are reset to 00:00 since only the day is known once moved.

    If another workout already exists on the target day, this workout's
    activities are merged into it instead of leaving two workouts on the
    same day.
    """
    workout = Workout.query.get_or_404(workout_id)
    new_date = parse_date_param(request.form.get("date", ""))
    if not new_date or new_date == workout.date:
        return redirect(url_for("workouts.workout_detail", workout_id=workout.id))

    new_midnight = datetime.combine(new_date, time.min)
    target_workout = Workout.query.filter_by(date=new_date).first()

    if target_workout and target_workout.id != workout.id:
        Activity.query.filter_by(workout_id=workout.id).update(
            {"workout_id": target_workout.id, "timestamp": new_midnight}
        )
        if workout.comment and not target_workout.comment:
            target_workout.comment = workout.comment
        db.session.delete(workout)
        db.session.commit()
        return redirect(url_for("workouts.workout_detail", workout_id=target_workout.id))

    Activity.query.filter_by(workout_id=workout.id).update({"timestamp": new_midnight})
    workout.date = new_date
    db.session.commit()
    return redirect(url_for("workouts.workout_detail", workout_id=workout.id))
