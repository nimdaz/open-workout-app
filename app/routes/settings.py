"""Settings page plus CSV export/import and full data removal."""

from flask import Blueprint, render_template, request, Response

from ..models import db, Exercise, Activity, Workout
from ..csv_transfer import export_all_data_as_csv, import_data_from_csv

bp = Blueprint("settings", __name__)

REQUIRED_CONFIRMATION_TEXT = "confirm"


@bp.route("/settings")
def settings_page():
    return render_template("settings.html")


@bp.route("/export/csv")
def export_csv():
    csv_text = export_all_data_as_csv()
    return Response(
        csv_text,
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment; filename=workout-data.csv"},
    )


@bp.route("/import/csv", methods=["POST"])
def import_csv():
    uploaded_file = request.files.get("file")
    if not uploaded_file or uploaded_file.filename == "":
        return render_template("settings.html", message="No file selected.")
    message = import_data_from_csv(uploaded_file.stream)
    return render_template("settings.html", message=message)


@bp.route("/settings/delete-all", methods=["POST"])
def delete_all_data():
    typed_confirmation = request.form.get("confirm", "").strip().lower()
    if typed_confirmation != REQUIRED_CONFIRMATION_TEXT:
        return render_template(
            "settings.html",
            message='Type "confirm" exactly to remove all data. Nothing was deleted.',
        )

    Activity.query.delete()
    Workout.query.delete()
    Exercise.query.delete()
    db.session.commit()
    return render_template("settings.html", message="All data has been removed.")

