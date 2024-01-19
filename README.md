# Mod Archive

Site code for the new, updated Mod Archive. Not currently live in production environment.

## Visual Studio Code setup instructions

Create a virtual environment
Python: Create Environment
Venv
Install requirements.txt - pip install -r requirements.txt
Create a launch.json (make sure to include the settings bit)
Generate a secret key and put it in your launch.json

## How to run the dev environment

To run on a local environment, you will need to install dependencies.

### Install dependencies

You will need to have Python version 3.10 or higher, and pip to install required libraries.

### Set up virtual environment in VS Code

Note: These instructions will be different if you are using a different IDE.

1. Open the project folder in Visual Studio Code
2. From the Command Palette, select Python: Create Environment
3. Select Venv and select the Python binary you will be using
4. Install required libraries using pip install -r requirements.txt
5. Click "Run and Debug" and create a `launch.json` for Django

### Start database
`docker-compose up` will start the database to the foreground. Add `-d` to daemonize.

`docker-compose down` will stop the database. Add `-v` to destroy the volume data.

`invoke psql` will open an interactive psql shell in the database container.
See `inv psql --help` for more options.


### Set configs

Under args in `launch.json`, make sure to include the following:

    "args": [
        "runserver",
        "--settings=modarchive.settings.dev"
    ],

You should also make the following change to `manage.py` (but don't commit it):

    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'modarchive.settings.dev')

Django requires a secret key to run. Invoke `python manage.py shell` and do the following:

    from django.core.management.utils import get_random_secret_key
    get_random_secret_key()

Put the value of the secret key into `launch.json`:

    "env": {
        "MODARCHIVE_SECRET_KEY": "secret_key_goes_here"
    }

### Execute

## Setting up testing in local environment

The following instructions are relevant for use with Visual Studio Code. Please note that every directory with tests will need to have `__init__.py` in the directory.

First, do pip install pytest-django.

Second, in Visual Studio Code, click on "Testing" and select pytest as your testing framework.

You will need to create a pytest.ini with the following content:

    [pytest]
    DJANGO_SETTINGS_MODULE = modarchive.settings.unittest
    python_files = tests.py test_*.py *_tests.py

    env =
        MODARCHIVE_SECRET_KEY=(generate a new secret key here)
