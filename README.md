<!--
SPDX-FileCopyrightText: 2021 Magenta ApS <https://magenta.dk>
SPDX-License-Identifier: MPL-2.0
-->

# Organisation Gatekeeper

This repository contains an OS2mo integration that marks organisation units with one of four categories; Line management, self-owned, hidden or outside hierarchy.

It reacts to changes in OS2mo through the MO GraphQL event system. On startup it declares a listener per relevant object type in the `mo` namespace, and MO then delivers events to the matching endpoint:

| Routing key   | Endpoint                    |
|---------------|-----------------------------|
| `org_unit`    | `/events/mo/org_unit`       |
| `ituser`      | `/events/mo/ituser`         |
| `association` | `/events/mo/association`    |
| `engagement`  | `/events/mo/engagement`     |

An organisation unit is part of line management if:
* The unit-level is NY{x}-niveau or Afdelings-niveau.
* There are engagements or associations.
* The organisation unit is bellow a unit that is defined as root of line management in the configuration of this program.

If an organisation unit is not part of line management but has an it-account in a configured it-system it is marked as self-owned.

Any org_units that are configured to be hidden will be marked as such, and the same for each unit below it.

If an organisation unit does not fall into any of the above categories it will be marked as 'outside hierarchy'.

## Configurations

Adjust the environment variables either;
* directly in `docker-compose.yml` or
* by creating a `docker-compose.override.yaml` file.


* `SELF_OWNED_IT_SYSTEM_CHECK`: The it-system to check if the unit should be marked as self-owned.
* `LISTEN_TO_CHANGES_IN_MO`: Whether to declare the GraphQL event listeners and process MO changes as they happen. Defaults to `true`; the integration is event-driven and does nothing useful without it.

## Usage

Start the container using `docker-compose` (assuming you already have a running development-instance of os2mo):
```
docker-compose up -d
```

You should see the following:
```
[info     ] Starting metrics server        port=800
[info     ] Starting GraphQL event fetchers
[info     ] Declaring listener             listener=Listener(namespace='mo', user_key='org_unit', routing_key='org_unit', path='/events/mo/org_unit', parallelism=1)
[info     ] Starting fetcher               listener=... n=0
```
After which each event will add:
```
[info     ] Received org_unit event        org_unit_event={'subject': '...', 'priority': 10000}
[info     ] Changes to org_unit or its it-accounts org_unit=...
```
And at which point metrics should be available at `localhost:8000`, and line management information will be updated.

## Development

### Prerequisites

- [Poetry](https://github.com/python-poetry/poetry)

### Getting Started

1. Clone the repository:
```
git clone git@git.magenta.dk:rammearkitektur/os2mo-triggers/os2mo-amqp-trigger-organisation-gatekeeper.git
```

2. Install all dependencies:
```
poetry install
```

3. Set up pre-commit:
```
poetry run pre-commit install
```

### Running the tests

You use `poetry` and `pytest` to run the tests:

`poetry run pytest`

You can also run specific files

`poetry run pytest tests/<test_folder>/<test_file.py>`

and even use filtering with `-k`

`poetry run pytest -k "Manager"`

You can use the flags `-vx` where `v` prints the test & `x` makes the test stop if any tests fails (Verbose, X-fail)

#### Running the integration tests

The integration tests run against a live OS2mo stack. Start the
[os2mo](https://github.com/OS2mo/os2mo) stack according to its README, then start
this integration's stack and run the tests inside it:
```
docker compose up -d --build
docker compose stop orggatekeeper
docker compose run --rm orggatekeeper pytest tests/integration
```

## Versioning

This project uses [Semantic Versioning](https://semver.org/) with the following strategy:
- MAJOR: Incompatible changes to existing data models
- MINOR: Backwards compatible updates to existing data models OR new models added
- PATCH: Backwards compatible bug fixes

## Authors

Magenta ApS <https://magenta.dk>

## License

This project uses: [MPL-2.0](MPL-2.0.txt)

This project uses [REUSE](https://reuse.software) for licensing.
All licenses can be found in the [LICENSES folder](LICENSES/) of the project.
