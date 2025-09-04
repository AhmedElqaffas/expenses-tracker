# Expenses Tracker
A project for recording my spending and visualizing it using grafana.
The project consists of 3 components:
- Python script for adding spending records
- Postgres DB to save records
- Grafana container with a dashboard for visualization

## Python Script
The python script is used to insert spending in the database.
It takes the following parameters:
- amount
- item name
- categories that this item belong to
- (optional) spending date. If not specified, it will use the current date.

Example: 
```commandline
uv run python_script/expenses-tracker.py 300 fifa entertainment
```
You can use -h to get help
```commandline
uv run python_script/expenses-tracker.py -h
```
### Generating exe
To generate an executable script file (with dependencies bundled), run the following command
```commandline
 uv run pyinstaller --onefile --collect-all psycopg  --add-data ".env;." .\python_script\expenses-tracker.py
```
- --add-data is needed to bundle the env variables with the exe.
- --collect-all is needed to bundle binary `psycopg` files

## Postgres Database
A remotely hosted database (on [Supabase](https://supabase.com/)).
The schema for this database can be found in `./database_schema/schema.sql`.
There is also a `./database_schema/categories_population.sql` to populate the available spending categories.

To enable the python script to connect to the database, you need to set `DB_CONNECTION_STRING` env variable.
Example: `DB_CONNECTION_STRING=dbname=expenses_tracker user=postgres password=admin`.

## Grafana Dashboard

Contains some panels for visualizing my spending.
For deployment, I used public grafana docker image and added [provisioning](https://grafana.com/docs/grafana/latest/administration/provisioning/).
I provision the dashboard, the postgres datasource, and the login credentials, so that I don't lose anything when redeploying my docker container.
It is currently deployed on [Render](https://dashboard.render.com/).

You need to set the following env variables:
- For postgres datasource:
   - POSTGRES_USER
   - POSTGRES_PW
   - POSTGRES_DB
   - POSTGRES_HOST
- For Grafana login
   - GF_SECURITY_ADMIN_USER
   - GF_SECURITY_ADMIN_PASSWORD
