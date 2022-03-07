# Mod Archive

Site code for the new, updated Mod Archive. Not currently live in production environment.

## How to run the dev environment

To run on a local environment, you will need to install dependencies.

### Install dependencies

First, you will need Python and Django, naturally. You will also need to have a running PostgreSQL instance with a database called "mod_archive."

### Set configs

### Execute

## Setting up testing in local environment

The following instructions are relevant for use with Visual Studio Code. Please note that every directory with tests will need to have __init__.py in the directory.

First, do pip install pytest-django.

Second, in Visual Studio Code, click on "Testing" and select pytest as your testing framework.

The pytest.ini that is included in this repository should allow VS code to discover all the tests available. Note that you will need your database instance to be running to execute the tests.