#!/usr/bin/env bash
set -e
python manage.py migrate --noinput
python manage.py collectstatic --noinput
# Create the superuser on first deploy; silently skips if the username already exists.
# Must run before seed_if_empty because demo fixtures reference user pk=1.
python manage.py createsuperuser --no-input || true
# Seed reference data (muscle groups, exercises) and demo data (templates, plans)
# only if those tables are empty. Safe to run on every deploy.
python manage.py seed_if_empty
gunicorn hw_app.wsgi:application --bind 0.0.0.0:$PORT