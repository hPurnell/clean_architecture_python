# Clean Architecture implementation on Litestar
Python implementation of Robert C. Martin's Clean Architecture. 

The project is structured with concentric rings where the code depedencies flow inwards towards the center (the business domain layer) from the outer layers. Components are loosely coupled, which benefits testing and the evolving needs of the platform.

![Clean Architecture](https://blog.cleancoder.com/uncle-bob/images/2012-08-13-the-clean-architecture/CleanArchitecture.jpg)

## Features
- Web framework - Litestar.
    - Transport layer case conversion, i.e PascalCase REST layer to snake_case internal naming.
- Event streaming handled by FastSteam, supports Kafka, RabbitMQ, and Redis. Pub / sub.
    - Commands published over the broker are tracked as jobs, so an asynchronous request still has an outcome the caller can read back.
- ORM - SQLalchemy
    - Low code approach to adding tables - create a new domain model, a new SQLalchemy table entity, and inherit from BaseRepository and AbstractRepository.
- Unit of work design pattern.
- Dependency Inversion - Dishka DI framework
    - Dependency injection for components, seperate assembly for the application and test case instances. Monkey patching for tests is unncessary.


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

4. Run the server

        litestar run

    _or alternatively_

        uvicorn app.main:app --reload

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
        "ValueStr": "string",
        "ValueInt": 0,
        "ValueFloat": 0,
        "CreatedDate": "2025-03-17T01:47:27.156348",
        "ModifiedDate": "2025-03-17T01:47:27.156353"
        }

## Decoupled commands and jobs
`/items_decoupled` accepts the same commands as `/items`, but publishes them to the broker instead of carrying them out. There is no result to return, so each route records a job and answers `202 Accepted` with it:

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

The subscriber that runs the command moves the job to `RUNNING`, then to `SUCCEEDED` or `FAILED`. Poll it at:

    GET /jobs/{job_id}
    GET /jobs

`Result` is the id of the item the command affected, so a successful create is followed by `GET /items/{Result}`. `Error` carries the message of whatever went wrong. A domain error — deleting an item that does not exist, say — ends the job as `FAILED` rather than being retried, since the command could never succeed; anything else is recorded and left to the broker to redeliver.

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

`-n auto` runs the tests across xdist worker processes, so each has its own mock
database — the integration/E2E tests assert database state. The item integration
tests share one RabbitMQ broker, so they carry
`@pytest.mark.xdist_group("item_integration")`; `--dist loadgroup` is what makes
xdist honour that and keep the whole group on a single worker. Without it the
group mark is inert.

Plain `pytest` (no `-n`) runs everything serially and is what the VS Code test
runner uses — xdist and the editor's per-test execution/debugging do not mix.
