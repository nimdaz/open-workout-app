"""Small helper functions shared across route modules."""

from datetime import datetime

from .models import db, Workout


def get_or_create_workout(for_date):
    """Return the Workout for the given date, creating it if it doesn't exist yet."""
    workout = Workout.query.filter_by(date=for_date).first()
    if not workout:
        workout = Workout(date=for_date)
        db.session.add(workout)
        db.session.flush()
    return workout


def read_checkbox(form, field_name):
    """Interpret an HTML checkbox's presence in submitted form data as a bool."""
    return form.get(field_name) in ("on", "true", "1", "yes")


def parse_date_param(raw_value):
    """Parse a "YYYY-MM-DD" string (e.g. from a <input type="date">) into a
    date object, or return None if it's missing/invalid.
    """
    if not raw_value:
        return None
    try:
        return datetime.strptime(raw_value, "%Y-%m-%d").date()
    except ValueError:
        return None
