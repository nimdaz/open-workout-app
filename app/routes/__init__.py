"""All route blueprints, collected for easy registration in the app factory."""

from . import pages, exercises, activities, workouts, settings

ALL_BLUEPRINTS = [pages.bp, exercises.bp, activities.bp, workouts.bp, settings.bp]
