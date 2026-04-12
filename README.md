# Fitness app — backend (canonical)

This is the **canonical** Django REST API for the fitness application (JWT via `djangorestframework-simplejwt`, CORS enabled for local Vite).

It was established from a **legacy backend snapshot** sourced from **`hw-app-backend`** branch **`sw-v2`**. This repo is now the **source of truth**; the legacy repository is reference-only.

## Local setup

Dependencies are managed with **Pipenv** (`Pipfile`). From this repo:

```bash
pipenv install
pipenv run python manage.py migrate
pipenv run python manage.py runserver
```

Adjust commands if you use another virtualenv workflow, but Pipenv is what this tree ships with.

## Environment

Copy `.env.example` to `.env`. Settings load via `python-dotenv` in `hw_app/settings.py` (`load_dotenv(override=True)`).

## Legacy

**`hw-app-backend`** is **read-only** reference during migration; new backend work belongs here.
