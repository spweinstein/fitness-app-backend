# Fitness app — backend (canonical)

This is the **canonical** Django REST API for the fitness application (JWT via `djangorestframework-simplejwt`, CORS enabled for local Vite).

It was established from a **legacy backend snapshot** sourced from **`hw-app-backend`** branch **`sw-v2`**. This repo is now the **source of truth**; the legacy repository is reference-only.

## Local setup

Local development uses Docker Compose to run Postgres and Pipenv to manage Python dependencies.

**1. Start the database**

```bash
docker-compose up -d
```

This starts a Postgres 16 container on `localhost:5433` with the credentials in `.env.example`. The database persists in a named Docker volume between restarts (`docker-compose stop` / `docker-compose up -d`).

To wipe the database and start completely fresh (e.g. to verify migrations from scratch):

```bash
docker-compose down -v   # destroys the volume — all data is lost
docker-compose up -d
```

**2. Install dependencies and migrate**

```bash
pipenv install
pipenv run python manage.py migrate
```

`pipenv run` ensures commands execute inside the project's virtual environment using the exact versions in `Pipfile.lock`. Running `python manage.py migrate` without it will likely fail because Django and its dependencies won't be on the system PATH.

**3. Run the dev server**

```bash
pipenv run python manage.py runserver
```

## Tests

With the Docker Compose database running, execute the Django test suite from this directory:

```bash
pipenv run python manage.py test
```

The test runner creates and destroys a temporary test database automatically; it does not touch your development data. A clean checkout that skips `pipenv install` will fail with `ModuleNotFoundError` for missing packages.

## Environment

Copy `.env.example` to `.env`. Settings load via `python-dotenv` in `hw_app/settings.py` (`load_dotenv(override=True)`).

**Production:** Set `DJANGO_SECRET_KEY` to a strong secret. When `DJANGO_DEBUG` is false (or unset), Django will refuse to start if `DJANGO_SECRET_KEY` is missing, so deployments without a dev fallback key cannot boot accidentally.

**Database:** The app connects to whatever `DATABASE_URL` is set in the environment — Docker Compose is only used locally. On Railway (or any managed Postgres host), set `DATABASE_URL` to the connection string provided by the platform. Railway injects this automatically for attached Postgres services.

**Database TLS:** `DATABASE_SSL_REQUIRE` overrides whether `dj-database-url` uses `ssl_require` when parsing `DATABASE_URL`. If unset, non-debug (`DEBUG=False`) defaults to requiring SSL; set `DATABASE_SSL_REQUIRE=false` for local Postgres without TLS. Managed hosts like Railway use SSL by default, so the production default is correct without any extra configuration.

**JWT:** Access and refresh lifetimes are configurable via `JWT_ACCESS_TOKEN_LIFETIME_MINUTES` (default `60`) and `JWT_REFRESH_TOKEN_LIFETIME_DAYS` (default `7`). The SPA should refresh tokens before access expiry; shorter access tokens reduce exposure if a token is leaked.

## Legacy

**`hw-app-backend`** is **read-only** reference during migration; new backend work belongs here.
