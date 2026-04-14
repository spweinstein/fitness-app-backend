# Health is Wealth — Backend

Django REST API for **Health is Wealth**, a full-stack fitness and workout planning application.

This repo provides the API used by the frontend application. It handles authentication, exercises, workout templates, workout plans, scheduled workouts, profile data, and weight logs.

## Related projects

- Frontend repo: https://github.com/spweinstein/fitness-app-frontend
- Live frontend: https://fitness-app-frontend.netlify.app

## Tech Stack

- Python
- Django
- Django REST Framework
- PostgreSQL
- Pipenv
- Docker Compose
- `djangorestframework-simplejwt`
- `django-cors-headers`
- `dj-database-url`
- WhiteNoise

## API responsibilities

This API supports the main application workflows:

- user registration and login
- current-user lookup and token refresh
- exercise and muscle-group read APIs
- workout CRUD
- workout template CRUD
- workout plan CRUD
- schedule-from-template actions
- generate-from-plan actions
- profile CRUD
- weight-log CRUD

It also supports:

- public/private visibility for templates and plans
- search on public plan/template catalogs
- optional pagination for catalog endpoints
- per-user limits on templates, plans, and workouts

## Authentication endpoints

The current auth surface is:

- `POST /users/register/`
- `POST /users/login/`
- `GET /users/me/`
- `POST /users/token/refresh/`

Current behavior:

- register/login return `access`, `refresh`, and `user`
- `/users/me/` returns the authenticated user only
- `/users/token/refresh/` accepts a refresh token and returns a new access token

## Catalog behavior

Plan/template catalog endpoints support:

- visibility scopes (`public`, `user`, `all`)
- search by title
- optional page-number pagination

Pagination is intentionally backward-compatible:

- if `page` is omitted, catalog endpoints return a plain list
- if `page` is included, they return a paginated response shape

## Local development

### 1. Start Postgres with Docker Compose

```bash
docker-compose up -d
```

This starts a local Postgres container on `localhost:5433`.

To reset the local database completely:

```bash
docker-compose down -v
docker-compose up -d
```

### 2. Install dependencies

```bash
pipenv install
```

### 3. Configure environment variables

Copy `.env.example` to `.env`:

```bash
cp .env.example .env
```

### 4. Apply migrations

```bash
pipenv run python manage.py migrate
```

### 5. Run the development server

```bash
pipenv run python manage.py runserver
```

## Running tests

```bash
pipenv run python manage.py test
```

The Django test runner creates a temporary test database automatically.

## Fixtures

The repo includes JSON fixtures for seeded exercise, template, and plan data under `main_app/fixtures/`.

Load fixtures as needed during local development:

```bash
pipenv run python manage.py loaddata main_app/fixtures/muscle_groups.json
pipenv run python manage.py loaddata main_app/fixtures/exercises.json
pipenv run python manage.py loaddata main_app/fixtures/templates_and_items.json
pipenv run python manage.py loaddata main_app/fixtures/plans.json
```

## Environment variables

Important settings include:

```env
DJANGO_SECRET_KEY=
DJANGO_DEBUG=
DJANGO_ALLOWED_HOSTS=
CORS_ALLOWED_ORIGINS=
CSRF_TRUSTED_ORIGINS=
DATABASE_URL=
DATABASE_SSL_REQUIRE=
JWT_ACCESS_TOKEN_LIFETIME_MINUTES=
JWT_REFRESH_TOKEN_LIFETIME_DAYS=
USER_MAX_WORKOUT_TEMPLATES=
USER_MAX_WORKOUT_PLANS=
USER_MAX_WORKOUTS=
```

## Production notes

A few important production-related behaviors are built into settings:

- `DJANGO_SECRET_KEY` must be set when `DEBUG=False`
- `DJANGO_ALLOWED_HOSTS` must be explicitly provided
- `CORS_ALLOWED_ORIGINS` must be explicitly provided
- `CSRF_TRUSTED_ORIGINS` must be explicitly provided
- non-debug deployments default to requiring DB TLS unless overridden
- static assets are served through WhiteNoise
- per-user caps are configurable through environment variables

## Current scope

This repo is intended to support the current production-style demo of Health is Wealth.

It already includes:

- a split `me` / token refresh auth model
- catalog search and optional pagination
- ownership and visibility rules for templates and plans
- scheduling and generation flows
- regression and performance-oriented tests around core behavior

Areas that can still be improved later include:

- token rotation and revocation
- throttling and broader API abuse protection
- broader search fields and richer filtering
- deeper production runbooks and observability

## Notes for reviewers

- This repo contains the API for the current version of the app
- The frontend lives in a separate repository
- The app is structured around exercises, templates, plans, scheduled workouts, profile data, and weight logs
