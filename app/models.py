from datetime import datetime
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class Exercise(db.Model):
    __tablename__ = "exercise"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    has_weight = db.Column(db.Boolean, nullable=False, default=True)
    has_duration = db.Column(db.Boolean, nullable=False, default=False)
    has_reps = db.Column(db.Boolean, nullable=False, default=True)
    description = db.Column(db.Text, nullable=True)

    activities = db.relationship(
        "Activity",
        backref="exercise",
        lazy=True,
        cascade="all, delete-orphan",
        order_by="Activity.timestamp.desc()",
    )


class Workout(db.Model):
    """Groups together all activities logged on the same calendar day."""

    __tablename__ = "workout"

    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, unique=True, nullable=False)
    comment = db.Column(db.Text, nullable=True)

    activities = db.relationship(
        "Activity",
        backref="workout",
        lazy=True,
        order_by="Activity.timestamp.desc()",
    )

    @property
    def label(self):
        """Human-readable identifier, e.g. "wed 9-7-2026"."""
        weekday_name = self.date.strftime("%a").lower()
        return f"{weekday_name} {self.date.day}-{self.date.month}-{self.date.year}"


class Activity(db.Model):
    """A single logged set/session of an exercise, e.g. "40 kg x 10 reps"."""

    __tablename__ = "activity"

    id = db.Column(db.Integer, primary_key=True)
    exercise_id = db.Column(db.Integer, db.ForeignKey("exercise.id"), nullable=False)
    workout_id = db.Column(db.Integer, db.ForeignKey("workout.id"), nullable=True)
    timestamp = db.Column(db.DateTime, default=datetime.now, nullable=False)
    weight = db.Column(db.Float, nullable=True)    # kg
    duration = db.Column(db.Float, nullable=True)  # minutes
    reps = db.Column(db.JSON, nullable=True)         # list of ints, e.g. [10, 10, 7]
    settings = db.Column(db.String(200), nullable=True)
    adjustment = db.Column(db.String(1), nullable=True)  # "-", "*", "+" or NULL
    description = db.Column(db.Text, nullable=True)  # free-text note about this activity

    @staticmethod
    def _format_number(value):
        """Trims a trailing ".0" off whole numbers for cleaner display."""
        return str(int(value)) if value == int(value) else str(value)

    @property
    def summary(self):
        """One-line human-readable summary, e.g. "40 kg x 10, 10, 7 -"."""
        parts = []
        if self.weight is not None:
            parts.append(f"{self._format_number(self.weight)} kg")
        if self.duration is not None:
            parts.append(f"{self._format_number(self.duration)} min")
        summary_text = " + ".join(parts)

        if self.reps:
            reps_text = ", ".join(str(rep) for rep in self.reps)
            summary_text = f"{summary_text} × {reps_text}" if summary_text else reps_text

        if self.adjustment:
            summary_text = f"{summary_text} {self.adjustment}" if summary_text else self.adjustment

        return summary_text
