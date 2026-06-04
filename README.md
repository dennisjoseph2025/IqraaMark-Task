# IQRAAMARK Internship Platform

A Django REST API for managing internship listings and student applications.

## Features

- **Authentication** — Register (student/company), login, JWT profile
- **Internships** — CRUD for company-published internships
- **Applications** — Students apply, companies update status (pending/accepted/rejected)

## Stack

Django 5.2, DRF, SimpleJWT, PostgreSQL/SQLite, pytest

## Quick Start

```bash
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

## Tests

```bash
pytest -v    # 53 tests
```
