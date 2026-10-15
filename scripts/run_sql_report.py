import argparse
import csv
import os
from pathlib import Path

import psycopg
import yaml


PROJECT_ROOT = Path(__file__).resolve().parent.parent


def main():
    parser = argparse.ArgumentParser(
        description="Run one SQL query and export its result to CSV."
    )
    parser.add_argument(
        "sql_file",
        help="SQL file path relative to the project root.",
    )
    parser.add_argument(
        "report_file",
        help="Output CSV path relative to the project root.",
    )
    args = parser.parse_args()

    sql_path = PROJECT_ROOT / args.sql_file
    report_path = PROJECT_ROOT / args.report_file

    with (PROJECT_ROOT / "config.yaml").open(
        encoding="utf-8"
    ) as file:
        config = yaml.safe_load(file)

    db = config["database"]
    sql_text = sql_path.read_text(encoding="utf-8-sig")

    with psycopg.connect(
        host=db["host"],
        port=db["port"],
        dbname=db["name"],
        user=os.environ["PGUSER"],
        connect_timeout=5,
    ) as conn:
        # Reports should only read data.
        conn.read_only = True

        with conn.cursor() as cursor:
            # Extended protocol accepts one SQL statement.
            cursor.execute(sql_text, prepare=True)

            if cursor.description is None:
                raise ValueError(
                    "The SQL query did not return a result table."
                )

            columns = [
                column.name for column in cursor.description
            ]
            rows = cursor.fetchall()

    report_path.parent.mkdir(parents=True, exist_ok=True)

    with report_path.open(
        "w", encoding="utf-8", newline=""
    ) as file:
        writer = csv.writer(file)
        writer.writerow(columns)
        writer.writerows(rows)

    print(f"Query: {sql_path.name}")
    print(f"Result rows: {len(rows)}")
    print(f"Report saved to: {report_path}")

    # Display a small preview in the terminal.
    print("\t".join(columns))
    for row in rows[:20]:
        print("\t".join(
            "NULL" if value is None else str(value)
            for value in row
        ))


if __name__ == "__main__":
    main()