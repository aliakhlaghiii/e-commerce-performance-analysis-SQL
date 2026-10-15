import csv
import os
from pathlib import Path

import psycopg
import yaml


# Locate the project root regardless of the terminal directory.
PROJECT_ROOT = Path(__file__).resolve().parent.parent


def main():
    # Load project settings.
    config_path = PROJECT_ROOT / "config.yaml"

    with config_path.open(encoding="utf-8") as file:
        config = yaml.safe_load(file)

    db = config["database"]
    csv_path = (
        PROJECT_ROOT / config["paths"]["category_translation"]
    )

    # Validate the header and count source records.
    # utf-8-sig removes a BOM if one is present.
    with csv_path.open(
        "r", encoding="utf-8-sig", newline=""
    ) as file:
        reader = csv.reader(file)
        header = next(reader, None)

        expected_columns = [
            "product_category_name",
            "product_category_name_english",
        ]

        if header != expected_columns:
            raise ValueError(
                f"Unexpected CSV columns: {header}"
            )

        source_rows = sum(1 for _ in reader)

    if source_rows == 0:
        raise ValueError("The source CSV contains no data.")

    # Commit on success; roll back if an error occurs.
    with psycopg.connect(
        host=db["host"],
        port=db["port"],
        dbname=db["name"],
        user=os.environ["PGUSER"],
        connect_timeout=5,
    ) as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                "SELECT COUNT(*) FROM public.categories;"
            )
            rows_before = cursor.fetchone()[0]

            # Prevent accidentally importing the file twice.
            if rows_before != 0:
                raise ValueError(
                    "categories is not empty. Import stopped."
                )

            copy_sql = """
                COPY public.categories (
                    product_category_name,
                    product_category_name_english
                )
                FROM STDIN
                WITH (
                    FORMAT CSV,
                    HEADER TRUE,
                    ENCODING 'UTF8'
                )
            """

            # Remove any BOM and send UTF-8 bytes to PostgreSQL.
            with csv_path.open(
                "r", encoding="utf-8-sig", newline=""
            ) as file:
                with cursor.copy(copy_sql) as copy:
                    while chunk := file.read(65536):
                        copy.write(chunk.encode("utf-8"))

            cursor.execute(
                "SELECT COUNT(*) FROM public.categories;"
            )
            rows_after = cursor.fetchone()[0]
            inserted_rows = rows_after - rows_before

            if inserted_rows != source_rows:
                raise ValueError(
                    f"Row count mismatch: "
                    f"source={source_rows}, "
                    f"inserted={inserted_rows}"
                )

    # The database transaction has committed successfully.
    report_dir = PROJECT_ROOT / "reports"
    report_dir.mkdir(parents=True, exist_ok=True)

    report_path = (
        report_dir / "categories_load_report.csv"
    )

    with report_path.open(
        "w", encoding="utf-8", newline=""
    ) as file:
        writer = csv.DictWriter(
            file,
            fieldnames=[
                "table_name",
                "source_rows",
                "rows_before",
                "inserted_rows",
                "rows_after",
                "status",
            ],
        )

        writer.writeheader()
        writer.writerow({
            "table_name": "categories",
            "source_rows": source_rows,
            "rows_before": rows_before,
            "inserted_rows": inserted_rows,
            "rows_after": rows_after,
            "status": "PASS",
        })

    print(f"Loaded {inserted_rows} rows into categories.")
    print(f"Report saved to: {report_path}")


if __name__ == "__main__":
    main()