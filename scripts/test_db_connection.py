import os

import psycopg
import yaml


def main():
    with open("config.yaml", encoding="utf-8") as file:
        config = yaml.safe_load(file)

    db = config["database"]

    with psycopg.connect(
        host=db["host"],
        port=db["port"],
        dbname=db["name"],
        user=os.environ["PGUSER"],
        connect_timeout=5,
    ) as conn:
        with conn.cursor() as cursor:
            cursor.execute("SELECT current_database(), current_user;")
            database, user = cursor.fetchone()

    print(f"Connected to database: {database}")
    print(f"Connected as user: {user}")


if __name__ == "__main__":
    main()