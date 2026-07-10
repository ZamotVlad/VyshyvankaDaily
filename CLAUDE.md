# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this project is

VyshyvankaDaily — a Django app that generates a unique Ukrainian embroidery ornament every day, algorithmically (via symmetry-group math, not UGC/uploaded images), overlaid on a shirt silhouette. Each day is tied to a real historical Ukrainian region with culturally-sourced symbolism, and is deterministic (same date → same result forever). Bilingual (uk/en). See `README.md` for the pitch.

**Full spec lives in three root documents — read them before making architectural decisions, don't re-derive from code alone:**

- `TZ_VYSHYVANKA.md` — the technical spec: apps, models, pages, generation algorithm, security, SEO, admin. This is the single source of truth for intended design.
- `Roadmap_VYSHYVANKA.md` — staged build plan (Stage 0 → 8). Check this to know what's supposed to exist yet vs. not.
- `DECISIONS.md` — ADRs and deviations from the spec/roadmap. **When you make a non-trivial architectural choice or deviate from `TZ_VYSHYVANKA.md`/`Roadmap_VYSHYVANKA.md`, record it here** in the existing ADR / deviation format — that's the project's convention, not optional documentation.

## Current state (read before assuming features exist)

The repo is at **Stage 0** of the roadmap (foundation). Most app files (`models.py`, `views.py`) in `accounts`, `blog`, `pages`, `patterns` are still Django scaffolding stubs. Only `apps/core/models.py` has real code (`TimeStampedModel`, `SlugModel` abstract base models). `config/settings/base.py` and `config/urls.py` are still near-default `startproject` output — custom apps are not yet in `INSTALLED_APPS`, env-var-based config (`django-environ`, listed in `requirements/base.txt`) is not yet wired up, and i18n routing/`django-modeltranslation` registration is not yet connected. Don't assume the architecture described in `TZ_VYSHYVANKA.md` is implemented — check the actual file before relying on it.

## Local commands

Local dev runs in Docker (`docker-compose.yml`), mounting the repo into the container:

```bash
docker compose up            # runs manage.py runserver, host port 9000 -> container 8000
```

There's also a local `venv/` with everything installed if you want to run commands directly on Windows instead of through Docker (e.g. `venv\Scripts\python.exe manage.py ...`).

```bash
ruff check .                 # lint (matches CI)
ruff check --fix .           # lint + autofix
ruff format .                # format
pytest                       # run tests (config: pytest-django, uses config.settings.test)
pytest apps/core/tests.py    # run a single test file
pytest apps/core/tests.py::SomeTestCase::test_something   # single test
pre-commit run --all-files   # ruff-check --fix + ruff-format, same as the git hook
```

CI (`.github/workflows/ci.yml`) runs `ruff check .` then `pytest` on push/PR — nothing more. Keep changes passing both before considering a task done.

Settings module is selected via `DJANGO_SETTINGS_MODULE` (see `.env.example`): `config.settings.local` for dev, `config.settings.test` for pytest, `config.settings.production` for prod. `config/settings/test.py` swaps in `MD5PasswordHasher` purely for test speed — never let that leak into `local`/`production`.

## Architecture (per `TZ_VYSHYVANKA.md` §2 — target state, being built incrementally)

Apps are split by domain, dependencies point one way only (nobody imports from a layer above):

- `core` — foundation. Abstract base models (`TimeStampedModel`, `SlugModel`), shared utilities, context processors, sitemaps, error handlers. Depends on nothing.
- `accounts` — user profile, Allauth customization. Depends on `core`.
- `patterns` — the product's core domain: regions, motifs, sources, daily patterns, the generation algorithm, user collections. Depends on `core` and `accounts` (saved patterns link to users).
- `blog` — bilingual blog with WYSIWYG, categories, guest/sponsored post submissions. Depends on `core` only.
- `pages` — static pages, FAQ, contact form. Depends on `core` only.

Cross-app references (e.g. a blog post mentioning a pattern) go through slug/URL, never a direct FK across app boundaries. The generation algorithm is deliberately kept as an in-process service layer inside `patterns` (not a microservice) — if it grows past a few hundred lines, split into `patterns/generation/` as a subpackage, still inside the same app.

### Key model/design conventions (see `TZ_VYSHYVANKA.md` §3 for full field-level spec)

- **Slugs**: manually entered by the admin is the primary path; `SlugModel` (`apps/core/models.py`) falls back to transliteration (`python-slugify`, `allow_unicode=False` — always ASCII, no ugly percent-encoding in URLs) only if left blank on first save. `DailyPattern` is the exception — identified by date in the URL, no slug at all. See ADR 1 in `DECISIONS.md`.
- **Determinism**: `DailyPattern` generation must be fully deterministic — date → seed → same SVG forever for a given algorithm version. `DailyPattern` records the algorithm version it was generated with; changing the generation algorithm later must never retroactively alter historical records. Tests for determinism are the highest-priority tests in the codebase per the roadmap.
- **Lazy generation, no scheduler**: there is no cron/task scheduler (free-tier hosting constraint — see ADR 3). Today's pattern is generated synchronously on the first request to the homepage each day, guarded by a DB `UniqueConstraint` on date to survive concurrent first-requests. Any new recurring/background-feeling feature should default to this same request-triggered pattern rather than assuming a scheduler exists.
- **SQLite by default** (see ADR 2) — chosen because the workload is read-heavy with only one realistic concurrent-write point (first daily pattern creation), already protected by a unique constraint that works identically on SQLite and Postgres. Don't add SQLite-incompatible assumptions; the DB connection is meant to stay swappable to Postgres without logic changes.
- **Editorial source-of-truth methodology** (`TZ_VYSHYVANKA.md` §4): `Region` and `Motif` must have at least one linked `Source` before being marked "verified," and verification status gates whether they're eligible for the daily rotation. Symbolism descriptions must be explicitly labeled as either "documented" (high/highest-trust source) or "oral tradition" — never blended without distinction. Keep this distinction intact in any model/view work touching `Region`, `Motif`, or `BlogPost` sourcing.
- **i18n**: translated fields (region/motif names & descriptions, blog content, static pages/FAQ) go through `django-modeltranslation`, registered in each app's `translation.py` (see the stub at `apps/core/translation.py` for the pattern — currently empty since `core` has no translatable models yet). Slugs are never translated (one slug serves both language URLs; language prefix is the router's job, not the model's).

## Style

`pyproject.toml` configures Ruff: line length 100, target py312, rule sets `E, F, I, UP, DJ` (includes django-specific lint rules), double quotes, first-party import groups `apps`/`config`. Migrations are excluded from linting.

## Commands

Terminal Environment: The developer works on Windows using PowerShell. When suggesting terminal commands to run locally (outside of Docker), explicitly provide PowerShell-compatible commands (e.g., New-Item instead of touch, .\venv\Scripts\activate instead of source).
