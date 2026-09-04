# Clean Architecture implementation on Litestar
This project is a Python implementation of Robert C. Martin's Clean Architecture. 
It also serves as a modern implementation and interpretation of some of the ideas
in [Cosmic Python](https://www.cosmicpython.com/) and the book Architecture Patterns
with Python by Harry Percival and Bob Gregory.

The project is structured with concentric rings where the code depedencies
flow inwards towards the center (the business domain layer) from the outer
layers. Components are loosely coupled, which benefits testing and the
evolving needs of the platform.

![Clean Architecture](https://blog.cleancoder.com/uncle-bob/images/2012-08-13-the-clean-architecture/CleanArchitecture.jpg)

## Features
- Web framework - Litestar.
    - Transport layer case conversion, i.e PascalCase REST layer to
      snake_case internal naming.
- Authentication - JWT bearer tokens.
    - Argon2id password hashing at the library's RFC 9106 profile, and
      middleware that verifies the token before a request reaches a handler.
      Routes opt out individually with `exclude_from_auth`.
- API documentation - OpenAPI.
    - Swagger and Elements UIs generated from the route handlers, with the
      bearer security scheme declared, so the documentation is usable against
      a running server.
- Domain errors that know nothing about HTTP.
    - The domain and service layers raise plain exceptions; one handler maps
      them onto status codes at the edge, so a NotFoundError becomes a 404
      without the domain importing a web framework.
- Event streaming handled by FastSteam, supports Kafka, RabbitMQ, and Redis.
  Pub / sub.
    - Commands published over the broker are tracked as jobs, so an
      asynchronous request still has an outcome the caller can read back.
    - Commands carry a schema version, and a message predating a field the
      consumer requires is rejected rather than half-run.
- ORM - SQLalchemy
    - Low code approach to adding tables - create a new domain model, a new
      SQLalchemy table entity, and inherit from BaseRepository and
      AbstractRepository.
- Database migrations - Alembic.
    - The schema is owned by versioned migration files.
- Unit of work design pattern.
- Dependency Inversion - Dishka DI framework
    - Dependency injection for components, seperate assembly for the
      application and test case instances. Monkey patching for tests is
      unncessary.
- Typed configuration - pydantic-settings.
    - Settings are read from the environment or `.env` and validated on
      import. A required setting has no default, so a misconfigured
      deployment fails at startup rather than at the first request to need it.
- Static type checking - mypy strict.
    - The application and the test suite both pass mypy in strict mode, with
      ruff and black enforced by pre-commit.


## Application layers
- Business domain
- Database / APIs
- Service layer
- REST transport layer


## Installation and running the server

### MySQL docker
Using: https://hub.docker.com/r/mysql/mysql-server/

1. For WSL, create the following folders:
```
mkdir C:\mysql\data
mkdir C:\mysql\socket
```

2. Install and run the Docker container:
WSL:
```
docker run -d  -e MYSQL_ROOT_PASSWORD={password}   -v C:\mysql\data:/var/lib/mysql   -v C:\mysql\socket:/var/run/mysqld   -p 3306:3306   mysql:latest   --socket=/var/run/mysqld/mysqld.sock
```

POSIX:
```
docker run -d  -e MYSQL_ROOT_PASSWORD={password}   -p 3306:3306   mysql:latest   --socket=/var/run/mysqld/mysqld.sock
```

Substitute {password}, and set the connection string in .env.

### Rabbit MQ
Using: https://hub.docker.com/_/rabbitmq/

1. 
```
docker run -it --rm --name rabbitmq -p 5672:5672 -p 15672:15672 rabbitmq:4.0-management
```

### Server
1. Create a virtual environment

        python -m venv .venv

2. Activate the virtual environment

    _(Windows command prompt)_ `.venv\scripts\activate`

    _(Unix/Linux/MacOS)_ `source .venv/bin/activate`

    _(PowerShell)_ `.venv\Scripts\Activate.ps1`

3. Install the dependencies

        pip install -r requirements.txt

4. Create the database schema

        alembic upgrade head

5. Run the server

        litestar run

    _or alternatively_

        uvicorn app.main:app --reload

## Database migrations

The schema is owned by [Alembic](https://alembic.sqlalchemy.org/). The database
is never changed by hand and the application never creates its own tables:
every change is a reviewable file in `migrations/versions`, applied in order.

Alembic reads `DATABASE_URL` from `app.config` — the same setting the
application uses — so `alembic.ini` holds no connection string and no
password.

### Everyday use

Bring a database up to date:

        alembic upgrade head

After changing an entity, write the migration for it:

        alembic revision --autogenerate -m "add supplier to items"

Autogenerate diffs the entities against the live database and writes the
`op.*` calls itself. **Read what it produced before committing it** — it is a
very good first draft, not an oracle. It does not see a rename (that is a drop
plus an add), and it never writes the data migration that a change of meaning
needs.

Inspect, undo, and see where a database stands:

        alembic history            # the revisions, newest first
        alembic current            # what this database has applied
        alembic downgrade -1       # step back one revision

### Against a database this machine cannot reach

        alembic upgrade head --sql > upgrade.sql

Offline mode emits the SQL rather than running it, for a database whose
credentials belong to somebody else.

### Adding an aggregate

A new entity must be imported in `app/shared/persistence/entities.py`.
Autogenerate can only write a migration for a table it can see, and it sees
`Base.metadata` — which holds whatever has been imported.
`tests/shared/persistence/test_entities.py` fails if that module is missing
one, so a forgotten import is caught by the suite rather than by a missing
table in production.

### The check Django makes you remember to run

`tests/shared/persistence/test_migrations.py` applies every migration to a
scratch database and asserts that autogenerate then finds nothing left to do.
An entity changed without a migration fails the test suite, naming the column:

        Failed: The entities and the migrations disagree. Write a migration
        with `alembic revision --autogenerate`:
        New upgrade operations detected: [('add_column', None, 'items',
        Column('drift_probe', String(length=10), table=<items>))]

It also asserts every migration can be downgraded, so a bad deployment is
reversible. These tests are marked `e2e` and skip when no database server is
running.

5. Go to: 
        http://127.0.0.1:8000/schema/elements
        http://127.0.0.1:8000/schema/swagger

    POST /auth/login:

        {"username": "john.doe@example.com", "password": "password"}

    POST /items:

        {
        "ValueStr": "string",
        "ValueInt": 0,
        "ValueFloat": 0
        }

    PATCH /items:

        {
        "Id": 8,
        "ValueStr": "string"
        }

    A PATCH carries the id and the fields being changed. Anything left out
    keeps the value it already has. `CreatedDate` and `ModifiedDate` belong to
    the server -- the first records when the item was stored, the second is
    stamped on every change -- and are not read from the request.

## Decoupled commands and jobs
`/items_decoupled` accepts the same commands as `/items`, but publishes them
to the broker instead of carrying them out. There is no result to return, so
each route records a job and answers `202 Accepted` with it:

    POST /items_decoupled

        {
        "Id": "9f2c1d8e4b7a4b0f8a1c6d3e5f7a9b2c",
        "Command": "create_item",
        "Status": "PENDING",
        "Result": null,
        "Error": null,
        "CreatedDate": "2025-03-17T01:47:27.156348",
        "ModifiedDate": "2025-03-17T01:47:27.156348"
        }

The subscriber that runs the command moves the job to `RUNNING`, then to
`SUCCEEDED` or `FAILED`. Poll it at:

    GET /jobs/{job_id}
    GET /jobs

`Result` is the id of the item the command affected, so a successful create
is followed by `GET /items/{Result}`. `Error` carries the message of
whatever went wrong. A domain error — deleting an item that does not exist,
say — ends the job as `FAILED` rather than being retried, since the command
could never succeed; anything else is recorded and left to the broker to
redeliver.

## Linting
1. Install linters.
```
pip install -r requirements-lint.in
```
2. Run linters.
```
pre-commit run --all-files
```

## Tests
Tests are located in the tests directory. To run the whole suite in parallel:

        pytest -n auto --dist loadgroup

`-n auto` runs the tests across xdist worker processes, so each has its own
mock database — the integration/E2E tests assert database state. The item
integration tests share one RabbitMQ broker, so they carry
`@pytest.mark.xdist_group("item_integration")`; `--dist loadgroup` is what
makes xdist honour that and keep the whole group on a single worker. Without
it the group mark is inert.

Plain `pytest` (no `-n`) runs everything serially and is what the VS Code test
runner uses — xdist and the editor's per-test execution/debugging do not mix.

## Not implemented yet

What a reference implementation leaves out is worth stating. Roughly in the
order they would be worth closing:

### The domain ring is thin
- `Item`, `Job` and `User` are dataclasses with no methods: every rule about
  them lives in a service.
- `JobStatus` has a real lifecycle (`PENDING` → `RUNNING` → `SUCCEEDED` |
  `FAILED`), but nothing rejects an illegal transition.
- No domain events and no message bus. The broker carries commands issued by
  a controller, never events raised by an aggregate, so there is no
  `collect_new_events` on the unit of work and nothing subscribes in process.
  This is the half of the Cosmic Python progression the project stops short
  of.

### Authorization
- Authentication answers "who are you" and stops there. A token carries
  `exp`, `iat` and `sub` — no roles, scopes or permissions — so any
  authenticated caller can read, change and delete every item.
- Items have no owner.
- No refresh tokens, logout or revocation.
- The user repository is a fake holding one hardcoded user. There is no users
  table, no registration and no password change.

### Message delivery
- No idempotency: a redelivered create command creates a second item. The
  `job_id` every command already carries is the key that would prevent it.
- No dead letter queue and no backoff, so a poison message redelivers
  forever.
- No outbox. A crash between recording a job and publishing its command
  leaves the job `PENDING`, with nothing to run it and nothing to time it out.
- Message contracts are versioned, but there is no upcasting path to a second
  version.

### API surface
- No pagination, filtering or sorting: a collection route returns the whole
  table, and jobs accumulate with no expiry.
- No optimistic concurrency — two concurrent updates and the last writer wins
  silently. `modified_date` is already stored, and is one `If-Match` away
  from being a precondition.
- No API versioning, and `PATCH /items` takes the id in the body rather than
  the path.

### Production readiness
- No health or readiness endpoint, on a service with two external
  dependencies.
- No correlation ids or structured logging, so the two halves of a decoupled
  request cannot be tied together in the logs.
- No rate limiting, including on `/auth/login`.
- No CORS or security header configuration.
- No metrics or tracing.
- No `docker-compose.yml` and no CI.
