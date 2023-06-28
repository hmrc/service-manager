# Service Manager

## This tool is deprecated. Use  [service-manager-2](https://github.com/hmrc/sm2) instead.

------

Developing with lots of microservices often draws complaints from the eventual complexity for the developer. i.e. 10 different services to start that are constantly evolving, owned by different teams and using different technologies... What if there was a way to manage this so you can just get on with your work...

## Introducing Service Manager

A set of utilities to run applications and micro services during the development and testing phase, and make development easier in a micro service environment.

#### [How do I install?](https://github.com/hmrc/service-manager/wiki/Install#install-service-manager)

### Common use cases / Getting started

- For a list of commands type `sm --help`
- For current run status type `sm -s`
- Start service using binaries: `sm --start SERVICE_NAME`
- Start a specific version using binaries: `sm --start SERVICE_NAME -r 1.2.3`
- Open service log file: `sm --logs SERVICE_NAME` (stderr.txt can be found in the same directory)

## Adding a new application

### Modify your services.json file

The application automatically looks for your config in `$WORKSPACE/service-manager-config`

You can change this directly in `$WORKSPACE/service-manager-config` to test your changes locally

Add a new application at the bottom of the `services.json`.
There are plenty of examples of how to do this by looking at existing entries

## SM Server

Service Manager also has a feature for allowing integration tests

Run `smserver` and it will run a service that can fire up services on demand

## API

| Path                         | Supported Methods | Description  |
| ---------------------------- | ------------------| ------------ |
|`/ping`                       |GET                |              |
|`/start`                      |POST               |              |
|`/stop`                       |POST               |              |
|`/version_variable`           |GET                |              |

## Development setup

This repo uses [tox](https://tox.readthedocs.io/en/latest/install.html) to simplify testing and packaging.

First, ensure you have tox and all other dependencies installed:

```
pipenv install
```

> You can check with `pipenv run tox --version`

## Running the tests

To run the tests is simply:

```bash
pipenv run tox
```

Alternatively, you can launch pytest manually (without tox) with:

```pipenv run python py.test -v -s test/```

Some of the tests pull down large repositories. To skip these online tests, you can use markers:
```pipenv run python py.test -v -m "not online" -s test/```

If you are using `tox` for local development, you can similarly edit the `py.test` command in `tox.ini` with suitable marker flags.

The unit tests and integration tests are in separate subfolders, so can also be selected independently

## Releasing a new version

> If in the HMRC org, there are build jobs setup to handle the release for you, see here: https://github.com/hmrc/service-manager/wiki/Releasing-servicemanager
> These notes are just for completeness.

Releasing is also setup via `tox`, and using [twine](https://pypi.org/project/twine/)

First set env vars for the release repository:
```
export TWINE_REPOSITORY_URL=<yourrepo>
export TWINE_USERNAME=<username>
export TWINE_PASSWORD=<password>
tox -e release
```

> N.B. for uploading to test.pypi.org and pypi.org, the username will always be `__token__` and the password should be
> an API token that you have generated in the account

## License

This code is open source software licensed under the [Apache 2.0 License]("http://www.apache.org/licenses/LICENSE-2.0.html").
