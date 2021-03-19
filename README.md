# SwaGrader
*Project Under Dr. Swaprava Nath, IIT Kanpur*

A modular and smart peer-grading tool with API back-end and angular front-end. Integrating Course metadata, discussion forums and peergrading based on the intelligent TRUPEQA algorithm.

## Requirements:

### PostgreSQL:

1. Install Postgres.
```
sudo apt-get update
sudo apt-get install python-pip python-dev libpq-dev postgresql postgresql-contrib

```

_For windows, download the installer from the official site._

2. Add `psql` to path, in env variables (this is for windows only, in ubuntu it'll be done automatically).

3. Enter the `psql` shell, by typing:

`psql -U postgres` 

Postgres is the default superuser made during the installation, enter the password for the same. 

For Ubuntu, add the user postgres as superuser, run:

`sudo su - postgres`

4. Create a database and and a user to access it, grant it all the permissions:

```
CREATE DATABASE yourproject;

CREATE USER youruser WITH PASSWORD 'yourpassword';

ALTER ROLE youruser SET client_encoding TO 'utf8';

ALTER ROLE youruser SET default_transaction_isolation TO 'read committed';    // Prevents reading from uncommitted entry.

ALTER ROLE youruser SET timezone TO 'UTC';

GRANT ALL PRIVILEGES ON DATABASE yourproject TO youruser;   // Getting privileges to youruser
```

Connect to the database by doing:

`\c yourproject`

5. quit the psql shell, by typing `\q`.

6. Install psycopg2 adapter for postgres (added in requirements.py file as well).

`pip install psycopg2`

7. Alter `settings.py` file. Enter configured username and password created in step 4. enter the name of database as well, this will look something like this :

```
. . .

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'yourproject',
        'USER': 'youruser',
        'PASSWORD': 'yourpassword',
        'HOST': 'localhost',         // This will be updated as per the deployment needs.
        'PORT': '',
    }
}

. . .
```

### Django:

1. `virtualenv <environment name>` Activate it.
2.  Navigate to `backend` directory. 
3.  Run `pip install requirements.txt` (`psycopg2` adapter is installed already in setting up Postgres, you may skip the warning)

**_Warning_**

During installation, some packages may throw error for the base version of python installed on the server, in that case, use:

`pip install --upgrade -r requirements.txt`

It will throw error on the main OS thread regarding install of `psycopg2`. In that case, *execute the postgres installation first*. And, then install `psycopg2` manually.

After this, rerun the command `pip install --upgrade -r requirements.txt`, and verify all the packages are installed by typing:

`pip freeze`

Once this is done, setup the internal `settings.py` file to modify the settings with the `username` and `password` you configured for the database.

## Running the project for development:

_Make sure Postgres service is up and database is setup and connected._

```
python manage.py makemigrations
python manage.py migrate
python manage.py test
python manage.py createsuperuser
python manage.py runserver <port>

```
bugs-
#bug- sent probe instead of assign
#copies not distributed to ta and instructor
#probe objects not initialised
# foriegn key not matching   probe_submission.probe_questions->grade probe in
=>probe = get_object_or_404(
        assign.assign_submissions.all(), probe_submission__probe_id=probe_id)  (major)
=> marks not saved in db