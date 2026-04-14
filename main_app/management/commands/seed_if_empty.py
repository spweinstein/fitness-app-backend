from django.core.management.base import BaseCommand
from django.core.management import call_command
from django.contrib.auth.models import User
from main_app.models import MuscleGroup, WorkoutTemplate


class Command(BaseCommand):
    """
    Loads fixture data only when the target tables are empty.
    Safe to run on every deploy — skips each fixture group if records already exist.

    Load order:
      1. muscle_groups + exercises  — reference data; no user dependency.
      2. templates_and_items + plans — public demo data owned by user pk=1 (the
         superuser). Skipped if the superuser does not exist yet or templates are
         already present.
    """

    help = "Seed the database with reference and demo data if the tables are empty."

    def handle(self, *args, **options):
        self._seed_reference_data()
        self._seed_demo_data()

    def _seed_reference_data(self):
        """Load muscle groups and exercises if the muscle_groups table is empty."""
        if MuscleGroup.objects.exists():
            self.stdout.write("Reference data already present — skipping.")
            return

        self.stdout.write("Seeding muscle groups...")
        call_command("loaddata", "muscle_groups", verbosity=0)
        self.stdout.write("Seeding exercises...")
        call_command("loaddata", "exercises", verbosity=0)
        self.stdout.write(self.style.SUCCESS("Reference data seeded."))

    def _seed_demo_data(self):
        """
        Load public demo templates and plans if the workout_templates table is empty.
        Requires the superuser (pk=1) to exist because the fixtures reference that user.
        """
        if WorkoutTemplate.objects.exists():
            self.stdout.write("Demo data already present — skipping.")
            return

        if not User.objects.filter(pk=1).exists():
            self.stdout.write(
                self.style.WARNING(
                    "Superuser (pk=1) not found — skipping demo templates and plans. "
                    "Re-run after the superuser is created."
                )
            )
            return

        self.stdout.write("Seeding demo templates and items...")
        call_command("loaddata", "templates_and_items", verbosity=0)
        self.stdout.write("Seeding demo plans...")
        call_command("loaddata", "plans", verbosity=0)
        self.stdout.write(self.style.SUCCESS("Demo data seeded."))
