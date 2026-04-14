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

## Tests

After `pipenv install`, run the Django test suite from this directory:

```bash
pipenv run python manage.py test
```

That installs and uses the same dependencies as the app (including `djangorestframework-simplejwt`). A clean checkout that skips `pipenv install` will fail with `ModuleNotFoundError` for missing packages.

## Environment

Copy `.env.example` to `.env`. Settings load via `python-dotenv` in `hw_app/settings.py` (`load_dotenv(override=True)`).

**Production:** Set `DJANGO_SECRET_KEY` to a strong secret. When `DJANGO_DEBUG` is false (or unset), Django will refuse to start if `DJANGO_SECRET_KEY` is missing, so deployments without a dev fallback key cannot boot accidentally.

**Database TLS:** `DATABASE_SSL_REQUIRE` overrides whether `dj-database-url` uses `ssl_require` when parsing `DATABASE_URL`. If unset, non-debug (`DEBUG=False`) defaults to requiring SSL; set `DATABASE_SSL_REQUIRE=false` for local Postgres without TLS.

**JWT:** Access and refresh lifetimes are configurable via `JWT_ACCESS_TOKEN_LIFETIME_MINUTES` (default `60`) and `JWT_REFRESH_TOKEN_LIFETIME_DAYS` (default `7`). The SPA should refresh tokens before access expiry; shorter access tokens reduce exposure if a token is leaked.

## Legacy

**`hw-app-backend`** is **read-only** reference during migration; new backend work belongs here.
