import csv
import os
from pathlib import Path

import psycopg
import yaml


PROJECT_ROOT = Path(__file__).resolve().parent.parent

EXPECTED_COLUMNS = [
    "geolocation_zip_code_prefix",
    "geolocation_lat",
    "geolocation_lng",
    "geolocation_city",
    "geolocation_state",
]


def main():
    # Load database settings and source file path.
    with (PROJECT_ROOT / "config.yaml").open(
        encoding="utf-8"
    ) as file:
        config = yaml.safe_load(file)

    db = config["database"]
    csv_path = PROJECT_ROOT / config["paths"]["geolocation"]

    print("Checking the source CSV...", flush=True)

    # Validate the header and count records without loading
    # the entire dataset into memory.
    with csv_path.open(
        "r", encoding="utf-8-sig", newline=""
    ) as file:
        reader = csv.reader(file)
        header = next(reader, None)

        if header != EXPECTED_COLUMNS:
            raise ValueError(
                f"Unexpected CSV columns: {header}"
            )

        source_rows = 0

        for record_number, row in enumerate(reader, start=1):
            if len(row) != len(EXPECTED_COLUMNS):
                raise ValueError(
                    f"Invalid column count in data record "
                    f"{record_number}: {len(row)}"
                )

            source_rows += 1

    if source_rows == 0:
        raise ValueError("The source CSV contains no data.")

    print(f"Source records: {source_rows}", flush=True)

    # Commit only if loading and row count validation succeed.
    with psycopg.connect(
        host=db["host"],
        port=db["port"],
        dbname=db["name"],
        user=os.environ["PGUSER"],
        connect_timeout=5,
    ) as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                "SELECT COUNT(*) FROM public.geolocation;"
            )
            rows_before = cursor.fetchone()[0]

            if rows_before != 0:
                raise ValueError(
                    "geolocation is not empty. Import stopped."
                )

            # PostgreSQL generates geolocation_id automatically.
            copy_sql = """
                COPY public.geolocation (
                    geolocation_zip_code_prefix,
                    geolocation_lat,
                    geolocation_lng,
                    geolocation_city,
                    geolocation_state
                )
                FROM STDIN
                WITH (
                    FORMAT CSV,
                    HEADER TRUE,
                    ENCODING 'UTF8'
                )
            """

            print("Loading geolocation records...", flush=True)

            with csv_path.open(
                "r", encoding="utf-8-sig", newline=""
            ) as file:
                with cursor.copy(copy_sql) as copy:
                    while chunk := file.read(65536):
                        copy.write(chunk.encode("utf-8"))

            cursor.execute(
                "SELECT COUNT(*) FROM public.geolocation;"
            )
            rows_after = cursor.fetchone()[0]
            inserted_rows = rows_after - rows_before

            if inserted_rows != source_rows:
                raise ValueError(
                    f"Row count mismatch: "
                    f"source={source_rows}, "
                    f"inserted={inserted_rows}"
                )

            print("Summarizing loaded data...", flush=True)

            cursor.execute("""
                SELECT
                    COUNT(DISTINCT geolocation_zip_code_prefix),
                    COUNT(*) FILTER (
                        WHERE NOT (
                            geolocation_lat BETWEEN -90 AND 90
                            AND geolocation_lng BETWEEN -180 AND 180
                        )
                    )
                FROM public.geolocation;
            """)

            (
                distinct_zip_prefixes,
                invalid_coordinate_rows,
            ) = cursor.fetchone()

            # Exclude the generated ID when checking duplicates.
            cursor.execute("""
                SELECT COALESCE(SUM(group_size - 1), 0)::BIGINT
                FROM (
                    SELECT COUNT(*) AS group_size
                    FROM public.geolocation
                    GROUP BY
                        geolocation_zip_code_prefix,
                        geolocation_lat,
                        geolocation_lng,
                        geolocation_city,
                        geolocation_state
                    HAVING COUNT(*) > 1
                ) AS duplicate_groups;
            """)
            duplicate_excess_rows = cursor.fetchone()[0]

    # Write the report after the transaction commits.
    report = {
        "table_name": "geolocation",
        "source_rows": source_rows,
        "rows_before": rows_before,
        "inserted_rows": inserted_rows,
        "rows_after": rows_after,
        "distinct_zip_prefixes": distinct_zip_prefixes,
        "duplicate_excess_rows": duplicate_excess_rows,
        "invalid_coordinate_rows": invalid_coordinate_rows,
        "status": "PASS",
    }

    report_dir = PROJECT_ROOT / "reports"
    report_dir.mkdir(parents=True, exist_ok=True)
    report_path = report_dir / "geolocation_load_report.csv"

    with report_path.open(
        "w", encoding="utf-8", newline=""
    ) as file:
        writer = csv.DictWriter(
            file,
            fieldnames=list(report),
        )
        writer.writeheader()
        writer.writerow(report)

    print(f"Loaded {inserted_rows} rows into geolocation.")
    print(f"Distinct ZIP prefixes: {distinct_zip_prefixes}")
    print(f"Duplicate excess rows: {duplicate_excess_rows}")
    print(f"Invalid coordinate rows: {invalid_coordinate_rows}")
    print(f"Report saved to: {report_path}")


if __name__ == "__main__":
    main()