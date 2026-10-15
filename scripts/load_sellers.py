import csv
import os
from pathlib import Path

import psycopg
import yaml


PROJECT_ROOT = Path(__file__).resolve().parent.parent

EXPECTED_COLUMNS = [
    "seller_id",
    "seller_zip_code_prefix",
    "seller_city",
    "seller_state",
]


def main():
    # Load database settings and source file path.
    with (PROJECT_ROOT / "config.yaml").open(
        encoding="utf-8"
    ) as file:
        config = yaml.safe_load(file)

    db = config["database"]
    csv_path = PROJECT_ROOT / config["paths"]["sellers"]

    # Validate the header and count CSV records.
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

    # Commit only if loading and validation both succeed.
    with psycopg.connect(
        host=db["host"],
        port=db["port"],
        dbname=db["name"],
        user=os.environ["PGUSER"],
        connect_timeout=5,
    ) as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                "SELECT COUNT(*) FROM public.sellers;"
            )
            rows_before = cursor.fetchone()[0]

            if rows_before != 0:
                raise ValueError(
                    "sellers is not empty. Import stopped."
                )

            copy_sql = """
                COPY public.sellers (
                    seller_id,
                    seller_zip_code_prefix,
                    seller_city,
                    seller_state
                )
                FROM STDIN
                WITH (
                    FORMAT CSV,
                    HEADER TRUE,
                    ENCODING 'UTF8'
                )
            """

            # Preserve IDs and leading zeros in ZIP prefixes.
            with csv_path.open(
                "r", encoding="utf-8-sig", newline=""
            ) as file:
                with cursor.copy(copy_sql) as copy:
                    while chunk := file.read(65536):
                        copy.write(chunk.encode("utf-8"))

            cursor.execute(
                "SELECT COUNT(*) FROM public.sellers;"
            )
            rows_after = cursor.fetchone()[0]
            inserted_rows = rows_after - rows_before

            if inserted_rows != source_rows:
                raise ValueError(
                    f"Row count mismatch: "
                    f"source={source_rows}, "
                    f"inserted={inserted_rows}"
                )

    # Write the report after the database commit succeeds.
    report_dir = PROJECT_ROOT / "reports"
    report_dir.mkdir(parents=True, exist_ok=True)
    report_path = report_dir / "sellers_load_report.csv"

    report = {
        "table_name": "sellers",
        "source_rows": source_rows,
        "rows_before": rows_before,
        "inserted_rows": inserted_rows,
        "rows_after": rows_after,
        "status": "PASS",
    }

    with report_path.open(
        "w", encoding="utf-8", newline=""
    ) as file:
        writer = csv.DictWriter(
            file,
            fieldnames=list(report),
        )
        writer.writeheader()
        writer.writerow(report)

    print(f"Loaded {inserted_rows} rows into sellers.")
    print(f"Report saved to: {report_path}")


if __name__ == "__main__":
    main()