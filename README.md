# Mod Archive

Site code for the new, updated Mod Archive. Not currently live in production environment.

## Visual Studio Code setup instructions

The following instructions are how to set the application up using Visual Studio Code.

If you want to use a different IDE such as Pycharm, feel free, but you will be on your own for its specifics.

### Install dependencies

The application currently runs on Python 3.13. Please ensure that this is installed on your system. This setup also requires Docker to be installed, as it will use docker-compose for the database.

### Set up virtual environment in VS Code

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

Create a `settings.json` in the `.vscode` directory that contains the following:

    {
        "terminal.integrated.env.windows": {
            "DJANGO_SETTINGS_MODULE": "modarchive.settings.dev"
        }
    }

This will make settings available in the terminal (you will probably need to open a new terminal in VS code for this to take effect).

Django requires a secret key to run. Invoke `python manage.py shell` and do the following:

    from django.core.management.utils import get_random_secret_key
    get_random_secret_key()

Put the value of the secret key into `launch.json`:

    "env": {
        "MODARCHIVE_SECRET_KEY": "secret_key_goes_here"
    }

### Run database migrations

In the VS code terminal, run:

    python manage.py migrate

This will run migrations against the database, which creates the necessary schema.

### Create a superuser

From your terminal, execute:

    python manage.py createsuperuser

Follow the prompts to create your user. You can use this to log in to the application when it runs.

## Run tests

You don't need to run tests to run the application, but if you plan to do any amount of development, you will need tests.

In the repository root directory, create file pytest.ini with the following content:

    [pytest]
    DJANGO_SETTINGS_MODULE = modarchive.settings.unittest
    python_files = tests.py test_*.py *_tests.py

    env =
        MODARCHIVE_SECRET_KEY=(secret key, the one you generated earlier will work fine)

In Visual Studio Code, click on "Testing" and select pytest as your testing framework. Once tests are discovered, run them and verify that they work.

## Run the application

Your launch.json needs a configuration that looks something like this (you may already have this if you followed earlier steps):

    {
      "name": "Python Debugger: Django",
      "type": "debugpy",
      "request": "launch",
      "args": ["runserver", "--settings=modarchive.settings.dev"],
      "django": true,
      "autoStartBrowser": false,
      "program": "${workspaceFolder}\\manage.py",
      "env": {
        "DJANGO_SETTINGS_MODULE": "modarchive.settings.dev",
        "MODARCHIVE_SECRET_KEY": "your secret key value goes here"
      }
    }

You will now be able to click "Python Debugger: Django" to run the application. Point your browser to localhost:8000 to visit the site.
